import React, { useState, useRef, useEffect } from 'react';
import { Send, Mic, Paperclip, Image as ImageIcon, Bot, User, Loader2, Factory, Flame, Activity, Zap, Droplet, FileText, Globe, FileDown } from 'lucide-react';

export default function OmniTerminal({ 
  messages, 
  sendMessage, 
  isTyping, 
  agentStatus, 
  selectedEquipment 
}) {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping, agentStatus]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!input.trim()) return;
    sendMessage(input);
    setInput('');
  };

  const suggestionCards = [
    {
      icon: <Flame className="w-5 h-5 text-orange-500" />,
      text: "BF-001 showing high temperature readings — what could be causing it?"
    },
    {
      icon: <Activity className="w-5 h-5 text-pink-400" />,
      text: "Rolling Mill 1 vibration is abnormal. Run full diagnostic."
    },
    {
      icon: <Zap className="w-5 h-5 text-yellow-500" />,
      text: "EAF-001 electrode breakage happening frequently — root cause analysis"
    },
    {
      icon: <Droplet className="w-5 h-5 text-blue-400" />,
      text: "Hydraulic system pressure dropping intermittently — diagnose"
    }
  ];

  return (
    <div className="flex-1 flex flex-col h-full relative overflow-hidden bg-[#0a0a0e]">
      {/* Messages Area / Empty State */}
      <div className="flex-1 overflow-y-auto p-6 scrollbar-thin scrollbar-track-transparent scrollbar-thumb-white/10">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center min-h-full text-white pt-10 pb-20">
            {/* Hero Section */}
            <div className="w-16 h-16 rounded-full bg-white/5 flex items-center justify-center mb-6 border border-white/10">
              <Factory className="w-8 h-8 text-blue-400" />
            </div>
            <h1 className="text-3xl font-bold mb-3 tracking-tight">OmniSense AI Wizard</h1>
            <p className="text-white/40 mb-12 text-sm">Multi-agent diagnostic intelligence for steel plant equipment</p>

            {/* Prompt Suggestions */}
            <div className="grid grid-cols-2 gap-4 max-w-3xl w-full mb-10">
              {suggestionCards.map((card, i) => (
                <button 
                  key={i}
                  onClick={() => {
                    setInput(card.text);
                  }}
                  className="bg-white/[0.03] hover:bg-white/[0.06] border border-white/5 hover:border-white/10 text-left p-4 rounded-2xl transition-all duration-200 flex items-start gap-4"
                >
                  <div className="mt-0.5 shrink-0">{card.icon}</div>
                  <span className="text-sm text-white/70 leading-relaxed">{card.text}</span>
                </button>
              ))}
            </div>

            {/* Feature Badges */}
            <div className="flex flex-wrap justify-center gap-6 max-w-3xl w-full">
              <div className="flex items-center gap-2 text-xs text-white/50">
                <ImageIcon className="w-4 h-4 text-green-400" /> Image Analysis
              </div>
              <div className="flex items-center gap-2 text-xs text-white/50">
                <FileText className="w-4 h-4 text-yellow-400" /> Sensor CSV
              </div>
              <div className="flex items-center gap-2 text-xs text-white/50">
                <Mic className="w-4 h-4 text-purple-400" /> Voice Input
              </div>
              <div className="flex items-center gap-2 text-xs text-white/50">
                <Globe className="w-4 h-4 text-blue-400" /> Multi-language
              </div>
              <div className="flex items-center gap-2 text-xs text-white/50">
                <FileDown className="w-4 h-4 text-red-400" /> PDF Reports
              </div>
              <div className="flex items-center gap-2 text-xs text-white/50 ml-4">
                <Zap className="w-4 h-4 text-orange-400" /> 8 AI Agents
              </div>
            </div>
          </div>
        ) : (
          <div className="space-y-6 max-w-4xl mx-auto w-full pt-4">
            {messages.map((msg, idx) => (
              <div key={idx} className={`flex gap-4 ${msg.sender === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${
                  msg.sender === 'user' 
                    ? 'bg-white/10 border border-white/20' 
                    : 'bg-blue-500/20 border border-blue-500/40 text-blue-400 shadow-[0_0_15px_rgba(59,130,246,0.2)]'
                }`}>
                  {msg.sender === 'user' ? <User className="w-5 h-5" /> : <Bot className="w-5 h-5" />}
                </div>
                
                <div className={`max-w-[85%] rounded-2xl p-5 ${
                  msg.sender === 'user'
                    ? 'bg-white/10 border border-white/10 text-white/90 rounded-tr-none'
                    : 'bg-white/5 border border-white/10 text-white/80 rounded-tl-none font-sans leading-relaxed'
                }`}>
                  <div className="prose prose-invert prose-sm max-w-none whitespace-pre-wrap">
                    {msg.text}
                  </div>
                </div>
              </div>
            ))}

            {/* Live Status Indicator */}
            {(isTyping || agentStatus) && (
              <div className="flex gap-4 animate-fade-in-up">
                <div className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0 bg-blue-500/20 border border-blue-500/40 text-blue-400 shadow-[0_0_15px_rgba(59,130,246,0.2)]">
                  <Bot className="w-5 h-5" />
                </div>
                <div className="bg-white/5 border border-white/10 rounded-2xl rounded-tl-none p-4 flex items-center gap-3">
                  <Loader2 className="w-4 h-4 text-blue-400 animate-spin" />
                  <span className="text-sm font-mono text-blue-400">{agentStatus || 'Processing...'}</span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input Area (ChatGPT Style) */}
      <div className="p-4 pb-6 shrink-0 w-full max-w-4xl mx-auto flex flex-col items-center relative">
        <form onSubmit={handleSubmit} className="w-full relative flex items-center bg-white/[0.08] hover:bg-white/[0.12] border border-white/10 transition-colors rounded-[2rem] p-2 pl-4 pr-2">
          
          <button type="button" className="p-2 text-white/40 hover:text-white transition-colors shrink-0">
            <Paperclip className="w-5 h-5" />
          </button>
          <button type="button" className="p-2 text-white/40 hover:text-white transition-colors shrink-0 mr-2">
            <Factory className="w-5 h-5" />
          </button>
          
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Describe the equipment issue, error codes, or symptoms..."
            className="flex-1 bg-transparent text-white/90 placeholder:text-white/30 outline-none text-[15px]"
          />
          
          <button 
            type="button" 
            className="p-2.5 text-white/40 hover:text-white transition-colors shrink-0 mx-1"
          >
            <Mic className="w-5 h-5" />
          </button>
          
          <button 
            type="submit" 
            disabled={!input.trim()}
            className="p-2.5 rounded-full bg-white/10 hover:bg-white/20 text-white transition-colors disabled:opacity-30 disabled:cursor-not-allowed shrink-0"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
        
        <div className="text-[11px] text-white/30 mt-3 tracking-wide">
          OmniSense processes through 8 AI agents · Auto-detects language · Supports image, CSV, voice, and PDF inputs
        </div>
      </div>
    </div>
  );
}
