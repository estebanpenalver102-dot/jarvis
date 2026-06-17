# JARVIS Phase 4 — Voice + Browser Automation ✅

## Stack
FastAPI 0.4.0 | PostgreSQL 16 + pgvector | Redis | Playwright Chromium | OpenAI Whisper + TTS

## New in Phase 4

### Voice Pipeline
| Endpoint | Description |
|----------|-------------|
| `POST /voice/transcribe` | Audio bytes (base64) → text via Whisper |
| `POST /voice/speak` | Text → MP3 audio (base64) via OpenAI TTS |
| `POST /voice/turn` | Full round-trip: audio in → response + audio out |
| `WS /voice/ws` | Real-time streaming WebSocket voice session |
| `GET /voice/voices` | List available TTS voices |

### Browser Automation
| Endpoint | Description |
|----------|-------------|
| `POST /browser/browse` | Navigate to URL + extract content via LLM |
| `POST /browser/search` | Google search + browse top results + synthesize |
| `POST /browser/monitor` | Check if a condition exists on a URL |
| `DELETE /browser/session` | Reset Playwright browser session |

### Agents (now 6)
cto · sales · coding · research · operations · **browser**

## Phase 5 (Next)
- Cloud deployment (VPS/Railway + custom domain)
- LiveKit for sub-800ms real-time voice
- DealCenter CRM live API integration
- Scheduled monitoring tasks (uptime, leads, SEO)
- Spotify integration
- JARVIS web UI (Next.js chat + voice interface)
