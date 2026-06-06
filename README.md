# ClaimLens

ClaimLens is an AI agent project for patent claim analysis and infringement risk review.

The service is designed as a portfolio project that connects patent-domain experience with an agentic workflow:

1. Analyze a product or technology description.
2. Search relevant patent candidates from stored KIPRIS data.
3. Parse independent claims into claim elements.
4. Match product features against claim elements.
5. Generate a claim chart and risk review report.

This project does not provide legal infringement decisions. It provides a technical risk review draft with evidence, uncertainty, and traceable analysis steps.

## Monorepo

```text
apps/
  web/     Next.js frontend for agent workflow UI
  api/     FastAPI + LangGraph backend
packages/
  shared/  Shared TypeScript contracts for frontend events
docs/
  project-plan.md
```

## Local Development

Frontend:

```bash
npm run dev:web
```

Backend:

```bash
cd apps/api
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
```
