# JARVIS — Personal AI Operating System

> Phase 1: Walking Skeleton — FastAPI + PostgreSQL + pgvector + Multi-Agent Foundation

## Overview
JARVIS is a personal AI Operating System designed to run businesses, websites, communications, research, automations, and personal workflows through a single unified interface.

## Stack
- **API:** Python 3.12 + FastAPI + SQLAlchemy (async)
- **Database:** PostgreSQL 16 + pgvector (5-tier memory system)
- **Cache/Queue:** Redis 7
- **Containerization:** Docker Compose → Kubernetes path
- **Agents:** Role-Based Multi-Agent System (R-MAS)

## Quick Start
```bash
cp .env.example .env
# Edit .env with your API keys
docker compose up --build
curl http://localhost:8000/health
curl http://localhost:8000/docs
```

## Endpoints
| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | System status |
| GET | `/health` | Health check (API + DB) |
| GET | `/health/pgvector` | pgvector extension check |
| POST | `/chat` | Chat with JARVIS |
| GET | `/chat/{id}/history` | Chat history |
| POST | `/memory` | Save memory |
| GET | `/memory` | List memories |
| GET | `/memory/stats` | Memory stats by tier |
| GET | `/tools` | List agent tools |
| POST | `/tools/call` | Execute a tool |
| GET | `/docs` | Swagger UI |

## Memory Tiers
| Tier | Category | What it stores |
|------|----------|----------------|
| 1 | `episodic` | Interaction logs |
| 2 | `semantic` | Extracted facts |
| 3 | `project` | Project context |
| 4 | `business` | CRM, dealership data |
| 5 | `preference` | User settings |

## Roadmap
- **Phase 1 ✅** Foundation — Docker + FastAPI + PostgreSQL + pgvector
- **Phase 2** Memory — Mem0, ETS pipeline, embedding auto-generation
- **Phase 3** Agent System — LLM routing, 5+ core tools
- **Phase 4** Voice & Browser — LiveKit + Playwright
- **Phase 5** Business — DealCenter CRM, Sales Agent
- **Phase 6** Autonomy — Self-healing, local fine-tuning
