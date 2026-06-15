import React from 'react';

const NAV_ITEMS = [
  { id: 'dashboard',   icon: '📊', label: 'Dashboard' },
  { id: 'chat',        icon: '🤖', label: 'AI Chat' },
  { id: 'history',     icon: '🕘', label: 'History' },
  { id: 'analytics',   icon: '📈', label: 'Analytics' },
  { id: 'risk',        icon: '⚠️', label: 'Risk' },
  { id: 'tickets',     icon: '🎫', label: 'Tickets' },
  { id: 'equipment',   icon: '⚙️', label: 'Equipment' },
  { id: 'maintenance', icon: '🔧', label: 'Maintenance' },
  { id: 'alerts',      icon: '🔔', label: 'Alerts' },
];

export default function Sidebar({ activePage, onNavigate, alertCounts }) {
  const criticalCount = (alertCounts?.critical || 0) + (alertCounts?.high || 0);

  return (
    <div className="sidebar">
      {/* Logo */}
      <div className="sidebar-logo" onClick={() => onNavigate('dashboard')}>
        <div className="sidebar-logo-icon">SM</div>
        <div className="sidebar-logo-text">
          <div className="sidebar-logo-title">OmniSense</div>
          <div className="sidebar-logo-sub">AI Wizard</div>
        </div>
      </div>

      {/* Nav Section */}
      <div className="sidebar-section-label">MAIN</div>
      <nav className="sidebar-nav">
        {NAV_ITEMS.map(item => (
          <button
            key={item.id}
            className={`sidebar-nav-item ${activePage === item.id ? 'active' : ''}`}
            onClick={() => onNavigate(item.id)}
          >
            <span className="sidebar-nav-icon">{item.icon}</span>
            <span className="sidebar-nav-label">{item.label}</span>
            {item.id === 'alerts' && criticalCount > 0 && (
              <span className="sidebar-alert-badge">{criticalCount}</span>
            )}
          </button>
        ))}
      </nav>

      {/* Bottom: Status */}
      <div className="sidebar-footer">
        <div className="sidebar-status">
          <span className="sidebar-status-dot"></span>
          <span className="sidebar-status-text">8 Agents Ready</span>
        </div>
        <div className="sidebar-version">Tata Steel AI Hackathon 2026</div>
      </div>
    </div>
  );
}
