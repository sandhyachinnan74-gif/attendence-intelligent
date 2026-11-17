import React, { useEffect, useState, useRef } from 'react';
import {
  Bot,
  Send,
  Plus,
  Trash2,
  Sparkles,
  ShieldCheck,
  FileText,
  Database,
  Copy,
  Check,
  RotateCcw,
  Zap,
  Cpu,
  Layers,
  HelpCircle,
  ChevronRight
} from 'lucide-react';
import { api } from '../services/api';
import { Conversation, ConversationMessage } from '../types';
import { useAuth } from '../context/AuthContext';
import { MarkdownRenderer } from '../components/common/MarkdownRenderer';

export const AIAssistant: React.FC = () => {
  const { user } = useAuth();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConvId, setActiveConvId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ConversationMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [activeProvider, setActiveProvider] = useState<string>('NVIDIA NIM (Mistral Large 4)');
  const [loadingStage, setLoadingStage] = useState<string>('Selecting authorized tools...');

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const roleScopedPrompts = user?.role === 'employee' ? [
    'What is my attendance record this month?',
    'What are our official core working hours?',
    'What is the policy for requesting remote work?',
    'How is overtime calculated for hourly shifts?',
  ] : [
    'Which employees arrived late more than five times this month?',
    'Who had the most overtime last month?',
    'Which department has the highest absenteeism?',
    'Find employees with both repeated lateness and excessive overtime.',
    'Compare late arrivals between Engineering and Sales.',
    'List pending anomaly flags requiring investigation.'
  ];

  const fetchConversations = async () => {
    try {
      const res = await api.get('/ai/conversations');
      setConversations(res.data);
      if (res.data.length > 0 && !activeConvId) {
        selectConversation(res.data[0].id);
      }
    } catch (e) {
      console.error('Failed to load conversations:', e);
    }
  };

  const selectConversation = async (convId: string) => {
    setActiveConvId(convId);
    try {
      const res = await api.get(`/ai/conversations/${convId}`);
      setMessages(res.data.messages || []);
    } catch (e) {
      console.error('Failed to load messages:', e);
    }
  };

  useEffect(() => {
    fetchConversations();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const handleSend = async (textToSend?: string) => {
    const prompt = (textToSend || input).trim();
    if (!prompt) return;

    setInput('');
    const tempUserMsg: ConversationMessage = {
      id: `temp_${Date.now()}`,
      role: 'user',
      content: prompt,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempUserMsg]);
    setLoading(true);
    setLoadingStage('Analyzing intent & evaluating scope permissions...');

    // Progress stage simulation
    const stage1 = setTimeout(() => {
      setLoadingStage('Querying PostgreSQL workforce database...');
    }, 700);
    const stage2 = setTimeout(() => {
      setLoadingStage('Synthesizing executive workforce intelligence...');
    }, 1800);

    try {
      const res = await api.post(
        '/ai/chat',
        { content: prompt },
        { params: activeConvId ? { conversation_id: activeConvId } : {} }
      );

      clearTimeout(stage1);
      clearTimeout(stage2);

      const { conversation_id, message, provider, model } = res.data;
      if (provider) {
        setActiveProvider(
          provider === 'nvidia'
            ? `NVIDIA NIM (${model || 'Mistral Large 4'})`
            : provider === 'groq'
            ? `GroqCloud (${model || 'GPT-OSS-120B'})`
            : 'AttendAI Intelligence Engine'
        );
      }

      if (!activeConvId) {
        setActiveConvId(conversation_id);
        fetchConversations();
      }
      setMessages((prev) => [...prev, message]);
    } catch (err: any) {
      clearTimeout(stage1);
      clearTimeout(stage2);
      const errorMsg: ConversationMessage = {
        id: `err_${Date.now()}`,
        role: 'assistant',
        content: `Error: ${err.response?.data?.detail || 'Failed to process workforce inquiry with the backend AI harness.'}`,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = (id: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleRegenerate = () => {
    const lastUserMsg = [...messages].reverse().find((m) => m.role === 'user');
    if (lastUserMsg) {
      handleSend(lastUserMsg.content);
    }
  };

  const handleNewChat = () => {
    setActiveConvId(null);
    setMessages([]);
  };

  const handleDeleteConversation = async (convId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await api.delete(`/ai/conversations/${convId}`);
      if (activeConvId === convId) {
        handleNewChat();
      }
      fetchConversations();
    } catch (e) {
      console.error('Failed to delete conversation:', e);
    }
  };

  return (
    <div className="h-[calc(100vh-7rem)] flex bg-card border border-border rounded-xl shadow-card overflow-hidden">
      {/* Conversations Sidebar */}
      <div className="w-64 border-r border-border bg-slate-50/70 flex flex-col justify-between">
        <div className="p-3 border-b border-border space-y-2">
          <button
            onClick={handleNewChat}
            className="w-full py-2 px-3 bg-white hover:bg-slate-100 border border-border rounded-lg text-xs font-semibold text-dark flex items-center justify-center gap-1.5 shadow-xs transition-colors"
          >
            <Plus className="w-3.5 h-3.5 text-primary" />
            <span>New Conversation</span>
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {conversations.length === 0 ? (
            <p className="text-[11px] text-secondary text-center py-6">No previous conversations.</p>
          ) : (
            conversations.map((c) => (
              <div
                key={c.id}
                onClick={() => selectConversation(c.id)}
                className={`group px-3 py-2 rounded-lg text-xs font-medium cursor-pointer flex items-center justify-between transition-colors ${
                  activeConvId === c.id
                    ? 'bg-primary text-white font-semibold'
                    : 'text-secondary hover:text-dark hover:bg-slate-200/50'
                }`}
              >
                <span className="truncate pr-2">{c.title}</span>
                <button
                  onClick={(e) => handleDeleteConversation(c.id, e)}
                  className={`opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-black/10 transition-opacity ${
                    activeConvId === c.id ? 'text-white' : 'text-secondary hover:text-danger'
                  }`}
                  title="Delete conversation"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Main Chat Workspace */}
      <div className="flex-1 flex flex-col bg-white">
        {/* Chat Header */}
        <div className="px-6 py-3 border-b border-border bg-slate-50/50 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-primary text-white flex items-center justify-center shadow-xs">
              <Bot className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-xs font-bold text-dark">AttendAI Workforce Intelligence</h2>
              <div className="flex items-center gap-1.5 text-[10px] text-secondary">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                {user?.role === 'admin' ? (
                  <span>AI Engine: <strong>{activeProvider}</strong></span>
                ) : (
                  <span>Enterprise Assistant &bull; Ready</span>
                )}
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {messages.length > 0 && (
              <button
                onClick={handleRegenerate}
                disabled={loading}
                className="py-1 px-2.5 rounded-md border border-border bg-white hover:bg-slate-100 text-[11px] font-medium text-secondary hover:text-dark flex items-center gap-1 transition-colors shadow-xs"
                title="Regenerate last response"
              >
                <RotateCcw className="w-3 h-3 text-primary" />
                <span>Regenerate</span>
              </button>
            )}
            <button
              onClick={handleNewChat}
              className="py-1 px-2.5 rounded-md border border-border bg-white hover:bg-slate-100 text-[11px] font-medium text-secondary hover:text-dark flex items-center gap-1 transition-colors shadow-xs"
            >
              <Plus className="w-3 h-3" />
              <span>Clear</span>
            </button>
          </div>
        </div>

        {/* Messages Thread */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center max-w-lg mx-auto text-center">
              <div className="w-14 h-14 rounded-2xl bg-blue-50 text-primary flex items-center justify-center mb-3 shadow-xs border border-blue-100">
                <Bot className="w-8 h-8" />
              </div>
              <h2 className="text-base font-bold text-dark">Enterprise Workforce Analyst</h2>
              <p className="text-xs text-secondary mt-1 max-w-sm">
                Ask analytical questions regarding attendance trends, tardiness, overtime, departmental absenteeism, or policy rules grounded in verified PostgreSQL records.
              </p>

              {/* Suggested Prompts */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-6 w-full text-left">
                {roleScopedPrompts.map((prompt, i) => (
                  <button
                    key={i}
                    onClick={() => handleSend(prompt)}
                    className="p-2.5 rounded-lg border border-border hover:border-primary/50 hover:bg-blue-50/40 text-xs text-dark transition-colors flex items-start gap-2 shadow-xs group"
                  >
                    <Sparkles className="w-3.5 h-3.5 text-primary flex-shrink-0 mt-0.5 group-hover:scale-110 transition-transform" />
                    <span className="font-medium text-slate-700">{prompt}</span>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((m) => (
              <div
                key={m.id}
                className={`flex gap-3 text-xs leading-relaxed ${
                  m.role === 'user' ? 'justify-end' : 'justify-start'
                }`}
              >
                {m.role === 'assistant' && (
                  <div className="w-7 h-7 rounded-lg bg-primary text-white flex items-center justify-center flex-shrink-0 mt-0.5 shadow-xs">
                    <Bot className="w-4 h-4" />
                  </div>
                )}

                <div
                  className={`max-w-2xl p-4 rounded-xl shadow-xs space-y-2.5 ${
                    m.role === 'user'
                      ? 'bg-primary text-white rounded-br-none'
                      : 'bg-slate-50/90 border border-border text-dark rounded-bl-none'
                  }`}
                >
                  {/* Tool Execution Transparency */}
                  {m.tool_calls && m.tool_calls.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 pb-1">
                      {m.tool_calls.map((tc, idx) => (
                        <span
                          key={idx}
                          className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-white border border-border text-[10px] font-mono text-primary font-semibold shadow-xs"
                        >
                          <Database className="w-3 h-3 text-primary" />
                          <span>Tool: {tc.function?.name}</span>
                        </span>
                      ))}
                    </div>
                  )}

                  {/* Message Content */}
                  {m.role === 'user' ? (
                    <p className="whitespace-pre-wrap font-medium">{m.content}</p>
                  ) : (
                    <div className="text-slate-900 leading-relaxed">
                      <MarkdownRenderer content={m.content} />
                    </div>
                  )}

                  {/* Source Citations */}
                  {m.citations && m.citations.length > 0 && (
                    <div className="pt-2.5 border-t border-border/80 space-y-1">
                      <span className="text-[10px] font-bold text-secondary uppercase tracking-wider block">
                        Verified Sources & Authoritative Citations
                      </span>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
                        {m.citations.map((cite: any, idx: number) => (
                          <div
                            key={idx}
                            className="flex items-center gap-1.5 p-1.5 rounded bg-white border border-border text-[11px] text-primary font-medium shadow-xs"
                          >
                            <FileText className="w-3.5 h-3.5 text-primary flex-shrink-0" />
                            <span className="truncate">{cite.source}</span>
                            {cite.page && <span className="text-secondary text-[10px]">(Page {cite.page})</span>}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Suggested Follow-up Questions */}
                  {m.follow_ups && m.follow_ups.length > 0 && (
                    <div className="pt-2 border-t border-border/60">
                      <span className="text-[10px] font-semibold text-secondary block mb-1.5">
                        Suggested Follow-ups:
                      </span>
                      <div className="flex flex-wrap gap-1.5">
                        {m.follow_ups.map((q, idx) => (
                          <button
                            key={idx}
                            onClick={() => handleSend(q)}
                            className="text-[11px] py-1 px-2 rounded-md bg-white hover:bg-blue-50 border border-border hover:border-primary/40 text-slate-700 hover:text-primary transition-colors flex items-center gap-1 shadow-xs font-medium"
                          >
                            <ChevronRight className="w-3 h-3 text-primary" />
                            <span>{q}</span>
                          </button>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Actions Bar (Copy) */}
                  {m.role === 'assistant' && (
                    <div className="pt-1.5 flex justify-end">
                      <button
                        onClick={() => handleCopy(m.id, m.content)}
                        className="p-1 text-secondary hover:text-dark rounded hover:bg-white transition-colors flex items-center gap-1 text-[10px]"
                        title="Copy to clipboard"
                      >
                        {copiedId === m.id ? (
                          <>
                            <Check className="w-3 h-3 text-emerald-600" />
                            <span className="text-emerald-600 font-semibold">Copied</span>
                          </>
                        ) : (
                          <>
                            <Copy className="w-3 h-3" />
                            <span>Copy Markdown</span>
                          </>
                        )}
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ))
          )}

          {loading && (
            <div className="flex gap-3 text-xs">
              <div className="w-7 h-7 rounded-lg bg-primary text-white flex items-center justify-center flex-shrink-0 shadow-xs">
                <Bot className="w-4 h-4" />
              </div>
              <div className="bg-slate-50 border border-border p-3.5 rounded-xl flex items-center gap-2.5 text-secondary shadow-xs">
                <div className="w-3.5 h-3.5 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                <span className="font-medium text-slate-700">{loadingStage}</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar */}
        <div className="p-4 border-t border-border bg-slate-50/40">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSend();
            }}
            className="flex items-center gap-2"
          >
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask AttendAI an analytical question about attendance, late arrivals, overtime, policies..."
              disabled={loading}
              className="flex-1 px-4 py-2.5 bg-white border border-border rounded-xl text-xs text-dark focus:outline-none focus:ring-1 focus:ring-primary shadow-xs disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="p-2.5 bg-primary text-white rounded-xl hover:bg-primary-hover shadow-xs transition-colors disabled:opacity-50 flex items-center justify-center"
            >
              <Send className="w-4 h-4" />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};
