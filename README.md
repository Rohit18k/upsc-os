# UPSC OS — One Solution

A production-grade AI Operating System for UPSC preparation.

## Architecture

```
upsc-os/
├── frontend/     # Next.js + TypeScript + TailwindCSS
├── backend/      # FastAPI + SQLAlchemy + Celery
├── docker/       # Docker Compose configurations
├── infrastructure/ # Nginx, monitoring, etc.
├── .github/      # CI/CD workflows
└── docs/         # Documentation
```

## Quick Start

```bash
# Clone and start
git clone <repo>
cd upsc-os
docker compose up

# Or run locally
cd backend && uvicorn app.main:app --reload
cd frontend && npm run dev
```

## Tech Stack

- **Frontend:** Next.js, TypeScript, TailwindCSS, shadcn/ui
- **Backend:** Python, FastAPI, SQLAlchemy, Celery
- **Database:** Supabase PostgreSQL
- **Infrastructure:** Docker, Nginx, MinIO, Redis

## Security

- OWASP Top 10 & API Security Top 10
- Zero Trust Architecture
- JWT + Refresh Token authentication
- RBAC with Row Level Security
- Rate limiting, audit logging, CSP headers
- Structured input validation with Zod + Pydantic

## License

MIT
