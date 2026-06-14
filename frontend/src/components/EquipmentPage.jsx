import React from 'react';
import LiveChart from './LiveChart';

const SEVERITY_CONFIG = {
  CRITICAL: { color: '#ef4444', bg: 'rgba(239,68,68,0.12)', icon: '🔴' },
  HIGH:     { color: '#f97316', bg: 'rgba(249,115,22,0.12)', icon: '🟠' },
  MEDIUM:   { color: '#eab308', bg: 'rgba(234,179,8,0.12)',  icon: '🟡' },
  NORMAL:   { color: '#22c55e', bg: 'rgba(34,197,94,0.12)',  icon: '🟢' },
};

export default function EquipmentPage({ sensorData }) {
  const readings = sensorData?.readings || [];

  return (
    <div className="dashboard-content">
      <div className="dash-header">
        <div>
          <h1 className="dash-title">Equipment Fleet</h1>
          <p className="dash-subtitle">Detailed sensor readings and health status for all {readings.length} monitored assets</p>
        </div>
      </div>

      <div className="equip-grid">
        {readings.map(eq => {
          const cfg = SEVERITY_CONFIG[eq.severity] || SEVERITY_CONFIG.NORMAL;
          const sensors = eq.sensors || {};
          
          return (
            <div key={eq.equipment_id} className="equip-card">
              {/* Header */}
              <div className="equip-card-top">
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 4 }}>
                    <span className="equip-card-id">{eq.equipment_id}</span>
                    <span className="severity-badge" style={{ background: cfg.bg, color: cfg.color, border: `1px solid ${cfg.color}30` }}>
                      {cfg.icon} {eq.severity}
                    </span>
                  </div>
                  <div style={{ fontSize: 16, fontWeight: 700 }}>{eq.equipment_name}</div>
                  <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>
                    📍 {eq.plant} · {eq.equipment_type} · Criticality: <span style={{ textTransform: 'uppercase', fontWeight: 600 }}>{eq.criticality}</span>
                  </div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: 28, fontWeight: 800, color: eq.rul_days < 10 ? '#ef4444' : eq.rul_days < 30 ? '#eab308' : '#22c55e' }}>
                    {eq.rul_days}
                  </div>
                  <div style={{ fontSize: 10, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Days RUL</div>
                </div>
              </div>

              {/* Sensor readings grid */}
              <div className="equip-sensor-grid">
                {[
                  { key: 'temperature', label: 'Temperature', unit: '°C', color: '#ef4444' },
                  { key: 'vibration',   label: 'Vibration',   unit: 'mm/s', color: '#8b5cf6' },
                  { key: 'pressure',    label: 'Pressure',    unit: 'bar', color: '#3b82f6' },
                  { key: 'rpm',         label: 'RPM',         unit: 'rpm', color: '#f59e0b' },
                  { key: 'current',     label: 'Current',     unit: 'A', color: '#10b981' },
                ].map(sensor => (
                  <div key={sensor.key} className="equip-sensor-box">
                    <LiveChart
                      data={eq.history?.[sensor.key] || []}
                      color={sensor.color}
                      label={sensor.label}
                      unit={sensor.unit}
                      width={160}
                      height={45}
                    />
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
