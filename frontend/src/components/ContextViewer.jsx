import React from 'react';
import { ShieldAlert, BookOpen, Activity, FileWarning, ExternalLink } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

export default function ContextViewer({ context }) {
  // context object contains fields like: { rag_context, anomaly_result, vision_output, risk_details, report }
  
  if (!context || Object.keys(context).length === 0) {
    return (
      <div className="w-[400px] h-full glass-panel flex flex-col border-l border-white/10 items-center justify-center text-white/30 p-6 text-center">
        <ShieldAlert className="w-16 h-16 opacity-50 mb-4" />
        <p className="font-mono text-sm tracking-widest">CONTEXT VIEWER</p>
        <p className="text-xs mt-2 opacity-60">System context will appear here when agents are active.</p>
      </div>
    );
  }

  const { rag_context, anomaly_result, vision_output, risk_details } = context;

  return (
    <div className="w-[400px] h-full flex flex-col glass-panel overflow-hidden border-l border-white/10">
      <div className="h-16 border-b border-white/10 bg-white/5 flex items-center px-6 shrink-0">
        <span className="font-mono text-sm tracking-widest text-white/60">
          AGENT CONTEXT
        </span>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-thin scrollbar-track-transparent scrollbar-thumb-white/10">
        
        {/* Risk Scorer Widget */}
        {risk_details && (
          <div className="p-4 rounded-xl border border-danger-500/30 bg-danger-500/10 shadow-[0_0_15px_rgba(255,51,102,0.1)]">
            <h3 className="text-xs font-mono tracking-widest text-danger-500 mb-2 flex items-center gap-2">
              <ShieldAlert className="w-4 h-4" />
              RISK ASSESSMENT
            </h3>
            <div className="flex justify-between items-end">
              <div>
                <p className="text-2xl font-bold text-white">{risk_details.final_risk}</p>
                <p className="text-xs text-white/60 mt-1">Act within {risk_details.urgency_hours} hours</p>
              </div>
              <div className="text-right">
                <p className="text-xl font-mono text-danger-500">{risk_details.risk_score}</p>
              </div>
            </div>
          </div>
        )}

        {/* Anomaly Agent Widget */}
        {anomaly_result && (
          <div className="p-4 rounded-xl bg-white/5 border border-white/10">
            <h3 className="text-xs font-mono tracking-widest text-accent-500 mb-3 flex items-center gap-2">
              <Activity className="w-4 h-4" />
              SENSOR ANOMALY
            </h3>
            <div className="space-y-2 text-sm text-white/80">
              <div className="flex justify-between border-b border-white/10 pb-2">
                <span className="text-white/50">Status</span>
                <span className={anomaly_result.anomaly_detected ? "text-danger-500" : "text-success-500"}>
                  {anomaly_result.anomaly_detected ? "ANOMALY DETECTED" : "NORMAL"}
                </span>
              </div>
              <div className="flex justify-between border-b border-white/10 pb-2">
                <span className="text-white/50">Anomaly Score</span>
                <span className="font-mono">{anomaly_result.anomaly_score}</span>
              </div>
              <div className="flex justify-between border-b border-white/10 pb-2">
                <span className="text-white/50">Culprit Sensor</span>
                <span className="font-mono text-accent-500">{anomaly_result.anomalous_sensor}</span>
              </div>
              <div className="flex justify-between pt-1">
                <span className="text-white/50">Predicted RUL</span>
                <span className="font-mono text-heat-500">{anomaly_result.rul_days} Days</span>
              </div>
            </div>
          </div>
        )}

        {/* Vision Agent Widget */}
        {vision_output && vision_output.fault_detected && (
          <div className="p-4 rounded-xl bg-white/5 border border-white/10">
            <h3 className="text-xs font-mono tracking-widest text-accent-500 mb-3 flex items-center gap-2">
              <FileWarning className="w-4 h-4" />
              VISION ANALYSIS
            </h3>
            <div className="space-y-2 text-sm text-white/80">
              <p><span className="text-white/50">Fault Type:</span> {vision_output.fault_type}</p>
              <p><span className="text-white/50">Component:</span> {vision_output.affected_component}</p>
              <div className="flex items-center gap-2 mt-2">
                <span className="text-white/50">Confidence:</span>
                <div className="flex-1 h-2 bg-black/50 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-accent-500" 
                    style={{ width: `${vision_output.confidence * 100}%` }}
                  />
                </div>
                <span className="font-mono text-xs">{Math.round(vision_output.confidence * 100)}%</span>
              </div>
            </div>
          </div>
        )}

        {/* RAG Context Widget */}
        {rag_context && rag_context.length > 0 && (
          <div className="p-4 rounded-xl bg-white/5 border border-white/10">
            <h3 className="text-xs font-mono tracking-widest text-accent-500 mb-3 flex items-center gap-2">
              <BookOpen className="w-4 h-4" />
              KNOWLEDGE BASE
            </h3>
            <div className="space-y-3">
              {rag_context.map((doc, idx) => (
                <div key={idx} className="bg-black/30 p-3 rounded-lg border border-white/5">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-xs font-mono text-white/50 flex items-center gap-1">
                      <ExternalLink className="w-3 h-3" />
                      {doc.source}
                    </span>
                    <span className="text-[10px] bg-accent-500/20 text-accent-500 px-2 py-0.5 rounded">
                      Page {doc.page}
                    </span>
                  </div>
                  <p className="text-xs text-white/70 line-clamp-3 leading-relaxed">
                    "{doc.content}"
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}
        
      </div>
    </div>
  );
}
