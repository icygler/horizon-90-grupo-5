# Horizon 90 — Requirements

## Objective

Create a public, lightweight airport decision rehearsal for Group 5 that demonstrates TiDB Cloud, TiDB Vector, Amazon Bedrock, Amazon S3 and EC2.

## Acceptance criteria

- The scenario is visibly labelled simulated and requires confirmation.
- Airport exposure uses aggregates only; no passenger or employee data is queried, prompted or returned.
- TiDB stores curated evidence with a generated `VECTOR(1024)` embedding and searches it semantically.
- The app rehearses exactly four fixed roles for one round, inspired by MiroFish without claiming a MiroFish integration.
- A decision pack is generated only after selection of one of three fixed strategies.
- TiDB, vector, Bedrock and S3 state is shown honestly as real, fallback or unavailable.
- S3 writes remain under `latam-hackathon-005/`.
