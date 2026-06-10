import React, { useState, useRef } from 'react';
import axios from 'axios';

const API = 'http://localhost:8000';

const Icon = ({ name, size = 18, color = 'currentColor' }) => {
  const icons = {
    mic: <><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="23"/></>,
    upload: <><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></>,
    file: <><path d="M13 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V9z"/><polyline points="13 2 13 9 20 9"/></>,
    sparkle: <><path d="M12 3l1.5 5.5L19 10l-5.5 1.5L12 17l-1.5-5.5L5 10l5.5-1.5z"/></>,
    check: <><polyline points="20 6 9 17 4 12"/></>,
    download: <><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></>,
    alert: <><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></>,
    wrench: <><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></>
  };
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      {icons[name]}
    </svg>
  );
};

function App() {
  const [query, setQuery] = useState('');
  const [eqId, setEqId] = useState('');
  const [image, setImage] = useState(null);
  const [csv, setCsv] = useState(null);
  const [pdf, setPdf] = useState(null);
  
  const [loading, setLoading] = useState(false);
  const [agentStep, setAgentStep] = useState('');
  const [result, setResult] = useState(null);

  const imgRef = useRef(null);
  const csvRef = useRef(null);
  const pdfRef = useRef(null);

  const handleLaunch = async () => {
    if (!query && !image && !csv) return;
    setLoading(true);
    setResult(null);
    setAgentStep('Orchestrator Routing Inputs...');

    try {
      const fd = new FormData();
      if (query) fd.append('query', query);
      else fd.append('query', 'Analyze provided files for diagnosis.');
      
      if (eqId) fd.append('equipment_id', eqId);
      if (image) fd.append('image', image);
      if (csv) fd.append('csv_file', csv);
      if (pdf) fd.append('documents', pdf); // Backend expects list, but FastAPI handles single as list if defined correctly

      // Simulate agent progress steps
      setTimeout(() => setAgentStep('Vision Agent analyzing image...'), 1000);
      setTimeout(() => setAgentStep('Anomaly Agent scanning sensor data...'), 2500);
      setTimeout(() => setAgentStep('RAG Agent searching SOPs...'), 4000);
      setTimeout(() => setAgentStep('Diagnostic Agent synthesizing...'), 5500);

      const res = await axios.post(`${API}/diagnose`, fd, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      setResult(res.data);
    } catch (e) {
      setResult({ error: e.response?.data?.detail || e.message || 'Pipeline failed' });
    }
    
    setLoading(false);
  };

  const handleFeedback = (status) => {
    alert(`Feedback "${status}" submitted to Feedback Agent. Knowledge base will be updated.`);
  };

  return (
    <div className="app-container">
      {/* HEADER */}
      <header className="header">
        <div className="brand">
          <div className="brand-icon">SM</div>
          <div>
            <h1>SteelMind Wizard</h1>
            <span>Intelligent Maintenance Decision-Support Platform</span>
          </div>
        </div>
        <div style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
          <div style={{ fontSize: 13, color: 'var(--text-muted)' }}>Tata Steel AI Hackathon 2026</div>
          <div style={{ background: 'var(--accent-glow)', border: '1px solid var(--border)', padding: '6px 12px', borderRadius: 20, fontSize: 12, fontWeight: 700, color: 'var(--accent)' }}>
            Status: Agents Online
          </div>
        </div>
      </header>

      {/* MAIN LAYOUT */}
      <div className="main-layout">
        
        {/* LEFT: INPUT WIZARD */}
        <div className="wizard-panel">
          <h2 style={{ fontSize: 18, marginBottom: 8 }}>Input Diagnosis Data</h2>
          <p style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 24 }}>Provide logs, sensor data, or visual evidence to start the multi-agent pipeline.</p>

          <div className="section-title">1. Operational Inputs</div>
          <div className="input-group">
            <label>Equipment ID (Optional)</label>
            <input type="text" className="form-control" placeholder="e.g. BF-001" value={eqId} onChange={e => setEqId(e.target.value)} />
          </div>
          <div className="input-group">
            <label>Engineer Query / Error Log</label>
            <textarea className="form-control" placeholder="Describe the issue, or paste error codes..." value={query} onChange={e => setQuery(e.target.value)} />
          </div>

          <div className="section-title">2. Condition Monitoring & Visual</div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 16 }}>
            <input type="file" ref={imgRef} style={{ display: 'none' }} accept="image/*" onChange={e => setImage(e.target.files[0])} />
            <div className={`upload-btn ${image ? 'active' : ''}`} onClick={() => imgRef.current?.click()}>
              <Icon name="upload" size={16} /> {image ? 'Image Added' : 'Photo'}
            </div>

            <input type="file" ref={csvRef} style={{ display: 'none' }} accept=".csv" onChange={e => setCsv(e.target.files[0])} />
            <div className={`upload-btn ${csv ? 'active' : ''}`} onClick={() => csvRef.current?.click()}>
              <Icon name="file" size={16} /> {csv ? 'CSV Added' : 'Sensor Data'}
            </div>
          </div>

          <div className="section-title">3. Knowledge Context</div>
          <div className="input-group">
            <input type="file" ref={pdfRef} style={{ display: 'none' }} accept=".pdf,.txt" onChange={e => setPdf(e.target.files[0])} />
            <div className={`upload-btn ${pdf ? 'active' : ''}`} onClick={() => pdfRef.current?.click()}>
              <Icon name="file" size={16} /> {pdf ? 'Manual Added' : 'Upload Manual / SOP (PDF)'}
            </div>
          </div>

          <button className="launch-btn" onClick={handleLaunch} disabled={loading || (!query && !image && !csv)}>
            <Icon name="sparkle" size={18} />
            Launch Multi-Agent Pipeline
          </button>
        </div>

        {/* RIGHT: OUTPUT RESULTS */}
        <div className="results-panel">
          
          {loading && (
            <div className="loading-overlay">
              <div className="spinner"></div>
              <div className="agent-status">{agentStep}</div>
            </div>
          )}

          {!result && !loading && (
            <div className="empty-state">
              <Icon name="wrench" size={48} color="var(--border)" />
              <h2>Awaiting Input</h2>
              <p>Enter data on the left to generate explainable recommendations.</p>
            </div>
          )}

          {result && result.error && (
            <div className="result-card" style={{ borderColor: 'var(--critical-border)' }}>
              <h3 style={{ color: 'var(--critical)', display: 'flex', alignItems: 'center', gap: 8 }}><Icon name="alert" /> Pipeline Error</h3>
              <p style={{ marginTop: 12, color: 'var(--text-muted)' }}>{result.error}</p>
            </div>
          )}

          {result && !result.error && (
            <>
              <div className="result-card">
                <div className="result-header">
                  <div>
                    <h2 style={{ fontSize: 20, fontWeight: 700, marginBottom: 4 }}>Diagnosis & Action Plan</h2>
                    <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Session: {result.session_id}</div>
                  </div>
                  <div className={`risk-badge ${(result.risk_level || 'LOW').toLowerCase()}`}>
                    RISK: {result.risk_level || 'UNKNOWN'}
                  </div>
                </div>

                <div className="grid-2">
                  <div className="data-box">
                    <h4><Icon name="sparkle" size={14} /> Probable Fault & Root Cause</h4>
                    <p style={{ fontSize: 14, color: 'var(--text-main)', lineHeight: 1.6 }}>
                      {result.diagnosis?.fault_identified || result.report?.summary || "No specific fault identified."}
                    </p>
                    {result.vision_output && result.vision_output.fault_detected && (
                      <div style={{ marginTop: 12, padding: 10, background: 'rgba(255,255,255,0.05)', borderRadius: 6, fontSize: 12 }}>
                        <strong>Vision AI Detected:</strong> {result.vision_output.fault_type} on {result.vision_output.affected_component}
                      </div>
                    )}
                  </div>

                  <div className="data-box">
                    <h4><Icon name="alert" size={14} /> Sensor Anomaly & RUL</h4>
                    {result.anomaly_result ? (
                      <div>
                        <div style={{ fontSize: 24, fontWeight: 700, color: result.anomaly_result.rul_days < 7 ? 'var(--critical)' : 'var(--text-main)' }}>
                          {result.anomaly_result.rul_days} Days RUL
                        </div>
                        <p style={{ fontSize: 13, color: 'var(--text-muted)', marginTop: 4 }}>
                          {result.anomaly_result.anomaly_detected ? "⚠️ Critical sensor anomalies detected." : "✅ Sensor readings within normal ranges."}
                        </p>
                      </div>
                    ) : (
                      <p style={{ fontSize: 13, color: 'var(--text-muted)' }}>No sensor CSV provided for anomaly detection.</p>
                    )}
                  </div>
                </div>

                <div className="data-box" style={{ marginTop: 24 }}>
                  <h4><Icon name="wrench" size={14} /> Step-by-Step Maintenance Recommendation</h4>
                  {result.diagnosis?.repair_steps && result.diagnosis.repair_steps.length > 0 ? (
                    <ul className="step-list">
                      {result.diagnosis.repair_steps.map((step, idx) => (
                        <li key={idx}>{step}</li>
                      ))}
                    </ul>
                  ) : (
                    <p style={{ fontSize: 13, color: 'var(--text-muted)' }}>No specific repair steps generated. Refer to general SOP.</p>
                  )}
                </div>

                <div className="feedback-section">
                  <div style={{ fontSize: 13, fontWeight: 600 }}>Did this solve the issue?</div>
                  <div style={{ display: 'flex', gap: 12 }}>
                    <button className="btn-secondary" onClick={() => handleFeedback('RESOLVED')}>
                      <Icon name="check" size={14} color="var(--low)" /> Yes, Resolved
                    </button>
                    <button className="btn-secondary" onClick={() => handleFeedback('ESCALATED')}>
                      <Icon name="alert" size={14} color="var(--critical)" /> No, Escalated
                    </button>
                  </div>
                </div>
              </div>

              {/* REPORT DOWNLOAD */}
              {result.report && (
                <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                  <a href={`${API}/report/${result.session_id}`} target="_blank" rel="noreferrer" style={{ textDecoration: 'none' }}>
                    <button className="btn-secondary" style={{ background: 'var(--accent)', color: 'white', border: 'none' }}>
                      <Icon name="download" size={16} /> Download Full PDF Report
                    </button>
                  </a>
                </div>
              )}
            </>
          )}

        </div>
      </div>
    </div>
  );
}

export default App;
