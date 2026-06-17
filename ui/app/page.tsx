'use client';
import { useState, useRef, useEffect } from 'react';
import Sidebar from '../components/Sidebar';
import MessageBubble from '../components/MessageBubble';
import VoiceButton from '../components/VoiceButton';
import StatusBar from '../components/StatusBar';

const API = process.env.NEXT_PUBLIC_API_URL || 'https://jarvis-mq5i.onrender.com';

const WELCOME = {
  role: 'assistant',
  content: 'Hey — I'm JARVIS. Your personal AI operating system. I have access to web search, browser automation, code execution, memory across all our conversations, and voice. What are we working on?',
  agent: 'JARVIS OS',
  timestamp: Date.now(),
};

const SUGGESTIONS = [
  'Search the web for the latest AI agent frameworks',
  'Write a Python script to analyze CSV data',
  'What do you remember about my projects?',
  'Research and summarize the Hermes Agent architecture',
];

export default function Home() {
  const [messages, setMessages] = useState([WELCOME]);
  const [input, setInput] = useState('');
  const [streaming, setStreaming] = useState(false);
  const [agent, setAgent] = useState('jarvis');
  const [mode, setMode] = useState('chat');
  const [agentStatus, setAgentStatus] = useState('Ready');
  const [conversations, setConversations] = useState(['Getting started with JARVIS']);
  const bottomRef = useRef(null);
  const textareaRef = useRef(null);
  const historyRef = useRef([]);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);

  const autoResize = () => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 160) + 'px';
  };

  const sendMessage = async (text) => {
    const content = (text || input).trim();
    if (!content || streaming) return;
    setInput('');
    if (textareaRef.current) textareaRef.current.style.height = 'auto';

    const userMsg = { role: 'user', content, timestamp: Date.now() };
    const newMsgs = [...messages, userMsg];
    setMessages(newMsgs);
    historyRef.current = [...historyRef.current, { role: 'user', content }];

    // Save to recent conversations
    if (messages.length === 1) {
      setConversations(prev => [content.slice(0, 50), ...prev.slice(0, 9)]);
    }

    setStreaming(true);
    setAgentStatus('Processing...');

    try {
      const resp = await fetch(`${API}/chat`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: content, conversation_history: historyRef.current.slice(-10), agent_preference: agent }),
      });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = await resp.json();
      const reply = data.response || data.message || 'No response';
      const agentName = data.agent_used || 'JARVIS';

      const aiMsg = { role: 'assistant', content: reply, agent: agentName, timestamp: Date.now() };
      setMessages(prev => [...prev, aiMsg]);
      historyRef.current = [...historyRef.current, { role: 'assistant', content: reply }];
      setAgentStatus(`${agentName} · ${data.memory_context ? data.memory_context + ' memories' : 'ready'}`);
    } catch (e) {
      setMessages(prev => [...prev, { role: 'assistant', content: `Error: ${e.message}. Check that JARVIS backend is running.`, agent: 'System', timestamp: Date.now() }]);
      setAgentStatus('Error');
    }
    setStreaming(false);
  };

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
  };

  const newChat = () => {
    setMessages([WELCOME]);
    historyRef.current = [];
    setAgentStatus('Ready');
  };

  const isEmpty = messages.length === 1 && messages[0] === WELCOME;

  return (
    <div style={{ display: 'flex', height: '100vh', overflow: 'hidden', background: 'var(--bg-base)' }}>
      <Sidebar activeAgent={agent} onAgentSelect={setAgent} conversations={conversations} onNewChat={newChat} />

      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        <StatusBar mode={mode} onModeChange={setMode} streaming={streaming} agentStatus={agentStatus} />

        {/* Messages */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '24px 0' }}>
          <div style={{ maxWidth: 760, margin: '0 auto', padding: '0 20px' }}>
            {messages.map((msg, i) => <MessageBubble key={i} msg={msg} />)}

            {streaming && (
              <div className="fade-in" style={{ display: 'flex', gap: 10, alignItems: 'flex-start', marginBottom: 16 }}>
                <div style={{ width: 32, height: 32, borderRadius: 10, background: 'linear-gradient(135deg, #7c6aff, #00d4ff)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 14, fontWeight: 700, flexShrink: 0, marginTop: 2 }}>J</div>
                <div className="message-ai" style={{ padding: '12px 16px', display: 'flex', gap: 5, alignItems: 'center' }}>
                  {[0,1,2].map(i => <div key={i} className="typing-dot" style={{ width: 7, height: 7, borderRadius: '50%', background: 'var(--text-secondary)' }}></div>)}
                </div>
              </div>
            )}

            {/* Suggestion chips — only on welcome screen */}
            {isEmpty && (
              <div style={{ marginTop: 32 }}>
                <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 12, textAlign: 'center' }}>Try asking</div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                  {SUGGESTIONS.map((s, i) => (
                    <button key={i} onClick={() => sendMessage(s)}
                      style={{ padding: '12px 14px', borderRadius: 12, border: '1px solid var(--border)', background: 'var(--bg-elevated)', color: 'var(--text-secondary)', cursor: 'pointer', fontSize: 13, textAlign: 'left', lineHeight: 1.4, transition: 'all 0.15s' }}
                      onMouseEnter={e => { e.currentTarget.style.borderColor = 'var(--accent)'; e.currentTarget.style.color = 'var(--text-primary)'; }}
                      onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--border)'; e.currentTarget.style.color = 'var(--text-secondary)'; }}
                    >{s}</button>
                  ))}
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>
        </div>

        {/* Input area */}
        <div style={{ padding: '16px 20px', borderTop: '1px solid var(--border)', background: 'var(--bg-surface)' }}>
          <div style={{ maxWidth: 760, margin: '0 auto' }}>
            <div className="input-glow" style={{ display: 'flex', alignItems: 'flex-end', gap: 10, background: 'var(--bg-input)', border: '1px solid var(--border)', borderRadius: 16, padding: '10px 12px', transition: 'all 0.15s' }}>
              <textarea
                ref={textareaRef}
                value={input}
                onChange={e => { setInput(e.target.value); autoResize(); }}
                onKeyDown={handleKey}
                placeholder={streaming ? 'JARVIS is thinking...' : 'Message JARVIS…  (Shift+Enter for newline)'}
                rows={1}
                disabled={streaming}
                style={{ flex: 1, background: 'none', border: 'none', outline: 'none', color: 'var(--text-primary)', fontSize: 14, resize: 'none', lineHeight: 1.6, maxHeight: 160, overflowY: 'auto', fontFamily: 'Inter, sans-serif', paddingTop: 2 }}
              />
              <VoiceButton onTranscript={t => { setInput(t); setTimeout(() => sendMessage(t), 100); }} disabled={streaming} />
              <button
                onClick={() => sendMessage()}
                disabled={!input.trim() || streaming}
                style={{ width: 40, height: 40, borderRadius: 12, border: 'none', background: input.trim() && !streaming ? 'var(--accent)' : 'var(--bg-elevated)', color: input.trim() && !streaming ? 'white' : 'var(--text-muted)', cursor: input.trim() && !streaming ? 'pointer' : 'default', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 16, flexShrink: 0, transition: 'all 0.15s' }}
              >↑</button>
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-muted)', textAlign: 'center', marginTop: 8 }}>
              JARVIS v1.0 · {API.replace('https://','')} · Memory enabled
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
