import React, { useEffect, useState } from 'react';
import { API_BASE } from '../api';
import { Activity, ShieldAlert, ArrowUpRight, Wrench } from 'lucide-react';

export default function RiskPage() {
  const [predictions, setPredictions] = useState([]);
  
  useEffect(() => {
    fetch(`${API_BASE}/predictions`)
      .then((res) => res.json())
      .then((data) => setPredictions(data.predictions || []))
      .catch(() => setPredictions([]));
  }, []);

  const getRiskColor = (risk) => {
    switch (risk) {
      case 'CRITICAL': return 'bg-red-500/20 text-red-500 border-red-500/50 shadow-[0_0_15px_rgba(239,68,68,0.2)]';
      case 'HIGH': return 'bg-orange-500/20 text-orange-500 border-orange-500/50';
      case 'MEDIUM': return 'bg-yellow-500/20 text-yellow-500 border-yellow-500/50';
      case 'LOW': return 'bg-green-500/20 text-green-500 border-green-500/50';
      default: return 'bg-slate-500/20 text-slate-500 border-slate-500/50';
    }
  };

  const getRulColor = (rul) => {
    if (rul < 7) return 'text-red-500';
    if (rul < 14) return 'text-orange-500';
    if (rul < 30) return 'text-yellow-500';
    return 'text-green-500';
  };

  return (
    <div className="p-8 h-full overflow-y-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Risk & Operations</h1>
        <p className="text-slate-400">Predictive maintenance and equipment risk scoring</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
        {predictions.map((item) => (
          <div key={item.equipment_id} className={`bg-[#181a24] border rounded-xl p-6 transition-all hover:-translate-y-1 ${getRiskColor(item.risk_level)}`}>
            <div className="flex justify-between items-start mb-6">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-white/5 border border-white/10 flex items-center justify-center text-white">
                  <Wrench size={20} />
                </div>
                <div>
                  <h3 className="font-bold text-lg text-white">{item.equipment_id}</h3>
                  <p className="text-xs font-mono opacity-80">Last Scan: {new Date(item.last_updated).toLocaleTimeString()}</p>
                </div>
              </div>
              <span className="px-3 py-1 rounded-full text-xs font-black tracking-wider border border-current bg-white/5 uppercase">
                {item.risk_level}
              </span>
            </div>
            
            <div className="grid grid-cols-2 gap-4 mb-6">
              <div className="bg-black/20 rounded-lg p-4 border border-white/5">
                <p className="text-xs uppercase tracking-wider font-semibold opacity-70 mb-1 flex items-center gap-1">
                  <Activity size={14} /> Est. RUL
                </p>
                <div className={`text-3xl font-black ${getRulColor(item.rul_days)}`}>
                  {item.rul_days} <span className="text-sm font-medium opacity-70">days</span>
                </div>
              </div>
              
              <div className="bg-black/20 rounded-lg p-4 border border-white/5 flex flex-col justify-center items-center text-center">
                <ShieldAlert size={24} className="mb-2 opacity-50" />
                <p className="text-xs opacity-70">Requires attention</p>
              </div>
            </div>
            
            <button className="w-full py-3 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-sm font-bold text-white transition-colors flex items-center justify-center gap-2">
              View Analytics <ArrowUpRight size={16} />
            </button>
          </div>
        ))}
        {predictions.length === 0 && (
          <div className="col-span-full flex justify-center p-12 text-slate-500">
            Fetching predictions...
          </div>
        )}
      </div>
    </div>
  );
}
