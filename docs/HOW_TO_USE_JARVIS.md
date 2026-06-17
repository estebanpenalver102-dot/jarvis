# JARVIS — Complete Usage Guide

## Quick Start (2 commands)

```bash
# 1. Clone & configure
git clone https://github.com/estebanpenalver102-dot/jarvis.git
cd jarvis && cp .env.example .env
# Your OpenAI key is already baked into .env from Phase 3

# 2. Start everything
docker compose up --build

# 3. Start the UI (new terminal)
cd ui && npm install && npm run dev
```

**Access:**
- 🌐 **JARVIS UI**: http://localhost:3000
- 📖 **API Swagger**: http://localhost:8000/docs

---

## The Interface

### Central Orb
| Action | What happens |
|--------|-------------|
| **Hover** | 6 colored agent nodes orbit around the orb |
| **Click orb** | Chat panel slides in from the right |
| **Drag agent → agent** | Reassign tasks between agents |
| **Click agent node** | See that agent's specialty |

### Agent Colors
| Agent | Color | Does |
|-------|-------|------|
| research | 🔵 Blue | Web search, analysis, market intel |
| sales | 🟠 Orange | CRM leads, DealCenter, follow-ups |
| coding | 🟣 Purple | Code gen, debugging |
| cto | 🟢 Green | Architecture, infra decisions |
| operations | 🟡 Amber | Scheduling, reminders, tasks |
| browser | 🩷 Pink | Web automation, page monitoring |

---

## Goal Mode (Most Powerful Feature)

Type any goal in the bottom bar and press Enter. JARVIS will:
1. Decompose it into subtasks automatically
2. Hire the right agents for each subtask
3. Run all agents and combine their answers
4. Save the results to long-term memory forever

**Example goals to try:**
```
Research the top 5 car dealership CRMs and compare pricing
Monitor openroad-autos.com daily and alert if it goes down
Find this week's most important AI industry news
Draft a follow-up email sequence for new car leads
Analyze my dealership's sales pipeline bottlenecks
Create a weekly SEO report template for my website
```

The agent nodes on the left **light up and pulse** when hired.

---

## Chat Mode

1. Click the JARVIS orb
2. Chat panel opens on the right
3. JARVIS has full memory — it remembers every conversation
4. Responses show which agent answered [agent_name]

---

## Voice Mode

Inside the chat panel:
1. Click the **🎤 mic button**
2. Speak your message
3. Click mic again to stop
4. JARVIS responds in text **and** plays back in Nova voice (OpenAI TTS)

---

## Screen Takeover

Click **"GIVE JARVIS CONTROL"** in the top right corner.
- Your browser will ask for screen share permission — click "Share"
- Every 5 seconds, JARVIS analyzes your screen and shows observations
- JARVIS can see what you're working on and give real-time guidance
- Click "STOP CONTROL" to end the session

---

## API Direct Access

For power users — all features are accessible via API:

```bash
# Chat
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is my DealCenter lead count?"}'

# Submit a goal
curl -X POST http://localhost:8000/goals \
  -d '{"goal": "Research Tesla competitors"}'

# Search memory
curl http://localhost:8000/memory/search?q=car+dealership+leads

# Web search
curl -X POST http://localhost:8000/browser/search \
  -d '{"query": "best EV deals 2026", "goal": "find best prices"}'

# Analyze a URL
curl -X POST http://localhost:8000/browser/browse \
  -d '{"url": "https://openroad-autos.com", "goal": "find SEO issues"}'
```

---

## Cloud Deployment (Go Live)

### Option 1: Railway (Easiest — 5 minutes)
1. Go to [railway.app](https://railway.app)
2. "New Project" → "Deploy from GitHub repo" → select `estebanpenalver102-dot/jarvis`
3. Add environment variables from your `.env`
4. Railway auto-deploys on every git push

### Option 2: VPS (DigitalOcean/Linode — Full Control)
```bash
# On your VPS
git clone https://github.com/estebanpenalver102-dot/jarvis.git
cd jarvis && cp .env.example .env && nano .env  # fill in keys
docker compose -f deploy/docker-compose.prod.yml up -d

# Set up nginx + SSL
apt install nginx certbot python3-certbot-nginx
certbot --nginx -d your-domain.com
cp deploy/nginx.conf /etc/nginx/sites-available/jarvis
# Edit: replace your-domain.com with your actual domain
nginx -t && systemctl reload nginx
```

### Option 3: Vercel (UI) + Railway (API)
- Deploy `ui/` to Vercel (free)
- Deploy API to Railway
- Set `NEXT_PUBLIC_API_URL` in Vercel to Railway API URL

---

## Memory System

JARVIS uses a 5-tier persistent memory (PostgreSQL + pgvector):

| Tier | Stores | Example |
|------|--------|---------|
| Episodic | What happened | "User asked about Tesla pricing today" |
| Semantic | Extracted facts | "User owns OpenRoad Auto Group" |
| Project | Project data | "JARVIS Phase 3 complete" |
| Business | Business knowledge | "OpenRoad focuses on used vehicles" |
| Preference | Your preferences | "User prefers concise summaries" |

Memory is **automatically searched** on every chat message — JARVIS always has context.

Search manually: `GET /memory/search?q=your+query`

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| "Connection error" in chat | Run `docker compose up` first |
| Voice not working | Add `OPENAI_API_KEY` to `.env` |
| Screen capture blank | Use Chrome/Edge (not Safari) |
| Agents not loading | Check `http://localhost:8000/goals/agents` |
| Slow responses | Normal for first request — Docker is warming up |
