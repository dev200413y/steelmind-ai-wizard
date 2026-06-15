import React, { useEffect, useMemo, useRef, useState } from 'react';

const API_BASE = import.meta.env.VITE_API_URL || 'https://steelmind-ai-wizard-production.up.railway.app';

const AGENT_MAP = {
  orchestrator: 'orchestrator',
  vision_agent: 'vision',
  rag_agent: 'rag',
  anomaly_agent: 'anomaly',
  diagnostic_agent: 'diagnostic',
  risk_scorer: 'risk',
  report_generator: 'report',
  idle: 'done',
};

const AGENT_LABELS = {
  orchestrator: 'Intent routing',
  vision: 'Visual reasoning',
  rag: 'Knowledge retrieval',
  anomaly: 'Sensor analytics',
  diagnostic: 'Root-cause synthesis',
  risk: 'Risk scoring',
  report: 'Report assembly',
  done: 'Response ready',
};

const SAMPLE_PROMPTS = [
  'How can I help you today? I see a burner issue that is not working.',
  'Please diagnose the vibration problem in Rolling Mill 1.',
  'You can speak naturally even if you do not upload any file.',
];

function makeSessionId() {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID().slice(0, 12);
  }
  return `${Date.now()}`.slice(-12);
}

function formatTime() {
  return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function mapNodeToAgent(node) {
  return AGENT_MAP[node] || 'orchestrator';
}

function speakWithBrowser(text, language) {
  if (!('speechSynthesis' in window) || !text) return false;
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text.slice(0, 500));
  utterance.lang = language || 'en';
  window.speechSynthesis.speak(utterance);
  return true;
}

function pulseTrail(setter) {
  let tick = 0;
  const interval = window.setInterval(() => {
    tick += 1;
    setter(0.35 + ((tick % 5) / 10));
  }, 180);
  return () => window.clearInterval(interval);
}

async function safeCloseAudioContext(audioCtxRef) {
  const audioCtx = audioCtxRef.current;
  if (!audioCtx) return;
  audioCtxRef.current = null;
  if (audioCtx.state === 'closed') return;
  try {
    await audioCtx.close();
  } catch (error) {
    if (error?.name !== 'InvalidStateError') {
      throw error;
    }
  }
}

function getTimeGreeting() {
  const hour = new Date().getHours();
  if (hour < 12) return 'Good morning';
  if (hour < 17) return 'Good afternoon';
  return 'Good evening';
}

