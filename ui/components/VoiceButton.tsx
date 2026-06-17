'use client';
import { useState, useRef } from 'react';

export default function VoiceButton({ onTranscript, disabled }) {
  const [recording, setRecording] = useState(false);
  const [level, setLevel] = useState(0);
  const mediaRef = useRef(null);
  const chunksRef = useRef([]);
  const analyserRef = useRef(null);
  const animRef = useRef(null);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const ctx = new AudioContext();
      const src = ctx.createMediaStreamSource(stream);
      const analyser = ctx.createAnalyser();
      analyser.fftSize = 256;
      src.connect(analyser);
      analyserRef.current = analyser;

      const animate = () => {
        const data = new Uint8Array(analyser.frequencyBinCount);
        analyser.getByteFrequencyData(data);
        setLevel(data.reduce((a, b) => a + b, 0) / data.length / 255);
        animRef.current = requestAnimationFrame(animate);
      };
      animate();

      const recorder = new MediaRecorder(stream);
      chunksRef.current = [];
      recorder.ondataavailable = e => chunksRef.current.push(e.data);
      recorder.onstop = async () => {
        cancelAnimationFrame(animRef.current);
        setLevel(0);
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
        const base64 = await new Promise(res => {
          const reader = new FileReader();
          reader.onloadend = () => res(reader.result.split(',')[1]);
          reader.readAsDataURL(blob);
        });
        try {
          const resp = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/voice/transcribe`, {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ audio_b64: base64, mime_type: 'audio/webm' })
          });
          const data = await resp.json();
          if (data.transcript) onTranscript(data.transcript);
        } catch { /* fallback: ignore */ }
        stream.getTracks().forEach(t => t.stop());
      };
      recorder.start();
      mediaRef.current = recorder;
      setRecording(true);
    } catch (e) { console.error('Mic error:', e); }
  };

  const stopRecording = () => {
    if (mediaRef.current?.state === 'recording') { mediaRef.current.stop(); setRecording(false); }
  };

  const sz = 40;
  const glow = recording ? level * 40 : 0;

  return (
    <button
      onMouseDown={startRecording} onMouseUp={stopRecording} onTouchStart={startRecording} onTouchEnd={stopRecording}
      disabled={disabled}
      style={{
        width: sz, height: sz, borderRadius: '50%', border: 'none', cursor: disabled ? 'not-allowed' : 'pointer',
        background: recording ? 'var(--accent)' : 'var(--bg-elevated)',
        color: recording ? 'white' : 'var(--text-secondary)',
        display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 18, flexShrink: 0, transition: 'all 0.15s',
        boxShadow: recording ? `0 0 ${glow}px var(--accent)` : 'none',
        opacity: disabled ? 0.5 : 1,
      }}
      title={recording ? 'Release to send' : 'Hold to talk'}
    >
      {recording ? '⏹' : '🎤'}
    </button>
  );
}
