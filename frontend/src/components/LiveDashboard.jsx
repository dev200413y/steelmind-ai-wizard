import React from 'react';
import LiveChart from './LiveChart';

const SEVERITY_CONFIG = {
  CRITICAL: { color: '#ef4444', bg: 'rgba(239,68,68,0.12)', icon: '🔴', pulse: true },
  HIGH:     { color: '#f97316', bg: 'rgba(249,115,22,0.12)', icon: '🟠', pulse: false },
  MEDIUM:   { color: '#eab308', bg: 'rgba(234,179,8,0.12)',  icon: '🟡', pulse: false },
  NORMAL:   { color: '#22c55e', bg: 'rgba(34,197,94,0.12)',  icon: '🟢', pulse: false },
};

const SeverityBadge = ({ level }) => {
  const cfg = SEVERITY_CONFIG[level] || SEVERITY_CONFIG.NORMAL;
  return (
    <span className={`severity-badge ${cfg.pulse ? 'pulse' : ''}`} style={{ background: cfg.bg, color: cfg.color, border: `1px solid ${cfg.color}30` }}>
      {cfg.icon} {level}
    </span>
  );
};

export default function LiveDashboard({ sensorData, alertCounts, recentAlerts }) {
  const readings = sensorData?.readings || [];
  const counts = alertCounts || { critical: 0, high: 0, medium: 0, total: 0 };
  const alerts = recentAlerts || [];

  // Compute plant-wide stats
  const totalEquipment = readings.length;
  const healthyCount = readings.filter(r => r.severity === 'NORMAL').length;
  const uptimePct = totalEquipment > 0 ? Math.round((healthyCount / totalEquipment) * 100) : 100;

  const kpiCards = [
    { label: 'Critical Alerts', value: counts.critical, color: '#ef4444', bg: 'rgba(239,68,68,0.1)', icon: '🔴' },
    { label: 'High Alerts', value: counts.high, color: '#f97316', bg: 'rgba(249,115,22,0.1)', icon: '🟠' },
    { label: 'Total Equipment', value: totalEquipment, color: '#3b82f6', bg: 'rgba(59,130,246,0.1)', icon: '⚙️' },
    { label: 'Plant Uptime', value: `${uptimePct}%`, color: '#22c55e', bg: 'rgba(34,197,94,0.1)', icon: '📈' },
  ];

  return (
    <div className="dashboard-content">
      {/* Header */}
      <div className="dash-header">
        <div>
          <h1 className="dash-title">Plant Overview</h1>
          <p className="dash-subtitle">Real-time equipment health monitoring across all facilities</p>
        </div>
        <div className="dash-timestamp">
          <span className="live-dot"></span>
          LIVE — {new Date().toLocaleTimeString()}
        </div>
      </div>

      {/* KPI Cards */}
      <div className="kpi-grid">
        {kpiCards.map((kpi, i) => (
          <div key={i} className="kpi-card" style={{ background: kpi.bg, borderColor: `${kpi.color}25` }}>
            <div className="kpi-icon" style={{ fontSize: 24 }}>{kpi.icon}</div>
            <div className="kpi-value" style={{ color: kpi.color }}>{kpi.value}</div>
            <div className="kpi-label">{kpi.label}</div>
          </div>
        ))}
      </div>

      {/* Equipment Fleet Grid + Alert Feed */}
      <div className="dash-grid-main">
        {/* Equipment Cards */}
        <div className="dash-fleet-section">
          <h3 className="dash-section-title">Equipment Fleet Status</h3>
          <div className="fleet-grid">
            {readings.map(eq => {
              const cfg = SEVERITY_CONFIG[eq.severity] || SEVERITY_CONFIG.NORMAL;
              return (
                <div key={eq.equipment_id} className="fleet-card" style={{ borderLeft: `3px solid ${cfg.color}` }}>
                  <div className="fleet-card-header">
                    <div>
                      <div className="fleet-card-id">{eq.equipment_id}</div>
                      <div className="fleet-card-name">{eq.equipment_name}</div>
                      <div className="fleet-card-plant">📍 {eq.plant}</div>
                    </div>
                    <SeverityBadge level={eq.severity} />
                  </div>
                  
                  {/* Sensor mini-charts */}
                  <div className="fleet-sensor-grid">
                    <div className="fleet-sensor">
                      <LiveChart data={eq.history?.temperature || []} color="#ef4444" label="Temp" unit="°C" width={100} height={32} showArea={false} />
                    </div>
                    <div className="fleet-sensor">
                      <LiveChart data={eq.history?.vibration || []} color="#8b5cf6" label="Vib" unit="mm/s" width={100} height={32} showArea={false} />
                    </div>
                  </div>

                  {/* RUL bar */}
                  <div className="fleet-rul">
                    <div className="fleet-rul-label">
                      <span>RUL</span>
                      <span style={{ fontWeight: 700, color: eq.rul_days < 10 ? '#ef4444' : eq.rul_days < 30 ? '#eab308' : '#22c55e' }}>
                        {eq.rul_days}d
                      </span>
                    </div>
                    <div className="fleet-rul-bar">
                      <div className="fleet-rul-fill" style={{
                        width: `${Math.min(100, (eq.rul_days / 90) * 100)}%`,
                        background: eq.rul_days < 10 ? '#ef4444' : eq.rul_days < 30 ? '#eab308' : '#22c55e'
                      }} />
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Recent Alerts Feed */}
        <div className="dash-alerts-section">
          <h3 className="dash-section-title">Recent Alerts</h3>
          <div className="alert-feed">
            {alerts.length === 0 ? (
              <div className="alert-empty">✅ No active alerts. All systems nominal.</div>
            ) : (
              alerts.slice(0, 15).map((alert, i) => {
                const cfg = SEVERITY_CONFIG[alert.severity] || SEVERITY_CONFIG.MEDIUM;
                return (
                  <div key={i} className="alert-feed-item" style={{ borderLeft: `3px solid ${cfg.color}` }}>
                    <div className="alert-feed-header">
                      <span style={{ fontWeight: 700, color: cfg.color, fontSize: 11 }}>{alert.severity}</span>
                      <span className="alert-feed-time">{new Date(alert.timestamp).toLocaleTimeString()}</span>
                    </div>
                    <div className="alert-feed-equip">{alert.equipment_name} ({alert.equipment_id})</div>
                    <div className="alert-feed-msg">{alert.message}</div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