export default function VoiceAgentExperience({
  equipmentId,
  equipmentType,
  selectedEquip,
  onConversationComplete,
}) {
  const [phase, setPhase] = useState('idle');
  const [recordingStatus, setRecordingStatus] = useState('Tap the orb and speak naturally.');
  const [transcript, setTranscript] = useState('');
  const [detectedLanguage, setDetectedLanguage] = useState('auto');
  const [activeAgent, setActiveAgent] = useState('');
  const [liveStatus, setLiveStatus] = useState('Voice copilot ready');
  const [statusTrail, setStatusTrail] = useState([]);
  const [liveData, setLiveData] = useState({});
  const [micLevel, setMicLevel] = useState(0.08);
  const [assistantLevel, setAssistantLevel] = useState(0.08);
  const [turns, setTurns] = useState([]);
  const [audioPlaying, setAudioPlaying] = useState(false);
  const [error, setError] = useState('');
  const [attachments, setAttachments] = useState([]);
  const [hasPlayedWelcome, setHasPlayedWelcome] = useState(false);
  const [micPermissionState, setMicPermissionState] = useState('unknown');

  const mediaRecorderRef = useRef(null);
  const streamRef = useRef(null);
  const audioChunksRef = useRef([]);
  const silenceTimerRef = useRef(null);
  const audioCtxRef = useRef(null);
  const rafRef = useRef(null);
  const audioRef = useRef(null);
  const wsRef = useRef(null);
  const wsConnectPromiseRef = useRef(null);
  const pendingTurnRef = useRef(null);
  const sessionIdRef = useRef(makeSessionId());
  const imageInputRef = useRef(null);
  const csvInputRef = useRef(null);
  const docInputRef = useRef(null);

  useEffect(() => {
    if (navigator?.permissions?.query) {
      navigator.permissions.query({ name: 'microphone' }).then((status) => {
        setMicPermissionState(status.state);
        status.onchange = () => setMicPermissionState(status.state);
      }).catch(() => {});
    }

    return () => {
      if (rafRef.current) window.cancelAnimationFrame(rafRef.current);
      if (silenceTimerRef.current) window.clearTimeout(silenceTimerRef.current);
      safeCloseAudioContext(audioCtxRef);
      if (streamRef.current) streamRef.current.getTracks().forEach((track) => track.stop());
      if (wsRef.current) wsRef.current.close();
    };
  }, []);

  const summaryText = useMemo(() => {
    return (
      liveData.chat_response ||
      liveData.report?.summary ||
      liveData.diagnosis?.fault_identified ||
      'Natural multilingual voice copilot ready'
    );
  }, [liveData]);

  const riskLabel = liveData.risk_level || '--';
  const rulDays = liveData.anomaly_result?.rul_days;
  const docsCount = liveData.rag_context?.length;

  const pushStatus = (status, node) => {
    setLiveStatus(status);
    setActiveAgent(mapNodeToAgent(node));
    setStatusTrail((prev) => {
      const next = [{ status, node, time: formatTime() }, ...prev];
      const deduped = [];
      for (const item of next) {
        if (!deduped.find((entry) => entry.status === item.status && entry.node === item.node)) {
          deduped.push(item);
        }
      }
      return deduped.slice(0, 6);
    });
  };

  const ensureWebSocket = async () => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      return wsRef.current;
    }
    if (wsConnectPromiseRef.current) {
      return wsConnectPromiseRef.current;
    }

    wsConnectPromiseRef.current = new Promise((resolve, reject) => {
      const ws = new WebSocket(`${API_BASE.replace('http', 'ws')}/ws/chat/${sessionIdRef.current}`);
      wsRef.current = ws;

      ws.onopen = () => {
        wsConnectPromiseRef.current = null;
        resolve(ws);
      };

      ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          if (payload.type === 'status') {
            pushStatus(payload.status, payload.node);
            return;
          }
          if (payload.type === 'state') {
            setLiveData((prev) => ({ ...prev, ...payload.data }));
            return;
          }
          if (payload.type === 'message') {
            setLiveData((prev) => ({ ...prev, chat_response: payload.content }));
            return;
          }
          if (payload.type === 'complete') {
            const result = payload.data || {};
            setLiveData((prev) => ({ ...prev, ...result }));
            pushStatus('Response ready', 'idle');
            if (pendingTurnRef.current) {
              pendingTurnRef.current.resolve(result);
              pendingTurnRef.current = null;
            }
            return;
          }
          if (payload.type === 'error') {
            throw new Error(payload.content || 'Voice socket failed');
          }
        } catch (err) {
          if (pendingTurnRef.current) {
            pendingTurnRef.current.reject(err);
            pendingTurnRef.current = null;
          }
          setError(err.message || 'Voice stream parsing failed');
          setPhase('error');
        }
      };

      ws.onerror = () => {
        wsConnectPromiseRef.current = null;
        reject(new Error('WebSocket connection failed'));
      };

      ws.onclose = () => {
        wsConnectPromiseRef.current = null;
        wsRef.current = null;
        if (pendingTurnRef.current) {
          pendingTurnRef.current.reject(new Error('Voice session disconnected'));
          pendingTurnRef.current = null;
        }
      };
    });

    return wsConnectPromiseRef.current;
  };

  const sendTranscriptToCopilot = async (text, language) => {
    const ws = await ensureWebSocket();
    return new Promise((resolve, reject) => {
      pendingTurnRef.current = { resolve, reject };
      ws.send(
        JSON.stringify({
          text,
          language,
          equipment_id: equipmentId || undefined,
          equipment_type: equipmentType || undefined,
          image_paths: attachments.filter((item) => item.category === 'image').map((item) => item.path),
          csv_paths: attachments.filter((item) => item.category === 'csv').map((item) => item.path),
          doc_paths: attachments.filter((item) => item.category === 'document' || item.category === 'pdf').map((item) => item.path),
        }),
      );
    });
  };

  const uploadAttachment = async (file, category) => {
    const fd = new FormData();
    fd.append('file', file);
    fd.append('category', category);

    const response = await fetch(`${API_BASE}/api/session/upload`, {
      method: 'POST',
      body: fd,
    });
    if (!response.ok) {
      throw new Error('Attachment upload failed');
    }

    const payload = await response.json();
    setAttachments((prev) => [
      ...prev,
      {
        name: payload.filename,
        category: payload.category,
        path: payload.path,
      },
    ]);
  };

  const handleAttachmentSelect = async (event, category) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      setRecordingStatus('Uploading attachment...');
      await uploadAttachment(file, category);
      setRecordingStatus('Attachment ready. You can speak now.');
      setError('');
    } catch (err) {
      setError(err.message || 'Attachment upload failed');
    } finally {
      event.target.value = '';
    }
  };

  const removeAttachment = (path) => {
    setAttachments((prev) => prev.filter((item) => item.path !== path));
  };

  const playAssistantVoice = async (text, language) => {
    if (!text) return;
    setAudioPlaying(true);
    setPhase('speaking');
    const stopPulse = pulseTrail(setAssistantLevel);
    try {
      const fd = new FormData();
      fd.append('text', text);
      fd.append('language', language || 'en');
      const response = await fetch(`${API_BASE}/api/voice/tts`, { method: 'POST', body: fd });
      if (!response.ok) {
        throw new Error('TTS request failed');
      }
      const blob = await response.blob();
      const audio = new Audio(URL.createObjectURL(blob));
      audioRef.current = audio;
      audio.onended = () => {
        stopPulse();
        setAssistantLevel(0.08);
        setAudioPlaying(false);
        setPhase('idle');
        audioRef.current = null;
        window.setTimeout(() => startRecording(), 350);
      };
      await audio.play();
    } catch (err) {
      stopPulse();
      setAssistantLevel(0.08);
      setAudioPlaying(false);
      const usedBrowserVoice = speakWithBrowser(text, language || 'en');
      setPhase(usedBrowserVoice ? 'speaking' : 'idle');
      if (usedBrowserVoice) {
        window.setTimeout(() => setPhase('idle'), Math.min(9000, Math.max(2500, text.length * 45)));
      }
    }
  };

  const playWelcomePrompt = async () => {
    const greeting = `${getTimeGreeting()}. I am OmniSense AI. How can I help you today?`;
    setTurns((prev) => {
      if (prev.some((turn) => turn.role === 'assistant' && turn.text === greeting)) {
        return prev;
      }
      return [{ role: 'assistant', text: greeting, time: formatTime() }, ...prev].slice(0, 5);
    });
    setRecordingStatus('Assistant greeting is playing...');
    await playAssistantVoice(greeting, 'en');
    setRecordingStatus('Listening. Recording stops automatically after silence.');
  };

  const transcribeAudio = async (audioBlob) => {
    const fd = new FormData();
    fd.append('audio', audioBlob, 'recording.webm');
    const response = await fetch(`${API_BASE}/api/voice/stt`, {
      method: 'POST',
      body: fd,
    });
    if (!response.ok) {
      throw new Error('Speech-to-text failed');
    }
    return response.json();
  };

  const handleVoiceTurn = async (audioBlob) => {
    setError('');
    setPhase('transcribing');
    setRecordingStatus('Transcribing your speech...');
    setMicLevel(0.08);
    setLiveData({});
    setActiveAgent('orchestrator');

    try {
      const stt = await transcribeAudio(audioBlob);
      const text = (stt.text || '').trim();
      const language = stt.language || 'en';

      if (!text) {
        throw new Error('Speech was not clear enough. Please try again.');
      }

      setTranscript(text);
      setDetectedLanguage(language);
      setTurns((prev) => [{ role: 'user', text, time: formatTime() }, ...prev].slice(0, 5));
      setPhase('thinking');
      setRecordingStatus('Analyzing with live agents...');
      pushStatus('Transcript captured', 'orchestrator');

      const result = await sendTranscriptToCopilot(text, language);

      const assistantText =
        result.chat_response ||
        result.report?.summary ||
        result.diagnosis?.fault_identified ||
        'Analysis complete';

      setTurns((prev) => [{ role: 'assistant', text: assistantText, time: formatTime() }, ...prev].slice(0, 5));

      if (onConversationComplete) {
        onConversationComplete({
          transcript: text,
          result,
        });
      }

      setRecordingStatus('Response ready');
      await playAssistantVoice(assistantText, language);
    } catch (err) {
      setError(err.message || 'Voice pipeline failed');
      setRecordingStatus('Voice flow failed');
      setPhase('error');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current?.state === 'recording') {
      mediaRecorderRef.current.stop();
    }
  };

  const startRecording = async () => {
    if (phase === 'transcribing' || phase === 'thinking') return;

    try {
      setError('');
      if (!hasPlayedWelcome) {
        setHasPlayedWelcome(true);
        await playWelcomePrompt();
      }
      setPhase('listening');
      setRecordingStatus('Listening. Recording stops automatically after silence.');
      setTranscript('');
      setLiveStatus('Listening for your issue');
      setStatusTrail([]);

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      audioChunksRef.current = [];

      const preferredMimeType = typeof MediaRecorder !== 'undefined' && MediaRecorder.isTypeSupported
        ? (MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
            ? 'audio/webm;codecs=opus'
            : MediaRecorder.isTypeSupported('audio/webm')
              ? 'audio/webm'
              : '')
        : '';
      const recorder = preferredMimeType ? new MediaRecorder(stream, { mimeType: preferredMimeType }) : new MediaRecorder(stream);
      mediaRecorderRef.current = recorder;

      const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      audioCtxRef.current = audioCtx;
      const source = audioCtx.createMediaStreamSource(stream);
      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 256;
      source.connect(analyser);

      const dataArray = new Uint8Array(analyser.frequencyBinCount);
      const startAt = Date.now();

      const monitor = () => {
        if (recorder.state !== 'recording') return;
        analyser.getByteFrequencyData(dataArray);
        const average = dataArray.reduce((sum, value) => sum + value, 0) / dataArray.length;
        const normalized = Math.min(1, average / 60);
        setMicLevel(Math.max(0.08, normalized));

        if (Date.now() - startAt > 1500) {
          if (average < 5) {
            if (!silenceTimerRef.current) {
              silenceTimerRef.current = window.setTimeout(() => stopRecording(), 1800);
            }
          } else if (silenceTimerRef.current) {
            window.clearTimeout(silenceTimerRef.current);
            silenceTimerRef.current = null;
          }
        }

        rafRef.current = window.requestAnimationFrame(monitor);
      };

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) audioChunksRef.current.push(event.data);
      };

      recorder.onstop = async () => {
        if (rafRef.current) window.cancelAnimationFrame(rafRef.current);
        if (silenceTimerRef.current) {
          window.clearTimeout(silenceTimerRef.current);
          silenceTimerRef.current = null;
        }
        await safeCloseAudioContext(audioCtxRef);
        if (streamRef.current) {
          streamRef.current.getTracks().forEach((track) => track.stop());
          streamRef.current = null;
        }

        const blob = new Blob(audioChunksRef.current, { type: preferredMimeType || 'audio/webm' });
        await handleVoiceTurn(blob);
      };

      recorder.start(120);
      monitor();
    } catch (err) {
      setPhase('error');
      setRecordingStatus('Microphone access failed');
      setError(
        micPermissionState === 'denied'
          ? 'Microphone permission is blocked for this site. Open browser site settings and allow mic access, then refresh.'
          : 'Microphone permission is unavailable right now. Use text chat or allow mic access from the browser.'
      );
    }
  };

  const handleVoiceToggle = () => {
    if (audioPlaying) {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current.currentTime = 0;
        audioRef.current = null;
      }
      window.speechSynthesis?.cancel?.();
      setAudioPlaying(false);
      setPhase('idle');
      startRecording();
      return;
    }
    if (phase === 'listening') {
      stopRecording();
      return;
    }
    startRecording();
  };

  const orbScale = phase === 'listening' ? 1 + micLevel * 0.18 : audioPlaying ? 1 + assistantLevel * 0.12 : phase === 'thinking' ? 1.05 : 1;
  const orbGlow =
    phase === 'listening'
      ? `0 0 80px rgba(239,68,68,${0.25 + micLevel * 0.45})`
      : audioPlaying
        ? `0 0 80px rgba(59,130,246,${0.25 + assistantLevel * 0.45})`
        : phase === 'thinking'
          ? '0 0 65px rgba(16,185,129,0.35)'
          : '0 0 45px rgba(59,130,246,0.18)';

  return (
    <div className="voice-agent-shell">
      <div className="voice-agent-topbar">
        <div className="voice-chip">Session {sessionIdRef.current}</div>
        <div className="voice-chip">Language {detectedLanguage.toUpperCase()}</div>
        <div className="voice-chip">
          {selectedEquip ? `${selectedEquip.id} · ${selectedEquip.name}` : 'No equipment context'}
        </div>
        <button
          type="button"
          className="voice-chip"
          onClick={playWelcomePrompt}
          style={{ cursor: 'pointer', background: 'rgba(59,130,246,0.12)', color: '#dbeafe' }}
        >
          Play Greeting
        </button>
      </div>

      <div className="voice-upload-strip">
        <input ref={imageInputRef} type="file" accept="image/*" style={{ display: 'none' }} onChange={(event) => handleAttachmentSelect(event, 'image')} />
        <input ref={csvInputRef} type="file" accept=".csv" style={{ display: 'none' }} onChange={(event) => handleAttachmentSelect(event, 'csv')} />
        <input ref={docInputRef} type="file" accept=".pdf,.txt" style={{ display: 'none' }} onChange={(event) => handleAttachmentSelect(event, 'document')} />

        <button type="button" className="voice-upload-btn" onClick={() => imageInputRef.current?.click()}>
          Add Image
        </button>
        <button type="button" className="voice-upload-btn" onClick={() => csvInputRef.current?.click()}>
          Add CSV
        </button>
        <button type="button" className="voice-upload-btn" onClick={() => docInputRef.current?.click()}>
          Add Document / PDF
        </button>
      </div>

      {attachments.length > 0 && (
        <div className="voice-attachment-pills">
          {attachments.map((item) => (
            <div key={item.path} className="voice-attachment-pill">
              <span>{item.category.toUpperCase()}</span>
              <strong>{item.name}</strong>
              <button type="button" onClick={() => removeAttachment(item.path)}>x</button>
            </div>
          ))}
        </div>
      )}

      <div className="voice-agent-grid">
        <div className="voice-panel">
          <div className="voice-panel-title">Live Transcript</div>
          <div className="voice-transcript-card">
            <div className="voice-transcript-label">Engineer said</div>
            <div className="voice-transcript-text">
              {transcript || 'Your live transcript appears here after you speak.'}
            </div>
          </div>

          <div className="voice-panel-subtitle">Recent Turns</div>
          <div className="voice-turns">
            {turns.length === 0 ? (
              SAMPLE_PROMPTS.map((prompt) => (
                <div key={prompt} className="voice-turn-chip muted">
                  {prompt}
                </div>
              ))
            ) : (
              turns.map((turn, index) => (
                <div key={`${turn.role}-${index}-${turn.time}`} className={`voice-turn-chip ${turn.role}`}>
                  <span>{turn.role === 'user' ? 'You' : 'OmniSense'}</span>
                  <strong>{turn.text}</strong>
                </div>
              ))
            )}
          </div>
        </div>

        <div className="voice-stage">
          <div className="voice-stage-caption">Natural multilingual voice copilot</div>
          <div className="voice-orb-shell">
            <div className="voice-orb-ring ring-a"></div>
            <div className="voice-orb-ring ring-b"></div>
            <button
              type="button"
              className={`voice-orb-button ${phase}`}
              onClick={handleVoiceToggle}
              style={{ transform: `scale(${orbScale})`, boxShadow: orbGlow }}
            >
              <div className="voice-orb-core">
                {phase === 'listening' ? 'Stop' : phase === 'thinking' ? 'Think' : audioPlaying ? 'Speak' : 'Talk'}
              </div>
              <div className="voice-bars">
                {Array.from({ length: 5 }).map((_, index) => {
                  const base = phase === 'listening' ? micLevel : audioPlaying ? assistantLevel : phase === 'thinking' ? 0.45 : 0.12;
                  const height = 14 + ((index % 2 === 0 ? 1.2 : 0.8) * base * 48);
                  return <span key={index} style={{ height }}></span>;
                })}
              </div>
            </button>
          </div>

          <div className="voice-stage-title">
            {phase === 'listening'
              ? 'Listening'
              : phase === 'transcribing'
                ? 'Transcribing'
                : phase === 'thinking'
                  ? 'Analyzing'
                  : phase === 'speaking'
                    ? 'Speaking'
                    : phase === 'error'
                      ? 'Needs Retry'
                      : 'Ready'}
          </div>
          <div className="voice-stage-subtitle">{recordingStatus}</div>
          <div className="voice-status-live">{liveStatus}</div>
          {micPermissionState !== 'granted' && (
            <div className="voice-error-banner" style={{ marginTop: 12 }}>
              Microphone permission is {micPermissionState}. If voice does not start, use the browser site settings for localhost and allow microphone access.
            </div>
          )}
          {error && <div className="voice-error-banner">{error}</div>}
        </div>

        <div className="voice-panel">
          <div className="voice-panel-title">Live Ops Data</div>
          <div className="voice-kpi-grid">
            <div className="voice-kpi-card">
              <span>Risk</span>
              <strong>{riskLabel}</strong>
            </div>
            <div className="voice-kpi-card">
              <span>RUL</span>
              <strong>{rulDays != null ? `${rulDays}d` : '--'}</strong>
            </div>
            <div className="voice-kpi-card">
              <span>Docs</span>
              <strong>{docsCount != null ? docsCount : '--'}</strong>
            </div>
            <div className="voice-kpi-card">
              <span>Agent</span>
              <strong>{AGENT_LABELS[activeAgent] || 'Standby'}</strong>
            </div>
          </div>

          <div className="voice-live-summary">
            <div className="voice-panel-subtitle">Copilot Summary</div>
            <p>{summaryText}</p>
          </div>

          <div className="voice-panel-subtitle">Agent Timeline</div>
          <div className="voice-status-list">
            {statusTrail.length === 0 ? (
              <div className="voice-status-item muted">Realtime agent progress appears here during analysis.</div>
            ) : (
              statusTrail.map((item, index) => (
                <div key={`${item.node}-${item.status}-${index}`} className="voice-status-item">
                  <span className="voice-status-node">{AGENT_LABELS[mapNodeToAgent(item.node)] || item.node}</span>
                  <span className="voice-status-text">{item.status}</span>
                  <span className="voice-status-time">{item.time}</span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
