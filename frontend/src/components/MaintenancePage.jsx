import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'https://steelmind-ai-wizard-production.up.railway.app';

const SEVERITY_COLORS = {
  CRITICAL: { color: '#ef4444', bg: 'rgba(239,68,68,0.12)' },
  HIGH:     { color: '#f97316', bg: 'rgba(249,115,22,0.12)' },
  MEDIUM:   { color: '#eab308', bg: 'rgba(234,179,8,0.12)' },
  LOW:      { color: '#22c55e', bg: 'rgba(34,197,94,0.12)' },
};

const TYPE_COLORS = {
  'Emergency':        { color: '#ef4444', bg: 'rgba(239,68,68,0.1)', icon: '🚨' },
  'Corrective':       { color: '#f97316', bg: 'rgba(249,115,22,0.1)', icon: '🔧' },
  'Preventive':       { color: '#3b82f6', bg: 'rgba(59,130,246,0.1)', icon: '🛡️' },
  'Planned Shutdown':  { color: '#8b5cf6', bg: 'rgba(139,92,246,0.1)', icon: '📋' },
  'Condition-Based':  { color: '#06b6d4', bg: 'rgba(6,182,212,0.1)', icon: '📡' },
  'Predictive':       { color: '#10b981', bg: 'rgba(16,185,129,0.1)', icon: '🔮' },
};

function daysUntil(dateStr) {
  const d = new Date(dateStr);
  const now = new Date();
  return Math.ceil((d - now) / (1000 * 60 * 60 * 24));
}

function daysAgo(dateStr) {
  const d = new Date(dateStr);
  const now = new Date();
  return Math.floor((now - d) / (1000 * 60 * 60 * 24));
}

