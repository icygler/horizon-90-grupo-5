CREATE TABLE IF NOT EXISTS evidence_chunks (
  evidence_id BIGINT AUTO_RANDOM PRIMARY KEY,
  source_label VARCHAR(120) NOT NULL,
  source_type VARCHAR(40) NOT NULL,
  content TEXT NOT NULL,
  s3_key VARCHAR(512) NULL,
  embedding VECTOR(1024) GENERATED ALWAYS AS (
    EMBED_TEXT("tidbcloud_free/amazon/titan-embed-text-v2", content)
  ) STORED,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  VECTOR INDEX evidence_embedding_idx ((VEC_COSINE_DISTANCE(embedding)))
);

CREATE TABLE IF NOT EXISTS scenarios (
  scenario_id BIGINT AUTO_RANDOM PRIMARY KEY,
  airport_iata CHAR(3) NOT NULL,
  start_at DATETIME NOT NULL,
  duration_minutes INT NOT NULL,
  capacity_reduction_pct INT NOT NULL,
  assumptions JSON NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
