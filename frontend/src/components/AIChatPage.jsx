import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { runQuery, submitFeedback } from '../api';

const API = 'http://localhost:8000';

const EQUIPMENT_LIST = [
  { id: '', name: 'Select Equipment...', type: '' },
  { id: 'BF-001', name: 'Blast Furnace 1', type: 'Blast Furnace', plant: 'Jamshedpur' },
  { id: 'BF-002', name: 'Blast Furnace 2', type: 'Blast Furnace', plant: 'Jamshedpur' },
  { id: 'RM-001', name: 'Rolling Mill 1', type: 'Rolling Mill', plant: 'Jamshedpur' },
  { id: 'RM-002', name: 'Rolling Mill 2', type: 'Rolling Mill', plant: 'Kalinganagar' },
  { id: 'CC-001', name: 'Continuous Caster 1', type: 'Continuous Caster', plant: 'Jamshedpur' },
  { id: 'HS-001', name: 'Hydraulic System 1', type: 'Hydraulic System', plant: 'Jamshedpur' },
  { id: 'EAF-001', name: 'Electric Arc Furnace 1', type: 'Electric Arc Furnace', plant: 'Kalinganagar' },
  { id: 'CV-001', name: 'Conveyor System 1', type: 'Conveyor System', plant: 'IJmuiden' },
  { id: 'CP-001', name: 'Compressor 1', type: 'Compressor', plant: 'Port Talbot' },
];

const AGENTS = [
  { id: 'orchestrator', label: 'Orchestrator', desc: 'Routing inputs', icon: '🎯' },
  { id: 'vision', label: 'Vision Agent', desc: 'Analyzing image', icon: '👁️' },
  { id: 'rag', label: 'RAG Agent', desc: 'Searching manuals', icon: '📚' },
  { id: 'anomaly', label: 'Anomaly Agent', desc: 'Sensor analysis', icon: '📡' },
  { id: 'diagnostic', label: 'Diagnostic Agent', desc: 'Synthesizing', icon: '🔍' },
  { id: 'risk', label: 'Risk Scorer', desc: 'Risk assessment', icon: '⚠️' },
  { id: 'report', label: 'Report Generator', desc: 'Building report', icon: '📋' },
];

const RISK_CONFIG = {
  LOW:      { color: '#22c55e', bg: 'rgba(34,197,94,0.15)',  label: 'LOW RISK' },
  MEDIUM:   { color: '#eab308', bg: 'rgba(234,179,8,0.15)',  label: 'MEDIUM RISK' },
  HIGH:     { color: '#f97316', bg: 'rgba(249,115,22,0.15)', label: 'HIGH RISK' },
  CRITICAL: { color: '#ef4444', bg: 'rgba(239,68,68,0.15)',  label: 'CRITICAL RISK' },
};

const LANG_LABELS = { en: '🇬🇧 EN', hi: '🇮🇳 HI', bn: '🇮🇳 BN', or: '🇮🇳 OR', th: '🇹🇭 TH', nl: '🇳🇱 NL' };

function detectLanguage(text) {
  if (!text) return 'en';
  if (/[\u0900-\u097F]/.test(text)) return 'hi';
  if (/[\u0980-\u09FF]/.test(text)) return 'bn';
  if (/[\u0B00-\u0B7F]/.test(text)) return 'or';
  if (/[\u0E00-\u0E7F]/.test(text)) return 'th';
  if (/\b(de|het|een|van|en|in|dat|die|niet)\b/i.test(text)) return 'nl';
  return 'en';
}

const SUGGESTIONS = [
  { icon: '🔥', text: 'BF-001 showing high temperature readings — what could be causing it?' },
  { icon: '📉', text: 'Rolling Mill 1 vibration is abnormal. Run full diagnostic.' },
  { icon: '⚡', text: 'EAF-001 electrode breakage happening frequently — root cause analysis' },
  { icon: '🛢️', text: 'Hydraulic system pressure dropping intermittently — diagnose' },
];

