# Fin RAG API

FastAPI adapter for the core `fin_rag` package.

## Local development

Run the API from the repository root:

```bash
uvicorn apps.api.app:app --reload
```

Run the React demo (proxies `/api` to port 8000):

```bash
cd apps/web
npm run dev
```

Set `GEMINI_API_KEY` in the project root `.env` before asking questions.
