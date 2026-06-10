import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';

const API = 'http://localhost:8000';

// ═══════════════════════════════════════════════════════════
// Icons (inline SVG to avoid dependency issues)
// ═══════════════════════════════════════════════════════════
const Icon = ({ name, size = 16, color = 'currentColor' }) => {
  const icons = {
    dashboard: <><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></>,
    equipment: <><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></>,
    diagnosis: <><path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z"/><path d="m9 12 2 2 4-4" stroke="#060b14" strokeWidth="2"/></>,
    alerts: <><path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/></>,
    chat: <><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></>,
    reports: <><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></>,
    spare: <><circle cx="12" cy="12" r="3"/><path d="M12 1v4M12 19v4M4.22 4.22l2.83 2.83M16.95 16.95l2.83 2.83M1 12h4M19 12h4M4.22 19.78l2.83-2.83M16.95 7.05l2.83-2.83"/></>,
    knowledge: <><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></>,
    temp: <><path d="M14 14.76V3.5a2.5 2.5 0 0 0-5 0v11.26a4.5 4.5 0 1 0 5 0z"/></>,
    vibration: <><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></>,
    pressure: <><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></>,
    send: <><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></>,
    mic: <><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="23"/></>,
    upload: <><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></>,
    sparkle: <><path d="M12 3l1.5 5.5L19 10l-5.5 1.5L12 17l-1.5-5.5L5 10l5.5-1.5z"/></>,
    x: <><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></>,
    check: <><polyline points="20 6 9 17 4 12"/></>,
    clock: <><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></>,
    target: <><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></>,
    zap: <><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></>,
    refresh: <><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></>,
    file: <><path d="M13 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V9z"/><polyline points="13 2 13 9 20 9"/></>,
    download: <><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></>,
  };
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      {icons[name] || null}
    </svg>
  );
};

// ═══════════════════════════════════════════════════════════
// Mock Equipment Data (from our actual sensor data)
// ═══════════════════════════════════════════════════════════
const EQUIPMENT_DATA = [
  { id: 'BF-001', name: 'Blast Furnace #1 Tuyere System', category: 'IRONMAKING', status: 'critical', temp: 1480, tempLimit: 1300, vibration: 3.8, vibLimit: 2.0, pressure: 235, pressLimit: 200, costPerHr: 18500, rul: 3 },
  { id: 'RM-001', name: 'Hot Strip Mill Roughing Stand Work Roll Bearing #1', category: 'ROLLING MILL', status: 'healthy', temp: 68, tempLimit: 85, vibration: 2.1, vibLimit: 4.5, pressure: 180, pressLimit: 220, costPerHr: 22000, rul: 145 },
  { id: 'CC-001', name: 'Continuous Caster Mould Oscillator #2', category: 'STEELMAKING', status: 'warning', temp: 185, tempLimit: 200, vibration: 6.8, vibLimit: 5, pressure: 210, pressLimit: 220, costPerHr: 14200, rul: 12 },
  { id: 'EAF-001', name: 'Electric Arc Furnace Electrode Assembly', category: 'STEELMAKING', status: 'healthy', temp: 920, tempLimit: 1200, vibration: 1.2, vibLimit: 3.0, pressure: 165, pressLimit: 200, costPerHr: 25000, rul: 210 },
  { id: 'HS-001', name: 'Central Hydraulic Power Unit', category: 'UTILITIES', status: 'healthy', temp: 55, tempLimit: 80, vibration: 0.8, vibLimit: 2.0, pressure: 175, pressLimit: 200, costPerHr: 8500, rul: 90 },
  { id: 'CP-001', name: 'Coke Oven Gas Compressor #3 Main Rotor', category: 'UTILITIES', status: 'healthy', temp: 92, tempLimit: 110, vibration: 1.6, vibLimit: 3, pressure: 14.5, pressLimit: 17, costPerHr: 9500, rul: 180 },
  { id: 'CV-001', name: 'Primary Feed Conveyor Belt System', category: 'MATERIAL HANDLING', status: 'healthy', temp: 45, tempLimit: 70, vibration: 1.1, vibLimit: 3.0, pressure: 0, pressLimit: 0, costPerHr: 5200, rul: 220 },
  { id: 'BF-002', name: 'Blast Furnace #2 Cooling Stave System', category: 'IRONMAKING', status: 'healthy', temp: 1220, tempLimit: 1300, vibration: 1.4, vibLimit: 2.0, pressure: 188, pressLimit: 200, costPerHr: 18500, rul: 95 },
];

