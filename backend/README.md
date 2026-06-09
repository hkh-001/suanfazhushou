# AlgoMentor Backend

Phase 1 FastAPI skeleton for AlgoMentor AI.

Run locally:

```bash
uv sync
uv run alembic upgrade head
uv run python scripts/seed_topics.py
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Run tests:

```bash
uv run pytest
```
