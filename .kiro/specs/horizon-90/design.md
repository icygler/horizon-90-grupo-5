# Horizon 90 — Design constraints

The application is one FastAPI process plus static browser assets. It uses TiDB for historical aggregate exposure and semantic evidence, Bedrock Haiku for parser/rehearsal and Sonnet only for the decision pack, and S3 for replay archives. A dependency failure must yield a visible fallback or unavailable state; it must never be represented as a live result.

The seeded GRU exercise begins at `2015-06-04T15:00:00`, lasts 90 minutes, and assumes a 30% capacity reduction. It is based on `airportdb` historical data and is not a real operational forecast.
