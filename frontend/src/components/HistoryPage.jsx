import React, { useEffect, useState } from 'react';
import html2pdf from 'html2pdf.js';
import { API_BASE } from '../api';
import { Clock, MessageSquare, AlertCircle, Calendar } from 'lucide-react';

export default function HistoryPage() {
  const [history, setHistory] = useState(null);

  useEffect(() => {
    fetch(`${API_BASE}/history`)
      .then((res) => res.json())
      .then(setHistory)
      .catch(() => setHistory({ total_sessions: 0, sessions: {} }));
  }, []);

  const sessions = Object.entries(history?.sessions || {}).reverse();

  const getRiskColor = (risk) => {
    switch (risk) {
      case 'CRITICAL': return 'border-red-500 text-red-500 bg-red-500/10';
      case 'HIGH': return 'border-orange-500 text-orange-500 bg-orange-500/10';
      case 'MEDIUM': return 'border-yellow-500 text-yellow-500 bg-yellow-500/10';
      case 'LOW': return 'border-green-500 text-green-500 bg-green-500/10';
      default: return 'border-slate-500 text-slate-500 bg-slate-500/10';
    }
  };

  return (
    <div className="p-8 h-full overflow-y-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Session History</h1>
        <p className="text-slate-400">Past AI diagnostic sessions</p>
      </div>
      
      <div className="space-y-6">
        {sessions.length === 0 ? (
          <div className="flex flex-col items-center justify-center p-12 text-slate-500">
            <Clock size={48} className="mb-4 opacity-50" />
            <p>No historical sessions found.</p>
          </div>
        ) : sessions.map(([id, session]) => {
          const riskLevel = session.result?.risk_level || 'UNKNOWN';
          const riskStyle = getRiskColor(riskLevel);
          
          return (
            <div key={id} className="flex gap-4">
              {/* Timeline Line */}
              <div className="flex flex-col items-center">
                <div className="w-4 h-4 rounded-full bg-blue-500 border-4 border-[#090a0f] z-10" />
                <div className="w-0.5 h-full bg-white/10 -mt-2" />
              </div>
              
              {/* Content Card */}
              <div id={`session-card-${id}`} className={`flex-1 bg-[#181a24] border border-white/10 rounded-xl p-6 mb-4 hover:border-white/20 transition-all ${riskStyle.split(' ')[0]} border-l-4`}>
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h3 className="font-bold text-lg mb-1 flex items-center gap-2">
                      <MessageSquare size={16} className="text-blue-500" />
                      Session: {id.slice(0,8)}...
                    </h3>
                    <div className="flex items-center gap-4 text-xs text-slate-400">
                      <span className="flex items-center gap-1"><Calendar size={12}/> {new Date(session.timestamp).toLocaleString()}</span>
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${riskStyle}`}>
                        {riskLevel} RISK
                      </span>
                    </div>
                  </div>
                  <button 
                    onClick={() => {
                      const element = document.getElementById(`session-card-${id}`);
                      if (element) {
                        const clone = element.cloneNode(true);
                        clone.style.background = '#181a24';
                        clone.style.color = '#ffffff';
                        const opt = {
                          margin: 0.5,
                          filename: `session_${id.slice(0,8)}.pdf`,
                          image: { type: 'jpeg', quality: 0.98 },
                          html2canvas: { scale: 2, backgroundColor: '#181a24' },
                          jsPDF: { unit: 'in', format: 'letter', orientation: 'portrait' }
                        };
                        html2pdf().set(opt).from(clone).save();
                      }
                    }}
                    className="px-3 py-1 bg-blue-600 hover:bg-blue-500 text-white rounded text-xs font-bold transition flex items-center gap-1"
                  >
                    ⬇️ Download PDF
                  </button>
                </div>
                
                <div className="bg-black/20 rounded-lg p-4 mb-4 space-y-4 max-h-[400px] overflow-y-auto">
                  {session.messages && session.messages.length > 0 ? (
                    session.messages.map((m, idx) => {
                      const msgType = m.type || (m.id && m.id[m.id.length - 1] ? m.id[m.id.length - 1].replace('Message', '').toLowerCase() : 'human');
                      const isHuman = msgType === 'human';
                      const textContent = typeof m.content === 'string' ? m.content : JSON.stringify(m.content);
                      
                      return (
                        <div key={idx} className={`flex gap-3 ${isHuman ? 'justify-end' : 'justify-start'}`}>
                          {!isHuman && <div className="w-8 h-8 rounded-full bg-blue-500/20 flex items-center justify-center shrink-0" style={{ fontSize: '16px' }}>🤖</div>}
                          <div className={`p-3 rounded-lg max-w-[85%] ${isHuman ? 'bg-blue-600/30 border border-blue-500/30' : 'bg-[#1e202d] border border-white/10 markdown-body'}`} style={{ fontSize: '13px' }}>
                            <p className="whitespace-pre-wrap text-slate-300">{textContent}</p>
                          </div>
                          {isHuman && <div className="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center shrink-0" style={{ fontSize: '16px' }}>👷</div>}
                        </div>
                      );
                    })
                  ) : (
                    <p className="text-sm italic text-slate-300">"{session.query}"</p>
                  )}
                </div>
                
                {session.result?.diagnosis?.fault_identified && (
                  <div className="flex items-start gap-2 text-sm text-slate-300">
                    <AlertCircle size={16} className="text-blue-500 mt-0.5 shrink-0" />
                    <p>{session.result.diagnosis.fault_identified}</p>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
