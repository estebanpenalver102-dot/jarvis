'use client';
import { useState } from 'react';
import Link from 'next/link';

const AGENTS = [
  { id: 'jarvis', name: 'JARVIS', icon: '⬡', color: '#7c6aff', desc: 'General OS' },
  { id: 'research', name: 'Research', icon: '◈', color: '#00d4ff', desc: 'Web + Data' },
  { id: 'coding', name: 'Coding', icon: '◎', color: '#22d3a0', desc: 'Dev Tasks' },
  { id: 'browser', name: 'Browser', icon: '◇', color: '#f59e0b', desc: 'Automation' },
  { id: 'memory', name: 'Memory', icon: '◆', color: '#ec4899', desc: 'Knowledge' },
];

export default function Sidebar({ activeAgent, onAgentSelect, conversations, onNewChat }) {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div
      style={{
        width: collapsed ? 64 : 260,
        minWidth: collapsed ? 64 : 260,
        background: 'var(--bg-surface)',
        borderRight: '1px solid var(--border)',
        display: 'flex',
        flexDirection: 'column',
        transition: 'width 0.2s ease',
        overflow: 'hidden',
      }}
    >
      {/* Logo row */}
      <div style={{ padding: '16px 12px', display: 'flex', alignItems: 'center', gap: 10, borderBottom: '1px solid var(--border)' }}>
        <button
          onClick={() => setCollapsed(!collapsed)}
          style={{ width: 36, height: 36, borderRadius: 10, border: '1px solid var(--border)', background: 'var(--bg-elevated)', color: 'var(--text-secondary)', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, fontSize: 16 }}
        >
          {collapsed ? '▶' : '◀'}
        </button>
        {!collapsed && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <div style={{ width: 28, height: 28, borderRadius: 8, background: 'linear-gradient(135deg, #7c6aff, #00d4ff)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 14, fontWeight: 700, color: 'white' }}>J</div>
            <span style={{ fontWeight: 700, fontSize: 15, letterSpacing: 0.5 }}>JARVIS</span>
            <span style={{ fontSize: 10, color: 'var(--accent)', background: 'var(--accent-glow)', padding: '2px 6px', borderRadius: 4, fontWeight: 600 }}>v1.0</span>
          </div>
        )}
      </div>

      {/* New chat */}
      <div style={{ padding: '10px 8px' }}>
        <button
          onClick={onNewChat}
          style={{ width: '100%', padding: collapsed ? '10px 0' : '10px 14px', borderRadius: 10, border: '1px dashed var(--border-hover)', background: 'transparent', color: 'var(--text-secondary)', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: collapsed ? 'center' : 'flex-start', gap: 8, fontSize: 13, transition: 'all 0.15s' }}
          onMouseEnter={e => { e.currentTarget.style.background = 'var(--bg-elevated)'; e.currentTarget.style.color = 'var(--text-primary)'; }}
          onMouseLeave={e => { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.color = 'var(--text-secondary)'; }}
        >
          <span style={{ fontSize: 18, lineHeight: 1 }}>+</span>
          {!collapsed && <span>New conversation</span>}
        </button>
      </div>

      {/* Agents */}
      {!collapsed && <div style={{ padding: '4px 12px 6px', fontSize: 10, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 1 }}>Agents</div>}
      <div style={{ padding: '0 8px', display: 'flex', flexDirection: 'column', gap: 2 }}>
        {AGENTS.map(a => (
          <button
            key={a.id}
            onClick={() => onAgentSelect(a.id)}
            style={{
              width: '100%', padding: collapsed ? '10px 0' : '9px 12px', borderRadius: 10, border: 'none',
              background: activeAgent === a.id ? 'var(--accent-glow)' : 'transparent',
              color: activeAgent === a.id ? 'var(--text-primary)' : 'var(--text-secondary)',
              cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: collapsed ? 'center' : 'flex-start',
              gap: 10, fontSize: 13, transition: 'all 0.15s', borderLeft: activeAgent === a.id ? `3px solid ${a.color}` : '3px solid transparent',
            }}
            onMouseEnter={e => { if (activeAgent !== a.id) e.currentTarget.style.background = 'var(--bg-elevated)'; }}
            onMouseLeave={e => { if (activeAgent !== a.id) e.currentTarget.style.background = 'transparent'; }}
          >
            <span style={{ fontSize: 18, color: a.color, flexShrink: 0 }}>{a.icon}</span>
            {!collapsed && (
              <div style={{ textAlign: 'left' }}>
                <div style={{ fontWeight: 500, lineHeight: 1.3 }}>{a.name}</div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{a.desc}</div>
              </div>
            )}
          </button>
        ))}
      </div>

      {/* Recent conversations */}
      {!collapsed && conversations.length > 0 && (
        <>
          <div style={{ padding: '12px 12px 6px', fontSize: 10, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 1 }}>Recent</div>
          <div style={{ flex: 1, overflowY: 'auto', padding: '0 8px' }}>
            {conversations.slice(0, 10).map((conv, i) => (
              <button key={i} style={{ width: '100%', padding: '8px 12px', borderRadius: 8, border: 'none', background: 'transparent', color: 'var(--text-secondary)', cursor: 'pointer', textAlign: 'left', fontSize: 12, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', transition: 'all 0.1s' }}
                onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-elevated)'}
                onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
              >{conv}</button>
            ))}
          </div>
        </>
      )}

      {/* Bottom status */}
      <div style={{ padding: '12px 8px', borderTop: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: 8 }}>
        <div style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--success)', boxShadow: '0 0 6px var(--success)', flexShrink: 0 }}></div>
        {!collapsed && <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>Live · Render Free</span>}
      </div>
    </div>
  );
}
