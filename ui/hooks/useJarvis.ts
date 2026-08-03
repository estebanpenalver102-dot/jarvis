const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
// FETCH_TIMEOUT_MS: previously these calls had NO timeout at all, so a
// backend still cold-starting (or genuinely stuck) would hang the caller
// forever with no error. 60s survives a free-tier Render cold start.
const FETCH_TIMEOUT_MS = 60000
const j = {
  post: (path: string, body: any) => fetch(`${API}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    signal: AbortSignal.timeout(FETCH_TIMEOUT_MS),
  }).then(r => r.json()),
  get: (path: string) => fetch(`${API}${path}`, {
    signal: AbortSignal.timeout(FETCH_TIMEOUT_MS),
  }).then(r => r.json()),
}
export const jarvis = {
  chat: (message: string, session_id: string) => j.post('/chat', {message, session_id}),
  goal: (goal: string) => j.post('/goals', {goal}),
  searchMemory: (q: string) => j.get(`/memory/search?q=${encodeURIComponent(q)}`),
  browseWeb: (url: string, goal: string) => j.post('/browser/browse', {url, goal}),
  webSearch: (query: string, goal: string) => j.post('/browser/search', {query, goal}),
}
export default jarvis
