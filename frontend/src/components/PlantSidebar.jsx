import React from 'react';
import { Factory, AlertCircle, Activity, LayoutDashboard, Settings, MapPin } from 'lucide-react';

export default function PlantSidebar({ selectedEquipment, setSelectedEquipment, currentTab, setCurrentTab }) {
  // Hardcoded for UI demonstration, could be fetched from backend /summary
  const equipmentList = [
    { id: 'BF-01', name: 'Blast Furnace #1', status: 'CRITICAL', temp: '1350°C', icon: Factory },
    { id: 'RM-02', name: 'Rolling Mill #2', status: 'WARNING', temp: '85°C', icon: Activity },
    { id: 'CC-03', name: 'Continuous Caster', status: 'HEALTHY', temp: '1100°C', icon: Factory },
    { id: 'EAF-01', name: 'Electric Arc Furnace', status: 'HEALTHY', temp: '1500°C', icon: Factory },
    { id: 'HYD-04', name: 'Main Hydraulic Pump', status: 'HEALTHY', temp: '60°C', icon: Activity },
  ];

  return (
    <div className="w-80 h-full flex flex-col glass-panel overflow-hidden border-r border-white/10">
      {/* Header */}
      <div className="p-6 border-b border-white/10 bg-white/5">
        <h2 className="text-xl font-bold tracking-wider flex items-center gap-3">
          <Factory className="w-6 h-6 text-accent-500" />
          <span className="bg-clip-text text-transparent bg-gradient-to-r from-white to-white/70">
            OMNISENSE
          </span>
        </h2>
        <p className="text-xs text-white/50 mt-1 uppercase tracking-widest font-mono">
          Jamshedpur Works
        </p>
      </div>

      {/* Navigation */}
      <div className="p-4 border-b border-white/10 flex flex-col gap-2">
        <button 
          onClick={() => setCurrentTab('dashboard')}
          className={`glass-button py-2 px-3 flex items-center justify-center gap-2 text-sm w-full ${currentTab === 'dashboard' ? 'bg-accent-500/20 text-accent-500 border-accent-500/50 shadow-[0_0_15px_rgba(0,240,255,0.2)]' : 'text-white/60 hover:text-white'}`}
        >
          <LayoutDashboard className="w-4 h-4" />
          Live Dashboard
        </button>
        <button 
          onClick={() => setCurrentTab('terminal')}
          className={`glass-button py-2 px-3 flex items-center justify-center gap-2 text-sm w-full ${currentTab === 'terminal' ? 'bg-accent-500/20 text-accent-500 border-accent-500/50 shadow-[0_0_15px_rgba(0,240,255,0.2)]' : 'text-white/60 hover:text-white'}`}
        >
          <Activity className="w-4 h-4" />
          Omni Terminal
        </button>
        <button 
          onClick={() => setCurrentTab('maintenance')}
          className={`glass-button py-2 px-3 flex items-center justify-center gap-2 text-sm w-full ${currentTab === 'maintenance' ? 'bg-accent-500/20 text-accent-500 border-accent-500/50 shadow-[0_0_15px_rgba(0,240,255,0.2)]' : 'text-white/60 hover:text-white'}`}
        >
          <Settings className="w-4 h-4" />
          Maintenance Logs
        </button>
      </div>

      {/* Equipment List */}
      <div className="flex-1 overflow-y-auto scrollbar-thin scrollbar-track-transparent scrollbar-thumb-white/10 p-4 space-y-3">
        <h3 className="text-xs uppercase tracking-widest text-white/40 mb-4 font-mono px-2">
          Active Equipment
        </h3>
        
        {equipmentList.map((eq) => {
          const isSelected = selectedEquipment === eq.id;
          const Icon = eq.icon;
          
          let statusColor = "text-success-500";
          let statusGlow = "";
          let bgHover = "hover:bg-white/5";
          
          if (eq.status === 'CRITICAL') {
            statusColor = "text-danger-500";
            statusGlow = "shadow-[0_0_10px_rgba(255,51,102,0.3)]";
            if (isSelected) bgHover = "bg-danger-500/10 border-danger-500/30";
          } else if (eq.status === 'WARNING') {
            statusColor = "text-warning-500";
            if (isSelected) bgHover = "bg-warning-500/10 border-warning-500/30";
          } else {
            if (isSelected) bgHover = "bg-white/10 border-white/20";
          }

          return (
            <button
              key={eq.id}
              onClick={() => setSelectedEquipment(eq.id)}
              className={`w-full text-left p-3 rounded-xl border border-transparent transition-all duration-300 ${bgHover} ${isSelected ? 'glass-button' : ''} group`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-lg bg-black/40 ${statusColor} ${statusGlow}`}>
                    <Icon className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="text-sm font-semibold text-white/90 group-hover:text-white transition-colors">
                      {eq.name}
                    </div>
                    <div className="text-xs text-white/40 font-mono mt-0.5">
                      {eq.id} • {eq.temp}
                    </div>
                  </div>
                </div>
                
                {eq.status === 'CRITICAL' && (
                  <AlertCircle className="w-4 h-4 text-danger-500 animate-pulse" />
                )}
              </div>
            </button>
          );
        })}
      </div>

      {/* Footer Settings */}
      <div className="p-4 border-t border-white/10">
        <button className="w-full glass-button py-3 px-4 flex items-center justify-center gap-2 text-sm text-white/60 hover:text-white">
          <Settings className="w-4 h-4" />
          System Configuration
        </button>
      </div>
    </div>
  );
}
