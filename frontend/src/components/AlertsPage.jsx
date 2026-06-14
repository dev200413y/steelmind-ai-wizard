import React, { useState } from 'react';

const SEVERITY_CONFIG = {
  CRITICAL: { color: '#ef4444', bg: 'rgba(239,68,68,0.12)', icon: '🔴' },
  HIGH:     { color: '#f97316', bg: 'rgba(249,115,22,0.12)', icon: '🟠' },
  MEDIUM:   { color: '#eab308', bg: 'rgba(234,179,8,0.12)',  icon: '🟡' },
  LOW:      { color: '#22c55e', bg: 'rgba(34,197,94,0.12)',  icon: '🟢' },
};

const AREAS = ['All', 'Blast Furnace', 'Rolling Mill', 'Steel Melting Shop', 'Raw Materials', 'Utilities'];

export default function AlertsPage({ alerts, alertCounts }) {
  const [filterSeverity, setFilterSeverity] = useState('All');
  const [filterArea, setFilterArea] = useState('All');

  const counts = alertCounts || { critical: 0, high: 0, medium: 0, total: 0 };
  const allAlerts = alerts || [];

  // Filter
  let filtered = allAlerts;
  if (filterSeverity !== 'All') {
    filtered = filtered.filter(a => a.severity === filterSeverity);
  }
  if (filterArea !== 'All') {
    filtered = filtered.filter(a => a.area === filterArea);
  }

  // Group by area for the area summary
  const areaGroups = {};
  allAlerts.forEach(a => {
    areaGroups[a.area] = (areaGroups[a.area] || 0) + 1;
  });

  return (
    <div className="dashboard-content">
      {/* Header */}
      <div className="dash-header">
        <div>
          <h1 className="dash-title">Anomaly Alerts</h1>
          <p className="dash-subtitle">Real-time anomaly detection and equipment health alerts</p>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="kpi-grid">
        {[
          { label: 'Critical Alerts', value: counts.critical, color: '#ef4444', bg: 'rgba(239,68,68,0.1)', icon: '🔴' },
          { label: 'High Alerts', value: counts.high, color: '#f97316', bg: 'rgba(249,115,22,0.1)', icon: '🟠' },
          { label: 'Medium Alerts', value: counts.medium, color: '#eab308', bg: 'rgba(234,179,8,0.1)', icon: '🟡' },
          { label: 'Total Alerts', value: counts.total, color: '#3b82f6', bg: 'rgba(59,130,246,0.1)', icon: '📋' },
        ].map((kpi, i) => (
          <div key={i} className="kpi-card" style={{ background: kpi.bg, borderColor: `${kpi.color}25` }}>
            <div className="kpi-icon" style={{ fontSize: 24 }}>{kpi.icon}</div>
            <div className="kpi-value" style={{ color: kpi.color }}>{kpi.value}</div>
            <div className="kpi-label">{kpi.label}</div>
          </div>
        ))}
      </div>

      {/* Severity Filter Tabs */}
      <div className="alert-filter-row">
        {['All', 'CRITICAL', 'HIGH', 'MEDIUM'].map(sev => {
          const active = filterSeverity === sev;
          const cfg = SEVERITY_CONFIG[sev] || {};
          return (
            <button
              key={sev}
              className={`alert-filter-tab ${active ? 'active' : ''}`}
              onClick={() => setFilterSeverity(sev)}
              style={active ? { background: cfg.bg || 'var(--accent-glow)', color: cfg.color || 'var(--accent)', borderColor: cfg.color || 'var(--accent)' } : {}}
            >
              {sev === 'All' ? `All (${counts.total})` : `${sev} (${sev === 'CRITICAL' ? counts.critical : sev === 'HIGH' ? counts.high : counts.medium})`}
            </button>
          );
        })}
      </div>

      {/* Alerts by Area */}
      <div className="alert-area-row">
        {AREAS.map(area => {
          const count = area === 'All' ? allAlerts.length : (areaGroups[area] || 0);
          const active = filterArea === area;
          return (
            <button
              key={area}
              className={`alert-area-tab ${active ? 'active' : ''}`}
              onClick={() => setFilterArea(area)}
            >
              {area}: <strong>{count}</strong>
            </button>
          );
        })}
      </div>

      {/* Alert List */}
      <div className="alert-list">
        {filtered.length === 0 ? (
          <div className="alert-empty">✅ No alerts matching filters. All systems nominal.</div>
        ) : (
          filtered.map((alert, i) => {
            const cfg = SEVERITY_CONFIG[alert.severity] || SEVERITY_CONFIG.MEDIUM;
            return (
              <div key={i} className="alert-list-item" style={{ borderLeft: `3px solid ${cfg.color}` }}>
                <div className="alert-list-left">
                  <span className="severity-badge" style={{ background: cfg.bg, color: cfg.color, border: `1px solid ${cfg.color}30` }}>
                    {cfg.icon} {alert.severity}
                  </span>
                  <div className="alert-list-content">
                    <div className="alert-list-title">{alert.equipment_name} ({alert.equipment_id})</div>
                    <div className="alert-list-msg">{alert.message}</div>
                    <div className="alert-list-meta">
                      📍 {alert.plant} · {alert.area} · Sensor: {alert.sensor}
                    </div>
                  </div>
                </div>
                <div className="alert-list-time">{new Date(alert.timestamp).toLocaleTimeString()}</div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