const ALERTS = [
  { id: 'ALT-001', equipment: 'BF-001', name: 'Blast Furnace #1 Tuyere System', severity: 'critical', message: 'TUYERE NO-4 HEAD TEMPERATURE EXCEEDS SAFE RUNNING MARGIN. COOLING NOZZLE FLOW DROPPED BENEATH CRITICAL LIMITS (< 350 L/MIN). BLOCKAGE OR PINCH DETECTED.', time: '45 mins', active: true },
  { id: 'ALT-002', equipment: 'CC-001', name: 'Continuous Caster Mould Oscillator #2', severity: 'high', message: 'ECCENTRIC BEARINGS VIBRATION EXCEEDED WARNING THRESHOLD (6.8 mm/s vs 5.0 mm/s limit). REPETITIVE PEAKS IN FFT ANALYSIS SUGGEST BEARING RACE DEFECT.', time: '2 hours', active: true },
  { id: 'ALT-003', equipment: 'RM-001', name: 'Hot Strip Mill Bearing', severity: 'medium', message: 'Grease flow sensor reading intermittent on Channel B. No vibration anomaly yet. Recommend visual inspection.', time: '5 hours', active: true },
  { id: 'ALT-004', equipment: 'BF-002', name: 'Blast Furnace #2', severity: 'low', message: 'Stave cooling water flow marginal on Zone 12. Within 5% of lower limit. Trend stable.', time: '8 hours', active: false },
];

// ═══════════════════════════════════════════════════════════
// Sidebar Component
// ═══════════════════════════════════════════════════════════
function Sidebar({ activePage, setActivePage, alertCount }) {
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: 'dashboard' },
    { id: 'equipment', label: 'Equipment', icon: 'equipment' },
    { id: 'diagnosis', label: 'Diagnosis', icon: 'diagnosis' },
    { id: 'alerts', label: 'Alerts', icon: 'alerts', badge: alertCount },
    { id: 'chat', label: 'AI Chat', icon: 'chat' },
    { id: 'reports', label: 'Reports', icon: 'reports' },
    { id: 'spare', label: 'Spare Parts', icon: 'spare' },
    { id: 'knowledge', label: 'Knowledge', icon: 'knowledge' },
  ];

  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="sidebar-brand-icon">SM</div>
        <div>
          <h1>SteelMind</h1>
          <p>Command Center</p>
        </div>
      </div>
      <nav className="sidebar-nav">
        <div className="nav-section-label">Operations</div>
        {navItems.slice(0, 4).map(item => (
          <div key={item.id} className={`nav-item ${activePage === item.id ? 'active' : ''}`} onClick={() => setActivePage(item.id)}>
            <Icon name={item.icon} size={16} />
            <span>{item.label}</span>
            {item.badge > 0 && <span className="nav-badge">{item.badge}</span>}
          </div>
        ))}
        <div className="nav-section-label" style={{ marginTop: 8 }}>Intelligence</div>
        {navItems.slice(4).map(item => (
          <div key={item.id} className={`nav-item ${activePage === item.id ? 'active' : ''}`} onClick={() => setActivePage(item.id)}>
            <Icon name={item.icon} size={16} />
            <span>{item.label}</span>
          </div>
        ))}
      </nav>
      <div style={{ padding: '12px 16px', borderTop: '1px solid var(--border)', fontSize: 10, color: 'var(--text-muted)' }}>
        SteelMind AI Wizard v1.0<br/>Tata Steel Hackathon 2026
      </div>
    </aside>
  );
}

