import React, { useEffect, useState } from 'react';
import { API_BASE } from '../api';
import { Ticket, AlertTriangle, CheckCircle, Clock } from 'lucide-react';

export default function TicketsPage() {
  const [tickets, setTickets] = useState([]);
  
  useEffect(() => {
    fetch(`${API_BASE}/api/tickets`)
      .then((res) => res.json())
      .then((data) => setTickets(data.tickets || []))
      .catch(() => setTickets([]));
  }, []);

  const getSeverityColor = (sev) => {
    switch (sev?.toUpperCase()) {
      case 'CRITICAL': return 'bg-red-500/20 text-red-500 border-red-500/30';
      case 'HIGH': return 'bg-orange-500/20 text-orange-500 border-orange-500/30';
      case 'MEDIUM': return 'bg-yellow-500/20 text-yellow-500 border-yellow-500/30';
      case 'LOW': return 'bg-green-500/20 text-green-500 border-green-500/30';
      default: return 'bg-slate-500/20 text-slate-500 border-slate-500/30';
    }
  };

  const getStatusIcon = (status) => {
    if (status === 'OPEN') return <AlertTriangle size={16} className="text-orange-500" />;
    if (status === 'IN_PROGRESS') return <Clock size={16} className="text-blue-500" />;
    return <CheckCircle size={16} className="text-green-500" />;
  };

  return (
    <div className="p-8 h-full overflow-y-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Maintenance Tickets</h1>
        <p className="text-slate-400">Manage and track generated repair tickets</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
        {tickets.length === 0 ? (
          <div className="col-span-full flex flex-col items-center justify-center p-12 text-slate-500">
            <Ticket size={48} className="mb-4 opacity-50" />
            <p>No active tickets found.</p>
          </div>
        ) : tickets.map((ticket) => (
          <div key={ticket.id} className="bg-[#181a24] border border-white/10 rounded-xl p-6 hover:border-white/20 transition-all flex flex-col">
            <div className="flex justify-between items-start mb-4">
              <span className="text-xs font-mono text-slate-500">{ticket.id}</span>
              <div className="flex gap-2">
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase border ${getSeverityColor(ticket.severity)}`}>
                  {ticket.severity}
                </span>
                <span className="flex items-center gap-1 px-2 py-0.5 rounded bg-white/5 border border-white/10 text-[10px] font-bold uppercase">
                  {getStatusIcon(ticket.status)} {ticket.status}
                </span>
              </div>
            </div>
            
            <h3 className="text-lg font-bold mb-2 text-white">{ticket.title}</h3>
            <p className="text-sm text-slate-400 mb-6 flex-1 line-clamp-3">
              {ticket.description}
            </p>
            
            <div className="pt-4 border-t border-white/10 flex justify-between items-center text-xs text-slate-500">
              <span className="flex items-center gap-1"><Clock size={12}/> {new Date().toLocaleDateString()}</span>
              <button className="text-blue-500 hover:text-blue-400 font-medium">View Details →</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
