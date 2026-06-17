'use client';
import { useState } from 'react';

function CodeBlock({ code, lang }) {
  const [copied, setCopied] = useState(false);
  return (
    <div style={{ margin: '12px 0', borderRadius: 10, overflow: 'hidden', border: '1px solid rgba(255,255,255,0.08)' }}>
      <div style={{ background: 'rgba(0,0,0,0.4)', padding: '6px 14px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontSize: 11, color: 'var(--text-muted)', fontFamily: 'monospace' }}>{lang || 'code'}</span>
        <button onClick={() => { navigator.clipboard.writeText(code); setCopied(true); setTimeout(() => setCopied(false), 1500); }}
          style={{ fontSize: 11, color: copied ? 'var(--success)' : 'var(--text-secondary)', background: 'none', border: 'none', cursor: 'pointer', padding: '2px 8px' }}>
          {copied ? '✓ Copied' : 'Copy'}
        </button>
      </div>
      <pre style={{ margin: 0, padding: '14px', background: 'rgba(0,0,0,0.3)', overflowX: 'auto', fontSize: 13, lineHeight: 1.6, color: '#e2e2f0', fontFamily: ''Fira Code', monospace' }}>
        <code>{code}</code>
      </pre>
    </div>
  );
}

function renderContent(text) {
  const parts = text.split(/(```[\s\S]*?```)/g);
  return parts.map((part, i) => {
    if (part.startsWith('```')) {
      const lines = part.slice(3, -3).split('
');
      const lang = lines[0].trim();
      const code = lines.slice(1).join('
').trimEnd();
      return <CodeBlock key={i} code={code} lang={lang} />;
    }
    return <span key={i} style={{ whiteSpace: 'pre-wrap', lineHeight: 1.7 }}>{part}</span>;
  });
}

export default function MessageBubble({ msg }) {
  const isUser = msg.role === 'user';
  return (
    <div className="fade-in" style={{ display: 'flex', justifyContent: isUser ? 'flex-end' : 'flex-start', marginBottom: 16, gap: 10, alignItems: 'flex-start' }}>
      {!isUser && (
        <div style={{ width: 32, height: 32, borderRadius: 10, background: 'linear-gradient(135deg, #7c6aff, #00d4ff)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 14, fontWeight: 700, flexShrink: 0, marginTop: 2 }}>J</div>
      )}
      <div style={{ maxWidth: '75%', padding: '12px 16px', fontSize: 14, lineHeight: 1.65 }} className={isUser ? 'message-user' : 'message-ai'}>
        {!isUser && msg.agent && (
          <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--accent)', marginBottom: 6, textTransform: 'uppercase', letterSpacing: 0.5 }}>{msg.agent}</div>
        )}
        {renderContent(msg.content)}
        {msg.timestamp && (
          <div style={{ fontSize: 10, color: isUser ? 'rgba(255,255,255,0.5)' : 'var(--text-muted)', marginTop: 6, textAlign: 'right' }}>
            {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </div>
        )}
      </div>
      {isUser && (
        <div style={{ width: 32, height: 32, borderRadius: 10, background: 'var(--bg-elevated)', border: '1px solid var(--border)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 13, flexShrink: 0, marginTop: 2 }}>🧑</div>
      )}
    </div>
  );
}
