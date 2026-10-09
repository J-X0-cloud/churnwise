# Churnwise engine

The Python service behind Churnwise. It owns the revenue model, every metric the dashboards show, the
forecasts, the failed-payment recovery logic and the billing-event store. The Next.js app in the repository
root renders what this service returns.

```bash
uv sync
uv run churnwise bootstrap      # apply migrations and create the sample workspace
uv run churnwise serve --reload # http://localhost:8000, OpenAPI docs at /docs
uv run pytest
```

See the root README for the full API list and environment variables.