// ═══════════════════════════════════════════════════════════
// TopBar Component
// ═══════════════════════════════════════════════════════════
function TopBar() {
  const [time, setTime] = useState(new Date());
  useEffect(() => { const t = setInterval(() => setTime(new Date()), 1000); return () => clearInterval(t); }, []);
  return (
    <div className="topbar">
      <div className="topbar-left">
        <span style={{ fontSize: 13, fontWeight: 600 }}>1. PLANT ASSETS TELEMETRY CORE</span>
        <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>Interactive Nodes</span>
      </div>
      <div className="topbar-right">
        <span style={{ fontSize: 11, color: 'var(--text-muted)', fontFamily: "'JetBrains Mono', monospace" }}>
          IST {time.toLocaleTimeString('en-IN', { hour12: false })}
        </span>
        <div className="status-pill operational"><span className="dot"></span>System Operational</div>
        <span style={{ background: 'var(--accent-glow)', border: '1px solid rgba(249,115,22,0.2)', padding: '4px 10px', borderRadius: 20, fontSize: 11, fontWeight: 700, color: 'var(--accent)' }}>
          ⚡ Multi-Agent AI
        </span>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════
// Equipment Card
// ═══════════════════════════════════════════════════════════
function EquipmentCard({ eq, onClick }) {
  const statusClass = eq.status === 'critical' ? 'critical' : eq.status === 'warning' ? 'warning' : '';
  const tempDanger = eq.temp > eq.tempLimit;
  const vibDanger = eq.vibration > eq.vibLimit;
  return (
    <div className={`eq-card ${statusClass}`} onClick={() => onClick(eq)} style={{ cursor: 'pointer' }}>
      <div className="eq-card-header">
        <div>
          <div className="eq-card-category">{eq.category}</div>
          <div className="eq-card-name">{eq.name}</div>
        </div>
        <div className={`eq-status-badge ${eq.status}`}>
          {eq.status === 'critical' ? '⚠' : eq.status === 'warning' ? '△' : '✓'} {eq.status}
        </div>
      </div>
      <div className="eq-sensors">
        <div className={`sensor-box ${tempDanger ? 'danger' : ''}`}>
          <div className="sensor-icon">🌡</div>
          <div className="sensor-label">Temp</div>
          <div className="sensor-value">{eq.temp}°C</div>
          <div className="sensor-limit">Limit: {eq.tempLimit}</div>
        </div>
        <div className={`sensor-box ${vibDanger ? 'danger' : ''}`}>
          <div className="sensor-icon">〰️</div>
          <div className="sensor-label">Vibration</div>
          <div className="sensor-value">{eq.vibration} mm/s</div>
          <div className="sensor-limit">Limit: {eq.vibLimit}</div>
        </div>
        <div className="sensor-box">
          <div className="sensor-icon">⏱</div>
          <div className="sensor-label">Pressure</div>
          <div className="sensor-value">{eq.pressure} bar</div>
          <div className="sensor-limit">Limit: {eq.pressLimit}</div>
        </div>
      </div>
      <div className="eq-card-footer">
        <div className="eq-cost">Delay Penalty: <span>₹{eq.costPerHr.toLocaleString()}/hr</span></div>
        <button className="btn" onClick={(e) => { e.stopPropagation(); }}>
          <Icon name="sparkle" size={12} /> Simulate
        </button>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════
// Dashboard Page
// ═══════════════════════════════════════════════════════════
function DashboardPage({ setActivePage, setSelectedEquipment, setDiagTarget }) {
  const criticals = EQUIPMENT_DATA.filter(e => e.status === 'critical').length;
  const warnings = EQUIPMENT_DATA.filter(e => e.status === 'warning').length;
  const activeAlerts = ALERTS.filter(a => a.active).length;

  return (
    <div style={{ padding: 24 }}>
      {/* Stats Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 24 }}>
        <div className="metric-stat">
          <div className="metric-label">Total Equipment</div>
          <div className="metric-value">{EQUIPMENT_DATA.length}</div>
          <div className="metric-sub">Monitored assets</div>
        </div>
        <div className="metric-stat" style={{ borderColor: 'var(--critical-border)' }}>
          <div className="metric-label">Critical</div>
          <div className="metric-value" style={{ color: 'var(--critical)' }}>{criticals}</div>
          <div className="metric-sub">Immediate action</div>
        </div>
        <div className="metric-stat" style={{ borderColor: 'var(--high-border)' }}>
          <div className="metric-label">Warnings</div>
          <div className="metric-value" style={{ color: 'var(--warning)' }}>{warnings}</div>
          <div className="metric-sub">Needs attention</div>
        </div>
        <div className="metric-stat">
          <div className="metric-label">Active Alerts</div>
          <div className="metric-value" style={{ color: 'var(--accent)' }}>{activeAlerts}</div>
          <div className="metric-sub">Unacknowledged</div>
        </div>
      </div>

      {/* Equipment Grid */}
      <div className="section-title">
        <Icon name="equipment" size={14} /> Plant Assets Telemetry
        <span className="section-count">{EQUIPMENT_DATA.length}</span>
      </div>
      <div className="equipment-grid" style={{ marginBottom: 32 }}>
        {EQUIPMENT_DATA.map(eq => (
          <EquipmentCard key={eq.id} eq={eq} onClick={(e) => {
            setSelectedEquipment(e);
            setDiagTarget(e.id);
            setActivePage('diagnosis');
          }} />
        ))}
      </div>

      {/* Alerts Section */}
      <div className="section-title">
        <Icon name="alerts" size={14} /> Active Alarms Ticker
        <span className="section-count">{activeAlerts}</span>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        {ALERTS.filter(a => a.active).map(alert => (
          <div key={alert.id} className={`alert-card ${alert.severity}-alert`}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
              <span style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-muted)' }}>{alert.id}</span>
              <span style={{ color: 'var(--text-muted)' }}>•</span>
              <span style={{ fontSize: 12, fontWeight: 600 }}>{alert.name}</span>
              <span className={`alert-severity ${alert.severity}`}>{alert.severity}</span>
              {alert.active && <span className="alert-severity active-badge">Active</span>}
            </div>
            <p style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.6, marginBottom: 10 }}>{alert.message}</p>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ fontSize: 11, color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: 4 }}>
                <Icon name="clock" size={12} /> Active for {alert.time}
              </span>
              <div style={{ display: 'flex', gap: 8 }}>
                <button className="ack-btn">Acknowledge</button>
                <button className="resolve-btn">Resolve</button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════
// Diagnosis Page — "Agentic Diagnosis & Planning"
// ═══════════════════════════════════════════════════════════
function DiagnosisPage({ diagTarget, setDiagTarget }) {
  const [notes, setNotes] = useState('');
  const [imageFile, setImageFile] = useState(null);
  const [csvFile, setCsvFile] = useState(null);
  const [isRunning, setIsRunning] = useState(false);
  const [result, setResult] = useState(null);
  const [activeTab, setActiveTab] = useState('interactive');
  const [chatMessages, setChatMessages] = useState([
    { role: 'ai', text: `Maintenance Assistant is Online.\nAsk me anything about ${diagTarget || 'your equipment'}. You can prompt queries like "What is the safety water flow rate for BF-01?" or "Is there a spare SKF roller bearing in stock?"` }
  ]);
  const [chatInput, setChatInput] = useState('');
  const fileRef = useRef(null);
  const csvRef = useRef(null);

  const launchDiagnosis = async () => {
    setIsRunning(true);
    setResult(null);
    try {
      const formData = new FormData();
      formData.append('query', notes || `Diagnose equipment ${diagTarget}`);
      if (diagTarget) formData.append('equipment_id', diagTarget);
      if (imageFile) formData.append('image', imageFile);
      if (csvFile) formData.append('csv_file', csvFile);
      const res = await axios.post(`${API}/diagnose`, formData, { headers: { 'Content-Type': 'multipart/form-data' } });
      setResult(res.data);
    } catch (e) {
      setResult({ error: e.message || 'Failed to connect to backend.' });
    }
    setIsRunning(false);
  };

  const sendChat = async () => {
    if (!chatInput.trim()) return;
    setChatMessages(prev => [...prev, { role: 'user', text: chatInput }]);
    const q = chatInput;
    setChatInput('');
    try {
      const formData = new FormData();
      formData.append('query', q);
      if (diagTarget) formData.append('equipment_id', diagTarget);
      const res = await axios.post(`${API}/diagnose`, formData);
      const answer = res.data?.report?.summary || res.data?.diagnosis?.fault_identified || 'Analysis complete.';
      setChatMessages(prev => [...prev, { role: 'ai', text: answer }]);
    } catch (e) {
      setChatMessages(prev => [...prev, { role: 'ai', text: 'Error: ' + (e.message || 'Could not reach backend.') }]);
    }
  };

  return (
    <div style={{ padding: 24, display: 'grid', gridTemplateColumns: '1fr 380px', gap: 20, height: 'calc(100vh - 52px)', overflow: 'hidden' }}>
      {/* Left: Diagnosis Panel */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 20, overflowY: 'auto', paddingRight: 8 }}>
        <div className="diag-panel">
          <div className="diag-panel-header">
            <div style={{ width: 36, height: 36, borderRadius: 10, background: 'var(--accent-glow)', display: 'flex', alignItems: 'center', justifyContent: 'center', border: '1px solid rgba(249,115,22,0.2)' }}>
              <Icon name="target" size={18} color="var(--accent)" />
            </div>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 15, fontWeight: 700 }}>Agentic Diagnosis & Planning</div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Traceable SOP Analysis & Failure Predictions</div>
            </div>
            <div style={{ padding: '4px 10px', background: 'rgba(6,182,212,0.1)', border: '1px solid rgba(6,182,212,0.2)', borderRadius: 6, fontSize: 11, fontWeight: 700, color: 'var(--accent-secondary)' }}>
              Target: {diagTarget || 'None'}
            </div>
          </div>
          <div className="diag-panel-body">
            {/* Equipment Selector */}
            <div style={{ marginBottom: 16 }}>
              <label style={{ display: 'block', fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 8 }}>Target Equipment</label>
              <select value={diagTarget} onChange={(e) => setDiagTarget(e.target.value)} style={{ width: '100%', background: 'rgba(255,255,255,0.04)', border: '1px solid var(--border)', borderRadius: 8, padding: '10px 14px', color: 'var(--text-primary)', fontSize: 13, outline: 'none' }}>
                <option value="">Select equipment...</option>
                {EQUIPMENT_DATA.map(eq => (
                  <option key={eq.id} value={eq.id}>{eq.id} — {eq.name}</option>
                ))}
              </select>
            </div>

            {/* Notes */}
            <div style={{ marginBottom: 16 }}>
              <label style={{ display: 'block', fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 8 }}>Additional Operator Sightings / Notes (Optional)</label>
              <textarea value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="e.g. Heard high-pitched grinding noises from bearing housing; cooling nozzle hose replaced during shift turn-over. Input physical logs here..." style={{ width: '100%', background: 'rgba(255,255,255,0.04)', border: '1px solid var(--border)', borderRadius: 8, padding: '12px 14px', color: 'var(--text-primary)', fontSize: 13, outline: 'none', resize: 'vertical', minHeight: 100, fontFamily: 'Inter, sans-serif', lineHeight: 1.6 }} />
            </div>

            {/* File uploads */}
            <div style={{ display: 'flex', gap: 10, marginBottom: 20 }}>
              <input type="file" ref={fileRef} className="hidden" accept="image/*" onChange={(e) => setImageFile(e.target.files[0])} style={{ display: 'none' }} />
              <input type="file" ref={csvRef} className="hidden" accept=".csv" onChange={(e) => setCsvFile(e.target.files[0])} style={{ display: 'none' }} />
              <button className="btn" onClick={() => fileRef.current?.click()}>
                <Icon name="upload" size={13} /> {imageFile ? imageFile.name : 'Upload Image'}
              </button>
              <button className="btn" onClick={() => csvRef.current?.click()}>
                <Icon name="file" size={13} /> {csvFile ? csvFile.name : 'Upload CSV'}
              </button>
            </div>

            {/* Launch Button */}
            <button className="launch-btn" onClick={launchDiagnosis} disabled={isRunning || !diagTarget}>
              <Icon name="sparkle" size={18} color="white" />
              {isRunning ? 'Running Multi-Agent Pipeline...' : 'Launch Diagnostics Reasoning Pipeline'}
            </button>
          </div>
        </div>

        {/* Results */}
        <AnimatePresence>
          {result && !result.error && (
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="diag-panel">
              <div className="diag-panel-header" style={{ background: result.risk_level === 'CRITICAL' ? 'var(--critical-bg)' : result.risk_level === 'HIGH' ? 'var(--high-bg)' : 'transparent' }}>
                <Icon name="diagnosis" size={20} color={result.risk_level === 'CRITICAL' ? 'var(--critical)' : 'var(--healthy)'} />
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 14, fontWeight: 700 }}>Diagnosis Result</div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Session: {result.session_id}</div>
                </div>
                <div className={`eq-status-badge ${result.risk_level === 'CRITICAL' ? 'critical' : result.risk_level === 'HIGH' ? 'warning' : 'healthy'}`}>
                  {result.risk_level || 'N/A'}
                </div>
              </div>
              <div className="diag-panel-body">
                {result.report?.summary && (
                  <pre style={{ whiteSpace: 'pre-wrap', fontFamily: 'Inter, sans-serif', fontSize: 13, lineHeight: 1.7, color: 'var(--text-secondary)', marginBottom: 16 }}>
                    {result.report.summary}
                  </pre>
                )}
                {result.diagnosis?.repair_steps && (
                  <div>
                    <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-muted)', marginBottom: 8 }}>REPAIR STEPS</div>
                    <ol style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.8, paddingLeft: 20 }}>
                      {result.diagnosis.repair_steps.map((s, i) => <li key={i}>{s}</li>)}
                    </ol>
                  </div>
                )}
              </div>
            </motion.div>
          )}
          {result?.error && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="diag-panel" style={{ borderColor: 'var(--critical-border)' }}>
              <div className="diag-panel-body" style={{ color: 'var(--critical)', fontSize: 13 }}>
                ❌ Pipeline Error: {result.error}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Right: Interactive Chat + RAG */}
      <div className="chat-container" style={{ height: 'calc(100vh - 76px)' }}>
        <div className="tab-bar">
          {['interactive', 'rag', 'logbook'].map(tab => (
            <div key={tab} className={`tab-item ${activeTab === tab ? 'active' : ''}`} onClick={() => setActiveTab(tab)}>
              {tab === 'interactive' ? '💬 Interactive Chat' : tab === 'rag' ? '📚 RAG KB' : '📋 Logbook'}
            </div>
          ))}
        </div>
        <div className="chat-header" style={{ borderBottom: '1px solid var(--border)', padding: '12px 20px' }}>
          <div style={{ width: 32, height: 32, borderRadius: 8, background: 'var(--accent-glow)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Icon name="sparkle" size={16} color="var(--accent)" />
          </div>
          <div>
            <div style={{ fontSize: 13, fontWeight: 700 }}>Interactive Troubleshooter</div>
            <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Context Bound: {diagTarget || 'Global'}</div>
          </div>
        </div>
        <div className="chat-messages" style={{ flex: 1, overflowY: 'auto' }}>
          {chatMessages.map((msg, i) => (
            <div key={i} className={`chat-msg ${msg.role}`}>
              <div className="chat-msg-bubble">
                <pre style={{ whiteSpace: 'pre-wrap', fontFamily: 'Inter, sans-serif', fontSize: 13, lineHeight: 1.6 }}>{msg.text}</pre>
              </div>
            </div>
          ))}
        </div>
        <div className="chat-input-area">
          <input value={chatInput} onChange={(e) => setChatInput(e.target.value)} onKeyDown={(e) => { if (e.key === 'Enter') sendChat(); }} className="chat-input" placeholder={`Troubleshoot ${diagTarget || 'equipment'}...`} />
          <button onClick={sendChat} style={{ background: 'var(--accent)', border: 'none', borderRadius: 8, padding: '8px 10px', cursor: 'pointer', display: 'flex', alignItems: 'center' }}>
            <Icon name="send" size={16} color="white" />
          </button>
        </div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════
// Alerts Page
// ═══════════════════════════════════════════════════════════
function AlertsPage() {
  const [filter, setFilter] = useState('active');
  const [sevFilter, setSevFilter] = useState('all');
  const total = ALERTS.length;
  const activeCount = ALERTS.filter(a => a.active).length;
  const critCount = ALERTS.filter(a => a.severity === 'critical').length;
  const highCount = ALERTS.filter(a => a.severity === 'high').length;
  
  const filtered = ALERTS.filter(a => {
    if (filter === 'active' && !a.active) return false;
    if (filter === 'resolved' && a.active) return false;
    if (sevFilter !== 'all' && a.severity !== sevFilter) return false;
    return true;
  });

  return (
    <div style={{ padding: 24 }}>
      <div style={{ fontSize: 18, fontWeight: 700, marginBottom: 4 }}>Alert Management</div>
      <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 24 }}>Monitor and manage equipment abnormality alerts</div>

      {/* Stats */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 24 }}>
        {[
          { label: 'Total Alerts', val: total, color: 'var(--text-primary)' },
          { label: 'Active', val: activeCount, color: 'var(--accent)' },
          { label: 'Critical', val: critCount, color: 'var(--critical)' },
          { label: 'High', val: highCount, color: 'var(--high)' },
        ].map((s, i) => (
          <div key={i} className="metric-stat" style={{ textAlign: 'center' }}>
            <div className="metric-value" style={{ color: s.color }}>{s.val}</div>
            <div className="metric-sub">{s.label}</div>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div className="filter-bar">
        {['all', 'active', 'acknowledged', 'resolved'].map(f => (
          <button key={f} className={`filter-pill ${filter === f ? 'active' : ''}`} onClick={() => setFilter(f)}>{f}</button>
        ))}
        <span style={{ width: 1, height: 20, background: 'var(--border)', margin: '0 4px' }} />
        {['all', 'critical', 'high', 'medium', 'low'].map(f => (
          <button key={f} className={`filter-pill ${sevFilter === f ? 'active' : ''}`} onClick={() => setSevFilter(f)}>{f}</button>
        ))}
        <span style={{ marginLeft: 'auto', fontSize: 11, color: 'var(--text-muted)' }}>{filtered.length} alerts</span>
      </div>

      {/* Alert List */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        {filtered.map(alert => (
          <div key={alert.id} className={`alert-card ${alert.severity}-alert`}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
              <span style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-muted)' }}>{alert.id}</span>•
              <span style={{ fontSize: 12, fontWeight: 600 }}>{alert.name}</span>
              <span className={`alert-severity ${alert.severity}`}>{alert.severity}</span>
              {alert.active && <span className="alert-severity active-badge">Active</span>}
            </div>
            <p style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.6, marginBottom: 10 }}>{alert.message}</p>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ fontSize: 11, color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: 4 }}>
                <Icon name="clock" size={12} /> Active for {alert.time}
              </span>
              <div style={{ display: 'flex', gap: 8 }}>
                <button className="ack-btn">Acknowledge</button>
                <button className="resolve-btn">Resolve</button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════
// AI Chat Page (full-width)
// ═══════════════════════════════════════════════════════════
function AIChatPage() {
  const [messages, setMessages] = useState([
    { role: 'ai', text: "Namaste! I am SteelMind AI Wizard — your multi-agent diagnostic assistant.\n\n🔧 I can analyze equipment images, sensor CSVs, and maintenance queries.\n📚 I search through SOPs, manuals, and historical failure cases.\n⚡ My pipeline includes Vision AI, RAG, Anomaly Detection, and Risk Scoring.\n\nHow can I help you today?" }
  ]);
  const [input, setInput] = useState('');
  const [imageFile, setImageFile] = useState(null);
  const [csvFile, setCsvFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const fileRef = useRef(null);
  const endRef = useRef(null);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages, loading]);

  const send = async () => {
    if (!input.trim() && !imageFile && !csvFile) return;
    setMessages(prev => [...prev, { role: 'user', text: input || 'Uploaded files for analysis.', image: imageFile?.name, csv: csvFile?.name }]);
    setLoading(true);
    const q = input; setInput('');
    try {
      const fd = new FormData();
      fd.append('query', q || 'Analyze provided files.');
      if (imageFile) fd.append('image', imageFile);
      if (csvFile) fd.append('csv_file', csvFile);
      const res = await axios.post(`${API}/diagnose`, fd, { headers: { 'Content-Type': 'multipart/form-data' } });
      const d = res.data;
      const text = d.report?.summary || d.diagnosis?.fault_identified || 'Analysis complete.';
      setMessages(prev => [...prev, { role: 'ai', text, riskLevel: d.risk_level, hasReport: !!d.report }]);
    } catch (e) {
      setMessages(prev => [...prev, { role: 'ai', text: '❌ Error: ' + (e.message || 'Could not reach backend.') }]);
    }
    setImageFile(null); setCsvFile(null); setLoading(false);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 52px)' }}>
      <div style={{ flex: 1, overflowY: 'auto', padding: '24px 32px' }}>
        {messages.map((m, i) => (
          <div key={i} className={`chat-msg ${m.role}`} style={{ marginBottom: 16 }}>
            <div className="chat-msg-bubble" style={{ maxWidth: 600 }}>
              <pre style={{ whiteSpace: 'pre-wrap', fontFamily: 'Inter, sans-serif', fontSize: 13, lineHeight: 1.7 }}>{m.text}</pre>
              {m.riskLevel && (
                <div style={{ marginTop: 10, display: 'flex', gap: 8 }}>
                  <span className={`eq-status-badge ${m.riskLevel === 'CRITICAL' ? 'critical' : m.riskLevel === 'HIGH' ? 'warning' : 'healthy'}`}>{m.riskLevel}</span>
                </div>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className="chat-msg ai" style={{ marginBottom: 16 }}>
            <div className="chat-msg-bubble" style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              <div style={{ display: 'flex', gap: 4 }}>
                {[0, 1, 2].map(i => <div key={i} style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--accent)', animation: `pulse-dot 1.2s ${i * 0.2}s infinite` }} />)}
              </div>
              <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>Multi-Agent Pipeline running...</span>
            </div>
          </div>
        )}
        <div ref={endRef} />
      </div>
      <div style={{ padding: '16px 32px', borderTop: '1px solid var(--border)', display: 'flex', gap: 10, alignItems: 'center' }}>
        <input type="file" ref={fileRef} style={{ display: 'none' }} accept="image/*,.csv" onChange={(e) => {
          const f = e.target.files[0]; if (!f) return;
          if (f.type.startsWith('image/')) setImageFile(f);
          else setCsvFile(f);
          e.target.value = null;
        }} />
        <button className="btn" onClick={() => fileRef.current?.click()}>
          <Icon name="upload" size={14} /> Attach
        </button>
        {(imageFile || csvFile) && (
          <div style={{ display: 'flex', gap: 6 }}>
            {imageFile && <span style={{ fontSize: 11, background: 'var(--accent-glow)', border: '1px solid rgba(249,115,22,0.2)', padding: '3px 8px', borderRadius: 6, color: 'var(--accent)' }}>📷 {imageFile.name}</span>}
            {csvFile && <span style={{ fontSize: 11, background: 'var(--accent-glow)', border: '1px solid rgba(249,115,22,0.2)', padding: '3px 8px', borderRadius: 6, color: 'var(--accent)' }}>📊 {csvFile.name}</span>}
          </div>
        )}
        <input value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={(e) => { if (e.key === 'Enter') send(); }} className="chat-input" style={{ flex: 1 }} placeholder="Ask SteelMind anything about your equipment..." />
        <button onClick={send} disabled={loading} style={{ background: 'var(--accent)', border: 'none', borderRadius: 10, padding: '10px 14px', cursor: 'pointer', display: 'flex', alignItems: 'center', opacity: loading ? 0.5 : 1 }}>
          <Icon name="send" size={18} color="white" />
        </button>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════
// Main App
// ═══════════════════════════════════════════════════════════
function App() {
  const [activePage, setActivePage] = useState('dashboard');
  const [selectedEquipment, setSelectedEquipment] = useState(null);
  const [diagTarget, setDiagTarget] = useState('BF-001');
  const activeAlerts = ALERTS.filter(a => a.active).length;

  const renderPage = () => {
    switch (activePage) {
      case 'dashboard': return <DashboardPage setActivePage={setActivePage} setSelectedEquipment={setSelectedEquipment} setDiagTarget={setDiagTarget} />;
      case 'diagnosis': return <DiagnosisPage diagTarget={diagTarget} setDiagTarget={setDiagTarget} />;
      case 'alerts': return <AlertsPage />;
      case 'chat': return <AIChatPage />;
      default: return (
        <div style={{ padding: 24, textAlign: 'center', color: 'var(--text-muted)', paddingTop: 100 }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>🚧</div>
          <div style={{ fontSize: 18, fontWeight: 700, marginBottom: 8, color: 'var(--text-primary)' }}>{activePage.charAt(0).toUpperCase() + activePage.slice(1)}</div>
          <div>This module is under development.</div>
        </div>
      );
    }
  };

  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      <Sidebar activePage={activePage} setActivePage={setActivePage} alertCount={activeAlerts} />
      <div className="main-content">
        <TopBar />
        {renderPage()}
      </div>
    </div>
  );
}

export default App;
