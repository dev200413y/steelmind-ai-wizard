import React, { useEffect, useState } from 'react';
import { API_BASE } from '../api';
import { BarChart3, Activity, ShieldAlert, CheckCircle, FileText, Database } from 'lucide-react';

export default function AnalyticsPage() {
  const [data, setData] = useState(null);

  useEffect(() => {
    fetch(`${API_BASE}/api/analytics/overview`)
      .then((res) => res.json())
      .then(setData)
      .catch(() => setData(null));
  }, []);

  return (
    <div className="p-8 h-full overflow-y-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Analytics Overview</h1>
        <p className="text-slate-400">System-wide operational metrics and insights</p>
      </div>
      
      <div className="grid grid-cols-4 gap-6 mb-8">
        <div className="bg-[#181a24] border border-white/10 rounded-xl p-6 flex items-center gap-4 hover:border-blue-500/50 transition-all">
          <div className="w-12 h-12 rounded-lg bg-blue-500/20 flex items-center justify-center text-blue-500">
            <Activity size={24} />
          </div>
          <div>
            <p className="text-slate-400 text-sm font-medium">Total Sessions</p>
            <p className="text-3xl font-bold">{data?.sessions ?? '--'}</p>
          </div>
        </div>
        
        <div className="bg-[#181a24] border border-white/10 rounded-xl p-6 flex items-center gap-4 hover:border-orange-500/50 transition-all">
          <div className="w-12 h-12 rounded-lg bg-orange-500/20 flex items-center justify-center text-orange-500">
            <FileText size={24} />
          </div>
          <div>
            <p className="text-slate-400 text-sm font-medium">Total Tickets</p>
            <p className="text-3xl font-bold">{data?.tickets ?? '--'}</p>
          </div>
        </div>
        
        <div className="bg-[#181a24] border border-white/10 rounded-xl p-6 flex items-center gap-4 hover:border-red-500/50 transition-all">
          <div className="w-12 h-12 rounded-lg bg-red-500/20 flex items-center justify-center text-red-500">
            <ShieldAlert size={24} />
          </div>
          <div>
            <p className="text-slate-400 text-sm font-medium">Open Tickets</p>
            <p className="text-3xl font-bold">{data?.open_tickets ?? '--'}</p>
          </div>
        </div>
        
        <div className="bg-[#181a24] border border-white/10 rounded-xl p-6 flex items-center gap-4 hover:border-green-500/50 transition-all">
          <div className="w-12 h-12 rounded-lg bg-green-500/20 flex items-center justify-center text-green-500">
            <CheckCircle size={24} />
          </div>
          <div>
            <p className="text-slate-400 text-sm font-medium">Reports Generated</p>
            <p className="text-3xl font-bold">{data?.reports ?? '--'}</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-6">
        <div className="bg-[#181a24] border border-white/10 rounded-xl p-6">
          <h2 className="text-lg font-bold mb-4 flex items-center gap-2"><BarChart3 size={20} className="text-blue-500"/> Risk Distribution</h2>
          <div className="space-y-4 mt-6">
            {Object.entries(data?.risk_counts || {}).map(([risk, count]) => (
              <div key={risk} className="flex items-center justify-between">
                <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase
                  ${risk === 'CRITICAL' ? 'bg-red-500/20 text-red-500' : 
                    risk === 'HIGH' ? 'bg-orange-500/20 text-orange-500' : 
                    risk === 'MEDIUM' ? 'bg-yellow-500/20 text-yellow-500' : 
                    'bg-green-500/20 text-green-500'}`}>
                  {risk}
                </span>
                <span className="font-bold">{count}</span>
              </div>
            ))}
            {Object.keys(data?.risk_counts || {}).length === 0 && (
              <div className="text-center text-slate-500 py-8">No risk data available</div>
            )}
          </div>
        </div>
        
        <div className="bg-[#181a24] border border-white/10 rounded-xl p-6 flex flex-col items-center justify-center text-slate-500 text-sm">
          <Database size={48} className="mb-4 opacity-50" />
          <p>More detailed analytics coming soon...</p>
        </div>
      </div>
    </div>
  );
}
