# JARVIS — Fly.io Deploy Guide (Free Tier)

## Prerequisites (one-time, ~2 min)
```bash
# 1. Install Fly CLI
curl -L https://fly.io/install.sh | sh
export PATH="$HOME/.fly/bin:$PATH"

# 2. Create free account or log in
flyctl auth signup    # new account (free, no card needed initially)
# or:
flyctl auth login
```

## Deploy JARVIS (run once, in order)
```bash
# 3. Clone the repo
git clone https://github.com/estebanpenalver102-dot/jarvis.git
cd jarvis

# 4. Create the Fly app (fly.toml already configured)
flyctl apps create jarvis-esteban

# 5. Add managed PostgreSQL w/ pgvector (free 1GB)
flyctl postgres create \
  --name jarvis-db \
  --region dfw \
  --initial-cluster-size 1 \
  --vm-size shared-cpu-1x \
  --volume-size 1
flyctl postgres attach jarvis-db --app jarvis-esteban
# ↑ Auto-sets DATABASE_URL secret for you

# 6. Add Redis via Upstash extension (free tier)
flyctl ext upstash-redis create --name jarvis-redis --region dfw
# ↑ Auto-sets UPSTASH_REDIS_REST_URL + UPSTASH_REDIS_REST_TOKEN

# 7. Set your secrets (replace OPENAI_API_KEY with your real key)
flyctl secrets set \
  OPENAI_API_KEY="sk-proj-YOUR_REAL_KEY_HERE" \
  SECRET_KEY="$(openssl rand -hex 32)" \
  --app jarvis-esteban

# 8. Deploy! (~3-4 minutes)
flyctl deploy --app jarvis-esteban
```

## Your JARVIS URLs (after deploy)
| Surface | URL |
|---------|-----|
| API root | https://jarvis-esteban.fly.dev |
| Interactive docs | https://jarvis-esteban.fly.dev/docs |
| Health check | https://jarvis-esteban.fly.dev/health |
| Chat | https://jarvis-esteban.fly.dev/chat |
| Voice | wss://jarvis-esteban.fly.dev/voice/ws |

## Drop files into JARVIS (continuous learning)
```bash
# Drop a GitHub file — JARVIS reads, summarizes, embeds it
curl -X POST https://jarvis-esteban.fly.dev/ingest/github-file \
  -H "Content-Type: application/json" \
  -d '{"url": "https://raw.githubusercontent.com/estebanpenalver102-dot/jarvis/main/README.md"}'

# Ingest a whole repo folder at once (max 20 files)
curl -X POST https://jarvis-esteban.fly.dev/ingest/github-repo \
  -H "Content-Type: application/json" \
  -d '{"repo": "estebanpenalver102-dot/jarvis", "folder": "api/agents"}'

# Paste raw text directly into knowledge base
curl -X POST https://jarvis-esteban.fly.dev/ingest/text \
  -H "Content-Type: application/json" \
  -d '{"text": "OpenRoad Autos inventory notes: we stock 40 vehicles..."}'

# See everything JARVIS has learned
curl https://jarvis-esteban.fly.dev/ingest/knowledge
```

## Deploy UI to Vercel (free)
```bash
cd ui
NEXT_PUBLIC_API_URL=https://jarvis-esteban.fly.dev npx vercel --prod
# Follow prompts → UI live at https://jarvis-esteban.vercel.app
```

## Useful Fly commands
```bash
flyctl logs --app jarvis-esteban        # live logs
flyctl status --app jarvis-esteban      # deployment status
flyctl ssh console --app jarvis-esteban # SSH into container
flyctl deploy --app jarvis-esteban      # redeploy after any git push
```

---
> Railway setup is in `docs/HOW_TO_DEPLOY_RAILWAY.md` — upgrade Railway trial anytime and you're live in minutes.
