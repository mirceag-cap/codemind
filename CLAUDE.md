# Project: CodeMind

## Commands

```bash
# Frontend
cd frontend && npm run dev          # Dev server
cd frontend && npm test             # Tests
cd frontend && npm run typecheck    # Type checking
cd frontend && npm run lint         # Linting

# Backend
cd backend && uvicorn app.main:app --reload   # Dev server
cd backend && python -m pytest -v             # Tests
cd backend && pyright                         # Type checking
cd backend && ruff check .                    # Linting
```
