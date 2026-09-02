"""Read-only airport exposure queries and application-owned TiDB evidence."""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path
from typing import Any

import pymysql

from horizon90.config import Settings
from horizon90.models import Evidence, ExposureSummary, ScenarioContract
from horizon90.seed import CURATED_EVIDENCE


EXPOSURE_SQL = """
SELECT
  a.iata AS airport_iata,
  COUNT(DISTINCT f.flight_id) AS affected_flights,
  COUNT(DISTINCT b.booking_id) AS affected_bookings,
  COALESCE(SUM(ap.capacity), 0) AS affected_capacity
FROM flight f
JOIN airport a ON a.airport_id IN (f.`from`, f.`to`)
LEFT JOIN booking b ON b.flight_id = f.flight_id
LEFT JOIN airplane ap ON ap.airplane_id = f.airplane_id
WHERE a.iata = %s
  AND f.departure < %s
  AND f.arrival >= %s
GROUP BY a.iata
"""

VECTOR_SQL = """
SELECT evidence_id, source_label, source_type, content,
       VEC_EMBED_COSINE_DISTANCE(
         embedding,
         EMBED_TEXT("tidbcloud_free/amazon/titan-embed-text-v2", %s)
       ) AS distance
FROM evidence_chunks
ORDER BY distance
LIMIT %s
"""

SCHEMA_PATH = Path(__file__).resolve().parents[2] / "sql" / "schema.sql"


class TiDBRepository:
    """Accesses only aggregate airport data and the app-owned evidence table."""

    def __init__(self, settings: Settings):
        self.settings = settings

    def connect(self) -> Any:
        return pymysql.connect(
            host=self.settings.tidb_host,
            port=self.settings.tidb_port,
            user=self.settings.tidb_user,
            password=self.settings.tidb_password,
            database=self.settings.tidb_database,
            cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=10,
            read_timeout=15,
            write_timeout=15,
            ssl={"check_hostname": True},
        )

    def ping(self) -> None:
        connection = self.connect()
        try:
            connection.ping(reconnect=False)
        finally:
            connection.close()

    def initialize(self) -> None:
        connection = self.connect()
        try:
            with connection.cursor() as cursor:
                for statement in self._schema_statements():
                    cursor.execute(statement)
                cursor.execute("SELECT COUNT(*) AS total FROM evidence_chunks")
                if cursor.fetchone()["total"] == 0:
                    cursor.executemany(
                        """
                        INSERT INTO evidence_chunks (source_label, source_type, content)
                        VALUES (%s, %s, %s)
                        """,
                        [(item.source_label, item.source_type, item.text) for item in CURATED_EVIDENCE],
                    )
            connection.commit()
        finally:
            connection.close()

    def fetch_exposure(self, contract: ScenarioContract) -> ExposureSummary:
        window_end = contract.start_at + timedelta(minutes=contract.duration_minutes)
        connection = self.connect()
        try:
            with connection.cursor() as cursor:
                cursor.execute(EXPOSURE_SQL, (contract.airport_iata, window_end, contract.start_at))
                row = cursor.fetchone()
        finally:
            connection.close()
        if row is None:
            return ExposureSummary(
                airport_iata=contract.airport_iata,
                affected_flights=0,
                affected_bookings=0,
                affected_capacity=0,
                source="tidb",
            )
        return ExposureSummary(
            airport_iata=row["airport_iata"],
            affected_flights=int(row["affected_flights"]),
            affected_bookings=int(row["affected_bookings"]),
            affected_capacity=int(row["affected_capacity"]),
            source="tidb",
        )

    def find_evidence(self, query: str, limit: int = 3) -> list[Evidence]:
        connection = self.connect()
        try:
            with connection.cursor() as cursor:
                cursor.execute(VECTOR_SQL, (query, limit))
                rows = cursor.fetchall()
        finally:
            connection.close()
        return [Evidence(**row) for row in rows]

    @staticmethod
    def _schema_statements() -> list[str]:
        return [statement.strip() for statement in SCHEMA_PATH.read_text(encoding="utf-8").split(";") if statement.strip()]
