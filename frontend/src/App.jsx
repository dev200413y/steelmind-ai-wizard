import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import LiveDashboard from './components/LiveDashboard';
import AIChatPage from './components/AIChatPage';
import EquipmentPage from './components/EquipmentPage';
import MaintenancePage from './components/MaintenancePage';
import AlertsPage from './components/AlertsPage';
import { getLiveSensors, getLiveAlerts } from './api';
import './index.css';

export default function App() {
  const [activePage, setActivePage] = useState('chat');
  const [sensorData, setSensorData] = useState(null);
  const [alertCounts, setAlertCounts] = useState({ critical: 0, high: 0, medium: 0, total: 0 });
  const [recentAlerts, setRecentAlerts] = useState([]);

  useEffect(() => {
    // Fetch live data every 2 seconds
    const fetchLive = async () => {
      try {
        const sensors = await getLiveSensors();
        setSensorData(sensors);
        setAlertCounts(sensors.alert_counts || { critical: 0, high: 0, medium: 0, total: 0 });
        
        const alerts = await getLiveAlerts();
        setRecentAlerts(alerts.alerts || []);
      } catch (e) {
        console.error("Live feed error:", e);
      }
    };

    fetchLive();
    const iv = setInterval(fetchLive, 2000);
    return () => clearInterval(iv);
  }, []);

  return (
    <div className="app-layout" style={{ display: 'flex', height: '100vh', width: '100vw', overflow: 'hidden', backgroundColor: '#090a0f', color: '#f8fafc', fontFamily: 'Inter, sans-serif' }}>
      <Sidebar activePage={activePage} onNavigate={setActivePage} alertCounts={alertCounts} />
      <div className="main-content" style={{ flex: 1, display: 'flex', flexDirection: 'column', height: '100vh', overflow: 'hidden', position: 'relative' }}>
        {activePage === 'dashboard' && (
          <LiveDashboard 
            sensorData={sensorData} 
            alertCounts={alertCounts} 
            recentAlerts={recentAlerts} 
          />
        )}
        {activePage === 'chat' && <AIChatPage />}
        {activePage === 'equipment' && <EquipmentPage sensorData={sensorData} />}
        {activePage === 'maintenance' && <MaintenancePage />}
        {activePage === 'alerts' && <AlertsPage alerts={recentAlerts} alertCounts={alertCounts} />}
      </div>
    </div>
  );
}