export default function MaintenancePage() {
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expandedId, setExpandedId] = useState(null);
  const [filterArea, setFilterArea] = useState('All');

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await axios.get(`${API_BASE}/api/maintenance/records`);
        setRecords(res.data.records || []);
      } catch (e) {
        console.error('Failed to load maintenance records:', e);
      }
      setLoading(false);
    };
    fetchData();
  }, []);

  // Compute summary stats
  const totalTeamSize = records.reduce((s, r) => s + (r.team?.team_size || 0), 0);
  const totalDowntimeYTD = records.reduce((s, r) => s + (r.total_downtime_hrs_ytd || 0), 0);
  const overdueCount = records.filter(r => daysUntil(r.next_maintenance_due) < 0).length;
  const dueSoonCount = records.filter(r => { const d = daysUntil(r.next_maintenance_due); return d >= 0 && d <= 7; }).length;

  const areas = ['All', ...new Set(records.map(r => r.area))];
  const filtered = filterArea === 'All' ? records : records.filter(r => r.area === filterArea);

  if (loading) {
    return (
      <div className="dashboard-content" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
        <div style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
          <div className="spinner" style={{ margin: '0 auto 16px' }}></div>
          Loading maintenance records...
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard-content">
      {/* Header */}
      <div className="dash-header">
        <div>
          <h1 className="dash-title">Maintenance Center</h1>
          <p className="dash-subtitle">Complete maintenance history, team assignments, fault analysis, and downtime tracking</p>
        </div>
      </div>

      {/* Summary KPIs */}
      <div className="kpi-grid">
        <div className="kpi-card" style={{ background: 'rgba(59,130,246,0.1)', borderColor: 'rgba(59,130,246,0.25)' }}>
          <div className="kpi-icon">🔧</div>
          <div className="kpi-value" style={{ color: '#3b82f6' }}>{records.length}</div>
          <div className="kpi-label">Total Equipment</div>
        </div>
        <div className="kpi-card" style={{ background: 'rgba(239,68,68,0.1)', borderColor: 'rgba(239,68,68,0.25)' }}>
          <div className="kpi-icon">⚠️</div>
          <div className="kpi-value" style={{ color: '#ef4444' }}>{overdueCount}</div>
          <div className="kpi-label">Overdue</div>
        </div>
        <div className="kpi-card" style={{ background: 'rgba(234,179,8,0.1)', borderColor: 'rgba(234,179,8,0.25)' }}>
          <div className="kpi-icon">⏰</div>
          <div className="kpi-value" style={{ color: '#eab308' }}>{dueSoonCount}</div>
          <div className="kpi-label">Due This Week</div>
        </div>
        <div className="kpi-card" style={{ background: 'rgba(139,92,246,0.1)', borderColor: 'rgba(139,92,246,0.25)' }}>
          <div className="kpi-icon">👷</div>
          <div className="kpi-value" style={{ color: '#8b5cf6' }}>{totalTeamSize}</div>
          <div className="kpi-label">Total Staff</div>
        </div>
      </div>

      {/* Area Filters */}
      <div className="alert-area-row" style={{ marginBottom: 20 }}>
        {areas.map(area => (
          <button key={area} className={`alert-area-tab ${filterArea === area ? 'active' : ''}`} onClick={() => setFilterArea(area)}>
            {area}
          </button>
        ))}
      </div>

      {/* Equipment Maintenance Cards */}
      <div className="maint-list">
        {filtered.map(rec => {
          const isExpanded = expandedId === rec.equipment_id;
          const daysLeft = daysUntil(rec.next_maintenance_due);
          const lastDays = daysAgo(rec.last_maintenance);
          const statusColor = daysLeft < 0 ? '#ef4444' : daysLeft <= 7 ? '#eab308' : '#22c55e';
          const statusLabel = daysLeft < 0 ? 'OVERDUE' : daysLeft <= 7 ? 'DUE SOON' : 'ON SCHEDULE';
          const mTypeCfg = TYPE_COLORS[rec.maintenance_type] || TYPE_COLORS['Preventive'];

          return (
            <div key={rec.equipment_id} className="maint-card" style={{ borderLeft: `3px solid ${statusColor}` }}>
              {/* Card Header — Always Visible */}
              <div className="maint-card-header" onClick={() => setExpandedId(isExpanded ? null : rec.equipment_id)} style={{ cursor: 'pointer' }}>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 4 }}>
                    <span className="equip-card-id">{rec.equipment_id}</span>
                    <span style={{ fontSize: 15, fontWeight: 700 }}>{rec.equipment_name}</span>
                    <span className="severity-badge" style={{ background: statusColor + '20', color: statusColor, border: `1px solid ${statusColor}40` }}>
                      {statusLabel}
                    </span>
                    <span style={{ fontSize: 11, padding: '2px 8px', borderRadius: 10, background: mTypeCfg.bg, color: mTypeCfg.color }}>
                      {mTypeCfg.icon} {rec.maintenance_type}
                    </span>
                  </div>
                  <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                    📍 {rec.plant} · {rec.equipment_type} · {rec.area} · Commissioned: {rec.commissioned_date} ({rec.age_years} years)
                  </div>
                </div>

                {/* Quick Stats */}
                <div style={{ display: 'flex', gap: 20, alignItems: 'center' }}>
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: 18, fontWeight: 800, color: statusColor }}>{daysLeft < 0 ? Math.abs(daysLeft) : daysLeft}</div>
                    <div style={{ fontSize: 9, color: 'var(--text-muted)', textTransform: 'uppercase' }}>{daysLeft < 0 ? 'Days Overdue' : 'Days Left'}</div>
                  </div>
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: 18, fontWeight: 800, color: 'var(--text-main)' }}>{lastDays}</div>
                    <div style={{ fontSize: 9, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Days Since Last</div>
                  </div>
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: 18, fontWeight: 800, color: '#8b5cf6' }}>{rec.total_maintenance_count}</div>
                    <div style={{ fontSize: 9, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Total Services</div>
                  </div>
                  <div style={{ fontSize: 18, color: 'var(--text-muted)', transition: 'transform 0.2s', transform: isExpanded ? 'rotate(180deg)' : 'rotate(0)' }}>▼</div>
                </div>
              </div>

              {/* Expanded Details */}
              {isExpanded && (
                <div className="maint-expanded" style={{ animation: 'slideUp 0.3s ease-out' }}>
                  {/* Row 1: Maintenance Schedule + Reliability KPIs */}
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 16, marginBottom: 16 }}>
                    <div className="maint-detail-box">
                      <h4>📅 Schedule</h4>
                      <div className="maint-detail-row"><span>Last Maintenance</span><span style={{ fontWeight: 600 }}>{rec.last_maintenance}</span></div>
                      <div className="maint-detail-row"><span>Next Due</span><span style={{ fontWeight: 700, color: statusColor }}>{rec.next_maintenance_due}</span></div>
                      <div className="maint-detail-row"><span>Interval</span><span>Every {rec.maintenance_interval_days} days</span></div>
                      <div className="maint-detail-row"><span>Type</span><span style={{ color: mTypeCfg.color }}>{rec.maintenance_type}</span></div>
                    </div>
                    <div className="maint-detail-box">
                      <h4>📊 Reliability Metrics</h4>
                      <div className="maint-detail-row"><span>MTBF</span><span style={{ fontWeight: 700 }}>{rec.mtbf_days} days</span></div>
                      <div className="maint-detail-row"><span>MTTR</span><span style={{ fontWeight: 700 }}>{rec.mttr_hrs} hrs</span></div>
                      <div className="maint-detail-row"><span>YTD Downtime</span><span style={{ fontWeight: 700, color: rec.total_downtime_hrs_ytd > 100 ? '#ef4444' : '#eab308' }}>{rec.total_downtime_hrs_ytd} hrs</span></div>
                      <div className="maint-detail-row"><span>Machine Age</span><span>{rec.age_years} years</span></div>
                    </div>
                    <div className="maint-detail-box">
                      <h4>👷 Maintenance Team</h4>
                      <div className="maint-detail-row"><span>Manager</span><span style={{ fontWeight: 600 }}>{rec.team?.manager}</span></div>
                      <div className="maint-detail-row"><span>Designation</span><span>{rec.team?.designation}</span></div>
                      <div className="maint-detail-row"><span>Team Size</span><span style={{ fontWeight: 700, color: '#8b5cf6' }}>{rec.team?.team_size} members</span></div>
                      <div className="maint-detail-row"><span>Shift</span><span>{rec.team?.shift_pattern}</span></div>
                      <div className="maint-detail-row"><span>Contact</span><span style={{ fontFamily: 'monospace', fontSize: 11 }}>{rec.team?.contact}</span></div>
                    </div>
                  </div>

                  {/* Row 2: Team Members */}
                  {rec.team?.members?.length > 0 && (
                    <div className="maint-detail-box" style={{ marginBottom: 16 }}>
                      <h4>👥 Team Members</h4>
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: 8 }}>
                        {rec.team.members.map((m, i) => (
                          <div key={i} style={{ padding: '8px 12px', background: 'rgba(255,255,255,0.03)', borderRadius: 8, border: '1px solid rgba(255,255,255,0.06)' }}>
                            <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-main)' }}>{m.name}</div>
                            <div style={{ fontSize: 11, color: 'var(--accent)' }}>{m.role}</div>
                            <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>{m.specialization}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Row 3: Common Faults Table */}
                  {rec.common_faults?.length > 0 && (
                    <div className="maint-detail-box" style={{ marginBottom: 16 }}>
                      <h4>⚠️ Common Faults ({rec.common_faults.length})</h4>
                      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
                        <thead>
                          <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
                            <th style={{ textAlign: 'left', padding: '6px 8px', color: 'var(--text-muted)', fontWeight: 600 }}>Fault</th>
                            <th style={{ textAlign: 'center', padding: '6px 8px', color: 'var(--text-muted)', fontWeight: 600 }}>Count</th>
                            <th style={{ textAlign: 'center', padding: '6px 8px', color: 'var(--text-muted)', fontWeight: 600 }}>Severity</th>
                            <th style={{ textAlign: 'center', padding: '6px 8px', color: 'var(--text-muted)', fontWeight: 600 }}>Avg Downtime</th>
                            <th style={{ textAlign: 'left', padding: '6px 8px', color: 'var(--text-muted)', fontWeight: 600 }}>Impact</th>
                          </tr>
                        </thead>
                        <tbody>
                          {rec.common_faults.map((f, i) => {
                            const sc = SEVERITY_COLORS[f.severity] || SEVERITY_COLORS.MEDIUM;
                            const barW = Math.min(100, (f.frequency / 25) * 100);
                            return (
                              <tr key={i} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                                <td style={{ padding: '8px' }}>{f.fault}</td>
                                <td style={{ padding: '8px', textAlign: 'center', fontWeight: 700, fontFamily: 'monospace' }}>{f.frequency}×</td>
                                <td style={{ padding: '8px', textAlign: 'center' }}>
                                  <span style={{ padding: '2px 8px', borderRadius: 10, fontSize: 10, fontWeight: 700, background: sc.bg, color: sc.color }}>{f.severity}</span>
                                </td>
                                <td style={{ padding: '8px', textAlign: 'center', fontFamily: 'monospace' }}>{f.avg_downtime_hrs}h</td>
                                <td style={{ padding: '8px' }}>
                                  <div style={{ height: 6, background: 'rgba(255,255,255,0.08)', borderRadius: 3, overflow: 'hidden', width: 80 }}>
                                    <div style={{ width: `${barW}%`, height: '100%', background: sc.color, borderRadius: 3 }} />
                                  </div>
                                </td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                  )}

                  {/* Row 4: Downtime History Timeline */}
                  {rec.downtime_history?.length > 0 && (
                    <div className="maint-detail-box">
                      <h4>📉 Downtime History ({rec.total_downtime_hrs_ytd}h YTD)</h4>
                      <div className="maint-timeline">
                        {rec.downtime_history.map((dt, i) => {
                          const tc = TYPE_COLORS[dt.type] || TYPE_COLORS['Corrective'];
                          return (
                            <div key={i} className="maint-timeline-item">
                              <div className="maint-timeline-dot" style={{ background: tc.color }}></div>
                              <div className="maint-timeline-content">
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 2 }}>
                                  <span style={{ fontSize: 12, fontWeight: 600 }}>{dt.date}</span>
                                  <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                                    <span style={{ fontSize: 10, padding: '1px 8px', borderRadius: 10, background: tc.bg, color: tc.color, fontWeight: 600 }}>{tc.icon} {dt.type}</span>
                                    <span style={{ fontSize: 12, fontWeight: 700, color: dt.duration_hrs > 24 ? '#ef4444' : dt.duration_hrs > 8 ? '#eab308' : 'var(--text-muted)', fontFamily: 'monospace' }}>{dt.duration_hrs}h</span>
                                  </div>
                                </div>
                                <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{dt.reason}</div>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