export default function AIChatPage() {
  // Chat messages: { role: 'user'|'assistant'|'system', content: ..., data: ..., timestamp }
  const [chatMode, setChatMode] = useState('text'); // 'text' | 'voice'
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState('');
  const [detectedLang, setDetectedLang] = useState('en');
  const [equipmentId, setEquipmentId] = useState('');
  const [equipmentType, setEquipmentType] = useState('');
  const [image, setImage] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [csv, setCsv] = useState(null);
  const [pdf, setPdf] = useState(null);
  const [loading, setLoading] = useState(false);
  const [activeAgent, setActiveAgent] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [recordingStatus, setRecordingStatus] = useState('');
  const [audioPlaying, setAudioPlaying] = useState(false);
  const [showAttachMenu, setShowAttachMenu] = useState(false);
  const [showEquipSelect, setShowEquipSelect] = useState(false);

  const imgRef = useRef(null);
  const csvRef = useRef(null);
  const pdfRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const chatEndRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    if (inputText) setDetectedLang(detectLanguage(inputText));
  }, [inputText]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const handleEquipmentSelect = (eqId) => {
    const eq = EQUIPMENT_LIST.find(e => e.id === eqId);
    setEquipmentId(eq?.id || '');
    setEquipmentType(eq?.type || '');
    setShowEquipSelect(false);
  };

  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setImage(file);
    const reader = new FileReader();
    reader.onloadend = () => setImagePreview(reader.result);
    reader.readAsDataURL(file);
    setShowAttachMenu(false);
  };

  const silenceTimerRef = useRef(null);
  const audioCtxRef = useRef(null);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioChunksRef.current = [];
      const mr = new MediaRecorder(stream, { mimeType: 'audio/webm' });
      mediaRecorderRef.current = mr;
      
      // Silence Detection Logic
      const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      audioCtxRef.current = audioCtx;
      const source = audioCtx.createMediaStreamSource(stream);
      const analyser = audioCtx.createAnalyser();
      source.connect(analyser);
      analyser.minDecibels = -50;
      const dataArray = new Uint8Array(analyser.frequencyBinCount);
      
      const startTime = Date.now();
      
      const checkSilence = () => {
        if (mr.state !== 'recording') return;
        analyser.getByteFrequencyData(dataArray);
        const avg = dataArray.reduce((a, b) => a + b, 0) / dataArray.length;
        
        // Give a 2 second grace period before checking for silence
        if (Date.now() - startTime > 2000) {
          if (avg < 5) {
            if (!silenceTimerRef.current) {
              silenceTimerRef.current = setTimeout(() => { stopRecording(); }, 10000); // 10 seconds of silence stops it
            }
          } else {
            if (silenceTimerRef.current) { clearTimeout(silenceTimerRef.current); silenceTimerRef.current = null; }
          }
        }
        requestAnimationFrame(checkSilence);
      };

      mr.ondataavailable = (e) => { if (e.data.size > 0) audioChunksRef.current.push(e.data); };
      mr.onstop = async () => {
        if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current);
        if (audioCtxRef.current) audioCtxRef.current.close();
        
        const blob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        stream.getTracks().forEach(t => t.stop());
        
        // Launch Voice Pipeline
        handleVoiceSend(blob);
      };
      
      mr.start(100); // collect 100ms chunks
      checkSilence();
      setIsRecording(true);
      setRecordingStatus('Listening... (auto-stops on silence)');
    } catch { 
      setRecordingStatus('Mic access denied'); 
      setTimeout(() => setRecordingStatus(''), 2000); 
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current?.state === 'recording') {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      setRecordingStatus('');
    }
  };

  const handleVoiceSend = async (audioBlob) => {
    if (loading) return;

    // Add temporary user message
    const tempId = Date.now();
    const userMsg = {
      id: tempId,
      role: 'user',
      content: '🎤 Processing voice input...',
      attachments: [],
      equipment: equipmentId ? EQUIPMENT_LIST.find(e => e.id === equipmentId) : null,
      timestamp: new Date().toLocaleTimeString(),
    };
    if (image) userMsg.attachments.push({ type: 'image', name: image.name, preview: imagePreview });
    if (csv) userMsg.attachments.push({ type: 'csv', name: csv.name });
    
    setMessages(prev => [...prev, userMsg]);
    setLoading(true);
    setActiveAgent('orchestrator');

    const timers = [
      setTimeout(() => setActiveAgent('orchestrator'), 0),
      setTimeout(() => setActiveAgent('vision'), 800),
      setTimeout(() => setActiveAgent('rag'), 1200),
      setTimeout(() => setActiveAgent('anomaly'), 1600),
      setTimeout(() => setActiveAgent('diagnostic'), 3000),
      setTimeout(() => setActiveAgent('risk'), 5500),
      setTimeout(() => setActiveAgent('report'), 7000),
    ];

    try {
      const fd = new FormData();
      fd.append('audio', audioBlob, 'recording.webm');
      if (equipmentId) fd.append('equipment_id', equipmentId);
      if (equipmentType) fd.append('equipment_type', equipmentType);
      if (image) fd.append('image', image);
      if (csv) fd.append('csv_file', csv);

      // Using the new runVoiceQuery from api.js which targets /voice
      const { runVoiceQuery } = await import('../api');
      const res = await runVoiceQuery(fd);
      
      timers.forEach(clearTimeout);
      setActiveAgent('done');

      // Update user message with transcribed text
      setMessages(prev => prev.map(m => m.id === tempId ? { ...m, content: res.transcribed_text || '🎤 Voice Input' } : m));

      // Append AI response
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: res,
        timestamp: new Date().toLocaleTimeString(),
      }]);

      // Auto-play the returned audio if it exists
      if (res.audio_response_path) {
        const audio = new Audio(res.audio_response_path);
        setAudioPlaying(true);
        audio.onended = () => setAudioPlaying(false);
        audio.play();
      }

    } catch (e) {
      timers.forEach(clearTimeout);
      setActiveAgent('error');
      setMessages(prev => prev.map(m => m.id === tempId ? { ...m, content: '🎤 Voice Input (Failed)' } : m));
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: { error: e.response?.data?.detail || e.message || 'Voice Pipeline failed' },
        timestamp: new Date().toLocaleTimeString(),
      }]);
    }

    setLoading(false);
    setImage(null);
    setImagePreview(null);
    setCsv(null);
    setPdf(null);
  };

  const handleVoiceToggle = () => { isRecording ? stopRecording() : startRecording(); };

  const playTTS = async (text) => {
    setAudioPlaying(true);
    try {
      const fd = new FormData();
      fd.append('text', text);
      fd.append('language', detectedLang);
      const resp = await fetch(`${API}/api/voice/tts`, { method: 'POST', body: fd });
      const blob = await resp.blob();
      const audio = new Audio(URL.createObjectURL(blob));
      audio.onended = () => setAudioPlaying(false);
      audio.play();
    } catch { setAudioPlaying(false); }
  };

  const handleSend = async (overrideText) => {
    const text = overrideText || inputText;
    if (!text && !image && !csv) return;
    if (loading) return;

    // Add user message
    const userMsg = {
      role: 'user',
      content: text || 'Analyze attached files',
      attachments: [],
      equipment: equipmentId ? EQUIPMENT_LIST.find(e => e.id === equipmentId) : null,
      timestamp: new Date().toLocaleTimeString(),
    };
    if (image) userMsg.attachments.push({ type: 'image', name: image.name, preview: imagePreview });
    if (csv) userMsg.attachments.push({ type: 'csv', name: csv.name });
    if (pdf) userMsg.attachments.push({ type: 'pdf', name: pdf.name });

    setMessages(prev => [...prev, userMsg]);
    setInputText('');
    setLoading(true);
    setActiveAgent('orchestrator');

    const timers = [
      setTimeout(() => setActiveAgent('orchestrator'), 0),
      setTimeout(() => setActiveAgent('vision'), 800),
      setTimeout(() => setActiveAgent('rag'), 1200),
      setTimeout(() => setActiveAgent('anomaly'), 1600),
      setTimeout(() => setActiveAgent('diagnostic'), 3000),
      setTimeout(() => setActiveAgent('risk'), 5500),
      setTimeout(() => setActiveAgent('report'), 7000),
    ];

    try {
      const fd = new FormData();
      fd.append('query', text || 'Analyze the provided data for maintenance diagnosis.');
      if (equipmentId) fd.append('equipment_id', equipmentId);
      if (equipmentType) fd.append('equipment_type', equipmentType);
      fd.append('language', detectedLang);
      if (image) fd.append('image', image);
      if (csv) fd.append('csv_file', csv);
      if (pdf) fd.append('documents', pdf);

      const res = await runQuery(fd);
      timers.forEach(clearTimeout);
      setActiveAgent('done');

      setMessages(prev => [...prev, {
        role: 'assistant',
        content: res,
        timestamp: new Date().toLocaleTimeString(),
      }]);
    } catch (e) {
      timers.forEach(clearTimeout);
      setActiveAgent('error');
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: { error: e.response?.data?.detail || e.message || 'Pipeline failed' },
        timestamp: new Date().toLocaleTimeString(),
      }]);
    }

    setLoading(false);
    setImage(null);
    setImagePreview(null);
    setCsv(null);
    setPdf(null);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleFeedback = async (result, status) => {
    if (!result?.session_id) return;
    try {
      await submitFeedback({ report_id: result.session_id, diagnosis_correct: status === 'RESOLVED', outcome: status, downtime_hours: 0, equipment_id: equipmentId || '' });
    } catch {}
  };

  const selectedEquip = EQUIPMENT_LIST.find(e => e.id === equipmentId);
  const hasAttachments = image || csv || pdf;

  return (
    <div className="chat-page">
      {/* ═══ Chat Mode Toggle ═══ */}
      <div style={{ display: 'flex', justifyContent: 'center', paddingTop: '20px', paddingBottom: '10px', position: 'relative', zIndex: 10 }}>
        <div style={{ background: '#1e2029', padding: '4px', borderRadius: '50px', display: 'flex', border: '1px solid #2b2d35', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)' }}>
          <button 
            onClick={() => setChatMode('text')}
            style={{ padding: '8px 24px', borderRadius: '50px', fontSize: '14px', fontWeight: 500, transition: 'all 0.3s', background: chatMode === 'text' ? '#3b82f6' : 'transparent', color: chatMode === 'text' ? 'white' : '#9ca3af', border: 'none', cursor: 'pointer' }}
          >
            💬 Text Chat
          </button>
          <button 
            onClick={() => setChatMode('voice')}
            style={{ padding: '8px 24px', borderRadius: '50px', fontSize: '14px', fontWeight: 500, transition: 'all 0.3s', background: chatMode === 'voice' ? '#10b981' : 'transparent', color: chatMode === 'voice' ? 'white' : '#9ca3af', border: 'none', cursor: 'pointer' }}
          >
            🎙️ Voice Agent
          </button>
        </div>
      </div>

      {chatMode === 'voice' ? (
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', position: 'relative', paddingBottom: '100px' }}>
            <div style={{ position: 'relative', display: 'flex', alignItems: 'center', justifyContent: 'center', width: '256px', height: '256px', borderRadius: '50%', transition: 'all 0.5s', background: isRecording ? 'rgba(239, 68, 68, 0.15)' : audioPlaying ? 'rgba(16, 185, 129, 0.15)' : 'transparent', transform: isRecording ? 'scale(1.1)' : audioPlaying ? 'scale(1.05)' : 'scale(1)' }}>
              <button 
                style={{ width: '128px', height: '128px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '48px', transition: 'all 0.3s', zIndex: 10, cursor: 'pointer', border: 'none', background: isRecording ? '#ef4444' : audioPlaying ? '#10b981' : '#2b2d35', color: isRecording || audioPlaying ? 'white' : '#d1d5db', boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.3)' }}
                onClick={handleVoiceToggle}
              >
                {isRecording ? '⏹️' : '🎤'}
              </button>
            </div>
            
            <div style={{ marginTop: '48px', textAlign: 'center' }}>
               <h2 style={{ fontSize: '24px', fontWeight: 600, color: 'white', marginBottom: '8px' }}>
                 {isRecording ? 'Listening...' : loading ? 'Thinking...' : audioPlaying ? 'Speaking...' : 'Tap to speak to OmniSense'}
               </h2>
               <p style={{ color: '#9ca3af', fontSize: '15px' }}>
                 {recordingStatus || 'Conversational intelligence for plant maintenance.'}
               </p>
            </div>
            
            {loading && (
              <div style={{ marginTop: '40px', background: '#1e2029', padding: '16px 24px', borderRadius: '12px', border: '1px solid #2b2d35' }}>
                 <AgentPipelineChat activeAgent={activeAgent} hasImage={!!image} hasCsv={!!csv} />
              </div>
            )}
        </div>
      ) : (
        <>
      {/* Chat Messages Area */}
      <div className="chat-messages-area">
        {messages.length === 0 && !loading ? (
          <div className="chat-welcome">
            <div className="chat-welcome-icon">
              <div className="chat-welcome-icon-inner">🏭</div>
              <div className="chat-welcome-ring"></div>
            </div>
            <h1 className="chat-welcome-title">OmniSense AI Wizard</h1>
            <p className="chat-welcome-sub">Multi-agent diagnostic intelligence for steel plant equipment</p>

            <div className="chat-suggestions">
              {SUGGESTIONS.map((s, i) => (
                <button key={i} className="chat-suggestion-card" onClick={() => { setInputText(s.text); }}>
                  <span className="chat-suggestion-icon">{s.icon}</span>
                  <span className="chat-suggestion-text">{s.text}</span>
                  <span className="chat-suggestion-arrow">→</span>
                </button>
              ))}
            </div>

            <div className="chat-capabilities">
              <div className="chat-cap-item"><span className="chat-cap-icon">🖼️</span> Image Analysis</div>
              <div className="chat-cap-item"><span className="chat-cap-icon">📊</span> Sensor CSV</div>
              <div className="chat-cap-item"><span className="chat-cap-icon">🎤</span> Voice Input</div>
              <div className="chat-cap-item"><span className="chat-cap-icon">🌐</span> Multi-language</div>
              <div className="chat-cap-item"><span className="chat-cap-icon">📋</span> PDF Reports</div>
              <div className="chat-cap-item"><span className="chat-cap-icon">⚡</span> 8 AI Agents</div>
            </div>
          </div>
        ) : (
          <div className="chat-messages-list">
            {messages.map((msg, i) => (
              <div key={i} className={`chat-msg ${msg.role}`}>
                {msg.role === 'user' ? <UserMessage msg={msg} /> : <AssistantMessage msg={msg} onFeedback={handleFeedback} onPlayTTS={playTTS} audioPlaying={audioPlaying} />}
              </div>
            ))}

            {loading && (
              <div className="chat-msg assistant">
                <div className="chat-msg-avatar chat-avatar-ai">🤖</div>
                <div className="chat-msg-body">
                  <AgentPipelineChat activeAgent={activeAgent} hasImage={!!image} hasCsv={!!csv} />
                </div>
              </div>
            )}

            <div ref={chatEndRef} />
          </div>
        )}
      </div>

      {/* Input Bar — Fixed at bottom */}
      <div className="chat-input-section">
        {/* Attachment pills */}
        {(hasAttachments || equipmentId) && (
          <div className="chat-input-attachments">
            {equipmentId && (
              <div className="chat-attach-pill equip-pill">
                ⚙️ {selectedEquip?.name} <span className="chat-attach-plant">({selectedEquip?.plant})</span>
                <button className="chat-attach-x" onClick={() => { setEquipmentId(''); setEquipmentType(''); }}>×</button>
              </div>
            )}
            {image && (
              <div className="chat-attach-pill">
                {imagePreview && <img src={imagePreview} alt="" className="chat-attach-thumb" />}
                📸 {image.name.slice(0, 18)}
                <button className="chat-attach-x" onClick={() => { setImage(null); setImagePreview(null); }}>×</button>
              </div>
            )}
            {csv && (
              <div className="chat-attach-pill">📊 {csv.name.slice(0, 18)} <button className="chat-attach-x" onClick={() => setCsv(null)}>×</button></div>
            )}
            {pdf && (
              <div className="chat-attach-pill">📄 {pdf.name.slice(0, 18)} <button className="chat-attach-x" onClick={() => setPdf(null)}>×</button></div>
            )}
          </div>
        )}

        {recordingStatus && <div className="chat-recording-indicator">{isRecording ? '🔴' : '✅'} {recordingStatus}</div>}

        <div className="chat-input-row">
          {/* Attach menu button */}
          <div className="chat-attach-menu-wrap">
            <button className="chat-input-icon-btn" onClick={() => setShowAttachMenu(!showAttachMenu)} title="Attach files">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21.44 11.05l-9.19 9.19a6 6 0 01-8.49-8.49l9.19-9.19a4 4 0 015.66 5.66l-9.2 9.19a2 2 0 01-2.83-2.83l8.49-8.48"/></svg>
            </button>
            {showAttachMenu && (
              <div className="chat-attach-dropdown">
                <input type="file" ref={imgRef} style={{ display: 'none' }} accept="image/*" onChange={handleImageChange} />
                <button className="chat-attach-opt" onClick={() => { imgRef.current?.click(); }}>📸 Equipment Photo</button>
                <input type="file" ref={csvRef} style={{ display: 'none' }} accept=".csv" onChange={e => { setCsv(e.target.files[0]); setShowAttachMenu(false); }} />
                <button className="chat-attach-opt" onClick={() => { csvRef.current?.click(); }}>📊 Sensor CSV</button>
                <input type="file" ref={pdfRef} style={{ display: 'none' }} accept=".pdf,.txt" onChange={e => { setPdf(e.target.files[0]); setShowAttachMenu(false); }} />
                <button className="chat-attach-opt" onClick={() => { pdfRef.current?.click(); }}>📄 Manual / SOP</button>
              </div>
            )}
          </div>

          {/* Equipment selector */}
          <div className="chat-attach-menu-wrap">
            <button className={`chat-input-icon-btn ${equipmentId ? 'active' : ''}`} onClick={() => setShowEquipSelect(!showEquipSelect)} title="Select equipment">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-2 2 2 2 0 01-2-2v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83 0 2 2 0 010-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 01-2-2 2 2 0 012-2h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 010-2.83 2 2 0 012.83 0l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 012-2 2 2 0 012 2v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 0 2 2 0 010 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 012 2 2 2 0 01-2 2h-.09a1.65 1.65 0 00-1.51 1z"/></svg>
            </button>
            {showEquipSelect && (
              <div className="chat-attach-dropdown equip-dropdown">
                {EQUIPMENT_LIST.filter(e => e.id).map(eq => (
                  <button key={eq.id} className={`chat-attach-opt ${equipmentId === eq.id ? 'active' : ''}`} onClick={() => handleEquipmentSelect(eq.id)}>
                    <span style={{ fontWeight: 600 }}>{eq.id}</span> — {eq.name}
                    <span style={{ fontSize: 10, color: 'var(--text-muted)', marginLeft: 'auto' }}>{eq.plant}</span>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Text input */}
          <div className="chat-input-field-wrap">
            <textarea
              ref={inputRef}
              className="chat-input-field"
              placeholder="Describe the equipment issue, error codes, or symptoms..."
              value={inputText}
              onChange={e => setInputText(e.target.value)}
              onKeyDown={handleKeyDown}
              rows={1}
              disabled={loading}
            />
            {detectedLang !== 'en' && <span className="chat-lang-indicator">{LANG_LABELS[detectedLang]}</span>}
          </div>

          {/* Voice button */}
          <button className={`chat-input-icon-btn voice-btn ${isRecording ? 'recording' : ''}`} onClick={handleVoiceToggle} title="Voice input">
            🎤
          </button>

          {/* Send button */}
          <button className="chat-send-btn" onClick={() => handleSend()} disabled={loading || (!inputText && !image && !csv)} title="Send">
            {loading ? (
              <div className="spinner" style={{ width: 16, height: 16 }}></div>
            ) : (
              <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>
            )}
          </button>
        </div>

        <div className="chat-input-footer">
          <span>OmniSense processes through 8 AI agents · Auto-detects language · Supports image, CSV, voice, and PDF inputs</span>
        </div>
      </div>
      </>
      )}
    </div>
  );
}

/* ═══ User Message Bubble ═══ */
function UserMessage({ msg }) {
  return (
    <>
      <div className="chat-msg-body user-body">
        {msg.equipment && (
          <div className="chat-msg-equip-tag">⚙️ {msg.equipment.id} — {msg.equipment.name}</div>
        )}
        <div className="chat-msg-text">{msg.content}</div>
        {msg.attachments?.length > 0 && (
          <div className="chat-msg-attachments">
            {msg.attachments.map((a, i) => (
              <div key={i} className="chat-msg-attach-chip">
                {a.type === 'image' && a.preview && <img src={a.preview} alt="" className="chat-msg-attach-img" />}
                {a.type === 'csv' && <span>📊</span>}
                {a.type === 'pdf' && <span>📄</span>}
                <span>{a.name}</span>
              </div>
            ))}
          </div>
        )}
        <div className="chat-msg-time">{msg.timestamp}</div>
      </div>
      <div className="chat-msg-avatar chat-avatar-user">👷</div>
    </>
  );
}

/* ═══ Assistant Message Bubble ═══ */
function AssistantMessage({ msg, onFeedback, onPlayTTS, audioPlaying }) {
  const data = msg.content;
  if (data?.error) {
    return (
      <>
        <div className="chat-msg-avatar chat-avatar-ai">🤖</div>
        <div className="chat-msg-body">
          <div className="chat-error-card">
            <div className="chat-error-title">⚠️ Pipeline Error</div>
            <div className="chat-error-detail">{data.error}</div>
          </div>
          <div className="chat-msg-time">{msg.timestamp}</div>
        </div>
      </>
    );
  }

  const diagnosis = data?.diagnosis;
  const riskLevel = data?.risk_level;
  const riskCfg = RISK_CONFIG[riskLevel];
  const anomaly = data?.anomaly_result;
  const vision = data?.vision_output;
  const report = data?.report;

  return (
    <>
      <div className="chat-msg-avatar chat-avatar-ai">🤖</div>
      <div className="chat-msg-body">
        {/* Render casual chat response if no formal diagnosis exists */}
        {!diagnosis && !report && data?.chat_response ? (
          <div className="chat-ai-casual-msg" style={{ padding: '8px 4px', fontSize: '15px', color: '#e5e7eb', lineHeight: '1.6' }}>
            <ReactMarkdown>{data.chat_response}</ReactMarkdown>
            <div className="chat-msg-time" style={{ marginTop: '8px', fontSize: '11px', color: '#6b7280' }}>{msg.timestamp}</div>
          </div>
        ) : (
          <>
            {/* Risk + Session Header */}
        <div className="chat-ai-header">
          <div className="chat-ai-header-left">
            <span style={{ fontWeight: 700, fontSize: 14 }}>Diagnosis Complete</span>
            <span style={{ fontSize: 10, color: 'var(--text-muted)', fontFamily: 'monospace' }}>ID: {data?.session_id?.slice(0, 8)}</span>
          </div>
          <div className="chat-ai-header-right">
            {riskLevel && (
              <span className="chat-risk-badge" style={{ background: riskCfg?.bg, color: riskCfg?.color, borderColor: riskCfg?.color }}>
                ● {riskCfg?.label}
              </span>
            )}
            <button className="chat-listen-btn" onClick={() => onPlayTTS(diagnosis?.fault_identified || '')} disabled={audioPlaying}>
              {audioPlaying ? '🔊 Playing...' : '🔊 Listen'}
            </button>
          </div>
        </div>

        {/* Fault & Root Cause */}
        <div className="chat-ai-section">
          <div className="chat-ai-section-title">🔍 Fault & Root Cause</div>
          <p className="chat-ai-section-text">{diagnosis?.fault_identified || 'No fault identified.'}</p>
          {diagnosis?.root_cause && diagnosis.root_cause !== 'Unknown' && (
            <div className="chat-ai-root-cause"><strong>Root Cause:</strong> {diagnosis.root_cause}</div>
          )}
          {diagnosis?.confidence != null && (
            <div className="chat-ai-confidence">
              <div className="chat-ai-conf-bar">
                <div className="chat-ai-conf-fill" style={{ width: `${diagnosis.confidence * 100}%`, background: diagnosis.confidence > 0.7 ? '#22c55e' : diagnosis.confidence > 0.4 ? '#eab308' : '#ef4444' }} />
              </div>
              <span className="chat-ai-conf-label">{(diagnosis.confidence * 100).toFixed(0)}% confidence</span>
            </div>
          )}
          {vision?.fault_detected && (
            <div className="chat-ai-vision-tag">👁️ Vision: {vision.fault_type} on {vision.affected_component}</div>
          )}
        </div>

        {/* Sensor & RUL */}
        {anomaly && (
          <div className="chat-ai-section">
            <div className="chat-ai-section-title">📡 Sensor Analysis & RUL</div>
            <div className="chat-ai-rul-row">
              <div className="chat-ai-rul-num" style={{ color: anomaly.rul_days < 7 ? '#ef4444' : anomaly.rul_days < 14 ? '#eab308' : '#22c55e' }}>
                {anomaly.rul_days}<span className="chat-ai-rul-unit">days</span>
              </div>
              <div className="chat-ai-rul-text">
                {anomaly.anomaly_detected ? `⚠️ Anomaly detected on ${anomaly.anomalous_sensor || 'sensor'}` : '✅ All sensors within normal range'}
              </div>
            </div>
          </div>
        )}

        {/* Immediate Actions */}
        {diagnosis?.immediate_actions?.length > 0 && (
          <div className="chat-ai-section urgent">
            <div className="chat-ai-section-title">⚡ Immediate Actions</div>
            <ul className="chat-ai-list">
              {diagnosis.immediate_actions.map((a, i) => <li key={i}>{a}</li>)}
            </ul>
          </div>
        )}

        {/* Repair Plan */}
        {diagnosis?.repair_steps?.length > 0 && (
          <div className="chat-ai-section">
            <div className="chat-ai-section-title">🔧 Repair Steps</div>
            <ol className="chat-ai-list ordered">
              {diagnosis.repair_steps.map((s, i) => <li key={i}>{s}</li>)}
            </ol>
          </div>
        )}

        {/* Safety */}
        {diagnosis?.safety_precautions?.length > 0 && (
          <div className="chat-ai-section safety">
            <div className="chat-ai-section-title">🦺 Safety Precautions</div>
            <ul className="chat-ai-list">
              {diagnosis.safety_precautions.map((s, i) => <li key={i}>{s}</li>)}
            </ul>
          </div>
        )}

        {/* Spare Parts */}
        {diagnosis?.spare_parts_needed?.length > 0 && (
          <div className="chat-ai-section">
            <div className="chat-ai-section-title">📦 Spare Parts Required</div>
            <div className="chat-ai-parts-grid">
              {diagnosis.spare_parts_needed.map((p, i) => (
                <div key={i} className="chat-ai-part-chip">
                  <div className="chat-ai-part-name">{p.name}</div>
                  <div className="chat-ai-part-meta">
                    <span>Qty: {p.quantity}</span>
                    <span className="chat-ai-part-num">{p.part_number}</span>
                    <span className={`chat-ai-part-urgency ${p.urgency}`}>{p.urgency}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Report */}
        {report?.full_report_md && (
          <details className="chat-ai-report-details">
            <summary className="chat-ai-report-summary">📋 Full Maintenance Report <span className="chat-ai-report-expand">Click to expand</span></summary>
            <div className="chat-ai-report-body markdown-body">
              <ReactMarkdown>{report.full_report_md}</ReactMarkdown>
            </div>
          </details>
        )}

        {/* Feedback */}
        <div className="chat-ai-feedback">
          <span>Was this helpful?</span>
          <button className="chat-fb-btn resolve" onClick={() => onFeedback(data, 'RESOLVED')}>✓ Resolved</button>
          <button className="chat-fb-btn escalate" onClick={() => onFeedback(data, 'ESCALATED')}>⚠ Escalate</button>
        </div>

        <div className="chat-msg-time">{msg.timestamp}</div>
          </>
        )}
      </div>
    </>
  );
}

/* ═══ Agent Pipeline Loader ═══ */
function AgentPipelineChat({ activeAgent, hasImage, hasCsv }) {
  const visible = AGENTS.filter(a => {
    if (a.id === 'vision' && !hasImage) return false;
    if (a.id === 'anomaly' && !hasCsv) return false;
    return true;
  });
  const activeIdx = activeAgent === 'done' ? 999 : visible.findIndex(a => a.id === activeAgent);

  return (
    <div className="chat-pipeline">
      <div className="chat-pipeline-title">
        <div className="spinner" style={{ width: 14, height: 14 }}></div>
        Processing through agent pipeline...
      </div>
      <div className="chat-pipeline-agents">
        {visible.map((agent, i) => {
          let status = i < activeIdx ? 'done' : i === activeIdx ? 'active' : 'waiting';
          return (
            <div key={agent.id} className={`chat-pipeline-agent ${status}`}>
              <span className="chat-pipeline-dot"></span>
              <span className="chat-pipeline-icon">{agent.icon}</span>
              <span className="chat-pipeline-label">{agent.label}</span>
              {status === 'active' && <span className="chat-pipeline-desc">{agent.desc}...</span>}
              {status === 'done' && <span className="chat-pipeline-check">✓</span>}
            </div>
          );
        })}
      </div>
    </div>
  );
}
