'use client';

const MODES = [
  { id: 'chat', label: 'Chat', icon: '💬' },
  { id: 'voice', label: 'Voice', icon: '🎤' },
  { id: 'research', label: 'Research', icon: '🔍' },
  { id: 'code', label: 'Code', icon: '⌨' },
];

export default function StatusBar({ mode, onModeChange, streaming, agentStatus }) {
  return (
    <div style={{
      padding: '10px 20px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      background: 'var(--bg-surface)', gap: 12,
    }}>
      <div style={{ display: 'flex', gap: 4 }}>
        {MODES.map(m => (
          <button key={m.id} onClick={() => onModeChange(m.id)}
            style={{
              padding: '5px 12px', borderRadius: 20, border: mode === m.id ? '1px solid var(--accent)' : '1px solid var(--border)',
              background: mode === m.id ? 'var(--accent-glow)' : 'transparent',
              color: mode === m.id ? 'var(--text-primary)' : 'var(--text-secondary)', cursor: 'pointer',
              fontSize: 12, fontWeight: mode === m.id ? 600 : 400, display: 'flex', alignItems: 'center', gap: 5, transition: 'all 0.15s',
            }}
          >{m.icon} {m.label}</button>
        ))}
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        {streaming && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: 'var(--accent)' }}>
            <div style={{ display: 'flex', gap: 3 }}>
              {[0,1,2].map(i => <div key={i} className="typing-dot" style={{ width: 5, height: 5, borderRadius: '50%', background: 'var(--accent)' }}></div>)}
            </div>
            Thinking
          </div>
        )}
        {agentStatus && !streaming && <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{agentStatus}</span>}
      </div>
    </div>
  );
}
