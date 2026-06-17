# Deploy JARVIS to Railway — Step by Step

## 1. One-click deploy (fastest)
Open this URL — it pre-fills your GitHub repo:
**https://railway.app/new/github**

1. Click **"Deploy from GitHub repo"**
2. Select **`estebanpenalver102-dot/jarvis`**
3. Railway detects Docker Compose automatically

---

## 2. Add environment variables
In Railway dashboard → your service → **Variables** tab, add:

```
OPENAI_API_KEY=sk-proj-...your-key...
OPENROUTER_API_KEY=          # optional free fallbacks
GROQ_API_KEY=                # optional
SECRET_KEY=change-me-random-64-chars
```
Railway auto-provisions Postgres + Redis if you add them as Railway plugins.

---

## 3. Add Postgres + Redis plugins
Railway dashboard → **New** → **Database** → PostgreSQL (with pgvector)
Railway dashboard → **New** → **Database** → Redis

Railway auto-sets `DATABASE_URL` and `REDIS_URL` env vars — no manual config needed.

---

## 4. Custom domain
Railway dashboard → your service → **Settings** → **Domains** → **Add custom domain**
Add `api.yourdomain.com` (or `jarvis.yourdomain.com`), point DNS CNAME to Railway.

---

## 5. Deploy UI (Vercel — free)
```bash
cd ui
npx vercel --prod
# Set NEXT_PUBLIC_API_URL=https://your-railway-api-url.railway.app
```

---

## Done
JARVIS will be live at:
- API: `https://your-project.railway.app`
- UI: `https://your-project.vercel.app`
- Docs: `https://your-project.railway.app/docs`
