# 3. Build report: retail-semantic-search

**Status: completed**

Built an API-only Flask sample with a 20-product catalog, ada-002 embeddings, a native DocumentDB IVF index, idempotent seeding, and POST /search returning up to 10 scored products.

## How to run

Create and activate a fresh Python virtual environment, then run pip install -r requirements.txt. Configure DOCUMENTDB_URI and OPENAI_API_KEY locally using .env.example. With permission to write to a dedicated sample database, run python seed.py, then flask --app app run. POST JSON {"query":"gear for a rainy hiking trip"} to http://127.0.0.1:5000/search. Full setup, testing, and cleanup instructions are in README.md.

## Verified by running

- Pinned dependencies installed into an isolated workspace package directory.
- Offline unittest suite: 14 tests passed on Python 3.14.10.
- compileall passed for application, seed script, and tests.
- Isolated application and seed imports passed; pinned package versions confirmed.
- Real PyMongo constructor accepted corrected TLS, SCRAM, retry, and timeout options without connecting.
- Read-only MCP database discovery succeeded; only an unrelated sales_forecast_db was present.

## Not verified

- Live ada-002 embeddings: no application OpenAI credentials or model access supplied.
- Managed catalog ingestion, IVF creation, index readiness, numeric-array acceptance, and search relevance: no chosen application cluster or URI supplied; this run prohibited writes.
- Python 3.11–3.13 compatibility and illustrative eastus2 development-cluster availability were not tested.

## Open issues

None.

## Files

- `app.py`
- `catalog.py`
- `seed.py`
- `data/products.json`
- `requirements.txt`
- `.env.example`
- `.gitignore`
- `README.md`
- `tests/test_sample.py`
- `tests/test_driver_options.py`

