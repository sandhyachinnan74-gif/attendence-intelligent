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
  ArrowRight,
  Clock,
  ExternalLink,
} from 'lucide-react';
import { api } from '../services/api';
import { Conversation, ConversationMessage } from '../types';
import { useAuth } from '../context/AuthContext';

export const AIAssistant: React.FC = () => {
  const { user } = useAuth();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConvId, setActiveConvId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ConversationMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const suggestedPrompts = [
    'Which employees arrived late more than five times this month?',
    'Show overtime by department.',
    'What is our overtime policy?',
    'Summarize this week’s attendance trends.',
    'Show my attendance records for the last two weeks.',
    'List pending anomaly flags requiring investigation.',
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

    try {
      const res = await api.post('/ai/chat', {
        content: prompt,
      }, {
        params: activeConvId ? { conversation_id: activeConvId } : {},
      });

      const { conversation_id, message } = res.data;
      if (!activeConvId) {
        setActiveConvId(conversation_id);
        fetchConversations();
      }
      setMessages((prev) => [...prev, message]);
    } catch (err: any) {
      const errorMsg: ConversationMessage = {
        id: `err_${Date.now()}`,
        role: 'assistant',
        content: `Error: ${err.response?.data?.detail || 'Failed to process AI query with the backend harness.'}`,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
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
      <div className="w-64 border-r border-border bg-slate-50/60 flex flex-col justify-between">
        <div className="p-3 border-b border-border">
          <button
            onClick={handleNewChat}
            className="w-full py-2 px-3 bg-white hover:bg-slate-100 border border-border rounded-lg text-xs font-semibold text-dark flex items-center justify-center gap-1.5 shadow-sm transition-colors"
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

        {/* Security Harness Badge */}
        <div className="p-3 border-t border-border bg-white text-[11px] text-secondary flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-primary flex-shrink-0" />
          <span>Security Harness Active (Role-Scoped RBAC)</span>
        </div>
      </div>

      {/* Main Chat Workspace */}
      <div className="flex-1 flex flex-col bg-white">
        {/* Messages Thread */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center max-w-lg mx-auto text-center">
              <div className="w-12 h-12 rounded-2xl bg-primary/10 text-primary flex items-center justify-center mb-3 shadow-sm">
                <Bot className="w-7 h-7" />
              </div>
              <h2 className="text-base font-bold text-dark">AttendAI Workforce Intelligence</h2>
              <p className="text-xs text-secondary mt-1 max-w-sm">
                Ask questions about employee attendance, overtime, late arrivals, policies, or anomaly flags backed by
                verified database records.
              </p>

              {/* Suggested Prompts */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-6 w-full text-left">
                {suggestedPrompts.map((prompt, i) => (
                  <button
                    key={i}
                    onClick={() => handleSend(prompt)}
                    className="p-2.5 rounded-lg border border-border hover:border-primary/50 hover:bg-blue-50/40 text-xs text-dark transition-colors flex items-start gap-2"
                  >
                    <Sparkles className="w-3.5 h-3.5 text-primary flex-shrink-0 mt-0.5" />
                    <span>{prompt}</span>
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
                  <div className="w-7 h-7 rounded-lg bg-primary text-white flex items-center justify-center flex-shrink-0 mt-0.5">
                    <Bot className="w-4 h-4" />
                  </div>
                )}

                <div
                  className={`max-w-xl p-3.5 rounded-xl shadow-sm space-y-2 ${
                    m.role === 'user'
                      ? 'bg-primary text-white rounded-br-none'
                      : 'bg-slate-50 border border-border text-dark rounded-bl-none'
                  }`}
                >
                  {/* Tool execution transparency pills */}
                  {m.tool_calls && m.tool_calls.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 pb-1">
                      {m.tool_calls.map((tc, idx) => (
                        <span
                          key={idx}
                          className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-white border border-border text-[10px] font-mono text-primary font-semibold"
                        >
                          <Database className="w-3 h-3 text-primary" />
                          <span>Tool: {tc.function?.name}</span>
                        </span>
                      ))}
                    </div>
                  )}

                  <p className="whitespace-pre-wrap">{m.content}</p>

                  {/* Source Citations */}
                  {m.citations && m.citations.length > 0 && (
                    <div className="pt-2 border-t border-border/80 space-y-1">
                      <span className="text-[10px] font-bold text-secondary uppercase tracking-wider block">
                        Verified Sources & Citations
                      </span>
                      {m.citations.map((cite: any, idx: number) => (
                        <div key={idx} className="flex items-center gap-1.5 text-[11px] text-primary font-medium">
                          <FileText className="w-3 h-3" />
                          <span>{cite.source}</span>
                          {cite.page && <span className="text-secondary">(Page {cite.page})</span>}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))
          )}

          {loading && (
            <div className="flex gap-3 text-xs">
              <div className="w-7 h-7 rounded-lg bg-primary text-white flex items-center justify-center flex-shrink-0">
                <Bot className="w-4 h-4" />
              </div>
              <div className="bg-slate-50 border border-border p-3.5 rounded-xl flex items-center gap-2 text-secondary">
                <div className="w-3.5 h-3.5 border-2 border-primary border-t-transparent rounded-full animate-spin"></div>
                <span>Executing authorized backend tools & synthesizing response...</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar */}
        <div className="p-4 border-t border-border bg-slate-50/30">
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
              placeholder="Ask AttendAI a question about attendance, policies, or anomalies..."
              disabled={loading}
              className="flex-1 px-4 py-2.5 bg-white border border-border rounded-xl text-xs text-dark focus:outline-none focus:ring-1 focus:ring-primary shadow-sm disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="p-2.5 bg-primary text-white rounded-xl hover:bg-primary-hover shadow-sm transition-colors disabled:opacity-50 flex items-center justify-center"
            >
              <Send className="w-4 h-4" />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};
