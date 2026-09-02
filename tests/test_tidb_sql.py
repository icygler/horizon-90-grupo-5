from horizon90.tidb import EXPOSURE_SQL


def test_exposure_query_never_reads_passenger_pii():
    forbidden = ("passenger", "passengerdetails", "employee", "passportno", "emailaddress")
    assert all(token not in EXPOSURE_SQL.lower() for token in forbidden)
    assert "COUNT(DISTINCT b.booking_id)" in EXPOSURE_SQL
