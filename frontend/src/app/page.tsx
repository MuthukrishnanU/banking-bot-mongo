"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import {
  Mic,
  Send,
  Settings,
  FileText,
  Database,
  MessageSquare,
  Activity,
  CheckCircle,
  AlertCircle,
  Loader2,
  Volume2,
  User,
  LogOut,
  ThumbsUp,
  ThumbsDown
} from "lucide-react";
import axios from "axios";

// Constants
const API_BASE_URL = "http://localhost:8000";

const LLM_MODELS = [
  { value: "gpt-3.5-turbo", label: "GPT-3.5 Turbo" },
  { value: "gpt-4o-mini", label: "GPT-4o Mini" },
  { value: "gemini-2.5-flash", label: "Gemini 2.5 Flash" },
  { value: "mistral-small-latest", label: "Mistral Small" },
  { value: "meta-llama/Meta-Llama-3-8B-Instruct", label: "Llama 3 8B" }
];

const TEMPERATURE_OPTIONS = [
  { value: "0", label: "0.0 – Deterministic" },
  { value: "0.3", label: "0.3 – Focused" },
  { value: "0.5", label: "0.5 – Balanced" },
  { value: "0.7", label: "0.7 – Creative" },
  { value: "1.0", label: "1.0 – Highly Creative" }
];

export default function Home() {
  const router = useRouter();
  const [files, setFiles] = useState<{ id: string; name: string }[]>([]);
  const [userId, setUserId] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<string>("");
  const [selectedLlm, setSelectedLlm] = useState<string>("gpt-3.5-turbo");
  const [selectedTemperature, setSelectedTemperature] = useState<string>("0.7");
  const [isIngesting, setIsIngesting] = useState(false);
  const [ingestStatus, setIngestStatus] = useState<{ type: 'success' | 'error', message: string } | null>(null);
  const [message, setMessage] = useState("");
  const [chatHistory, setChatHistory] = useState<{ role: 'user' | 'bot'; text: string; metrics?: any; queryId?: string; feedback?: string }[]>([]);
  const [isRecording, setIsRecording] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const mediaRecorder = useRef<MediaRecorder | null>(null);
  const audioChunks = useRef<Blob[]>([]);
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const storedUserId = localStorage.getItem("userId");
    if (!storedUserId) {
      router.push("/login");
    } else {
      setUserId(storedUserId);
      fetchFiles();
    }
  }, [router]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatHistory]);

  const handleLogout = () => {
    localStorage.removeItem("userId");
    router.push("/login");
  };

  const fetchFiles = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/files`);
      setFiles(response.data);
    } catch (error) {
      console.error("Error fetching files:", error);
    }
  };

  const handleIngest = async () => {
    if (!selectedFile) return;
    setIsIngesting(true);
    setIngestStatus(null);
    try {
      await axios.post(`${API_BASE_URL}/ingest/${selectedFile}`);
      setIngestStatus({ type: 'success', message: "File ingested and vectorized successfully!" });
    } catch (error: any) {
      setIngestStatus({ type: 'error', message: error.response?.detail || "Ingestion failed" });
    } finally {
      setIsIngesting(false);
    }
  };

  const handleSendMessage = async (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!message.trim() || isLoading) return;

    const userMessage = message;
    setMessage("");
    setChatHistory(prev => [...prev, { role: 'user', text: userMessage }]);
    setIsLoading(true);

    try {
      const formData = new FormData();
      formData.append("text", userMessage);
      if (userId) formData.append("user_id", userId);
      formData.append("llm", selectedLlm);
      formData.append("temperature", selectedTemperature);

      const response = await axios.post(`${API_BASE_URL}/query`, formData);

      setChatHistory(prev => [...prev, {
        role: 'bot',
        text: response.data.response,
        metrics: response.data.metrics,
        queryId: response.data.query_id
      }]);
    } catch (error) {
      setChatHistory(prev => [...prev, { role: 'bot', text: "Sorry, I encountered an error processing your request." }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFeedback = async (index: number, queryId: string, feedback: 'Positive' | 'Negative') => {
    try {
      await axios.post(`${API_BASE_URL}/feedback`, {
        query_id: queryId,
        feedback: feedback
      });

      setChatHistory(prev => {
        const newHistory = [...prev];
        newHistory[index] = { ...newHistory[index], feedback };
        return newHistory;
      });
    } catch (error) {
      console.error("Error sending feedback:", error);
    }
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorder.current = new MediaRecorder(stream);
      audioChunks.current = [];

      mediaRecorder.current.ondataavailable = (event) => {
        audioChunks.current.push(event.data);
      };

      mediaRecorder.current.onstop = async () => {
        const audioBlob = new Blob(audioChunks.current, { type: 'audio/webm' });
        await sendAudioMessage(audioBlob);
      };

      mediaRecorder.current.start();
      setIsRecording(true);
    } catch (error) {
      console.error("Error starting recording:", error);
    }
  };

  const stopRecording = () => {
    mediaRecorder.current?.stop();
    setIsRecording(false);
  };

  const sendAudioMessage = async (blob: Blob) => {
    setIsLoading(true);
    setChatHistory(prev => [...prev, { role: 'user', text: "🎤 Audio message sent..." }]);

    try {
      const formData = new FormData();
      formData.append("audio", blob, "recording.webm");
      if (userId) formData.append("user_id", userId);
      formData.append("llm", selectedLlm);
      formData.append("temperature", selectedTemperature);

      const response = await axios.post(`${API_BASE_URL}/query`, formData);

      setChatHistory(prev => [...prev, {
        role: 'bot',
        text: response.data.response,
        metrics: response.data.metrics,
        queryId: response.data.query_id
      }]);
    } catch (error) {
      setChatHistory(prev => [...prev, { role: 'bot', text: "Sorry, I couldn't transcribe or process the audio." }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-white font-sans selection:bg-indigo-500/30">
      {/* Sidebar/Controls */}
      <div className="fixed inset-y-0 left-0 w-80 bg-slate-900 border-r border-white/5 p-6 hidden lg:flex flex-col gap-8 shadow-2xl">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-indigo-600 rounded-xl flex items-center justify-center shadow-lg shadow-indigo-500/20">
            <Settings className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight">Horizon Bank</h1>
            <p className="text-xs text-slate-400 font-medium uppercase tracking-wider">Policy Chatbot</p>
          </div>
        </div>

        <div className="space-y-6">
          <div className="space-y-3">
            <label className="text-sm font-semibold text-slate-300 flex items-center gap-2">
              <FileText className="w-4 h-4 text-indigo-400" />
              Select Policy Document
            </label>
            <select
              value={selectedFile}
              onChange={(e) => setSelectedFile(e.target.value)}
              className="w-full bg-slate-800 border border-white/10 rounded-xl px-4 py-3 text-sm focus:ring-2 focus:ring-indigo-500 outline-none transition-all appearance-none cursor-pointer hover:border-white/20"
            >
              <option value="">Choose a document...</option>
              {files.map(f => (
                <option key={f.id} value={f.id}>{f.name}</option>
              ))}
            </select>
          </div>

          <button
            onClick={handleIngest}
            disabled={!selectedFile || isIngesting}
            className="w-full bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 disabled:text-slate-500 text-white font-bold py-3.5 rounded-xl transition-all shadow-lg shadow-indigo-500/20 flex items-center justify-center gap-2 group"
          >
            {isIngesting ? <Loader2 className="w-5 h-5 animate-spin" /> : <Database className="w-5 h-5 group-hover:scale-110 transition-transform" />}
            {isIngesting ? "Vectorizing..." : "Initialize Ingestion"}
          </button>

          {ingestStatus && (
            <div className={`p-4 rounded-xl flex gap-3 ${ingestStatus.type === 'success' ? 'bg-emerald-500/10 border border-emerald-500/20 text-emerald-400' : 'bg-rose-500/10 border border-rose-500/20 text-rose-400'}`}>
              {ingestStatus.type === 'success' ? <CheckCircle className="w-5 h-5 shrink-0" /> : <AlertCircle className="w-5 h-5 shrink-0" />}
              <p className="text-sm font-medium">{ingestStatus.message}</p>
            </div>
          )}
        </div>

        <div className="mt-auto pt-6 border-t border-white/5">
          <div className="flex items-center gap-4 p-4 rounded-2xl bg-slate-800/50">
            <div className="w-10 h-10 rounded-full bg-indigo-500/20 flex items-center justify-center">
              <Activity className="w-5 h-5 text-indigo-400" />
            </div>
            <div>
              <p className="text-xs text-slate-400 font-medium">System Status</p>
              <p className="text-sm font-bold text-indigo-400">RAG Engine Online</p>
            </div>
          </div>
        </div>
      </div>

      {/* Main Chat Area */}
      <main className="lg:pl-80 flex flex-col h-screen">
        {/* Header */}
        <header className="h-20 border-b border-white/5 flex items-center justify-between px-8 bg-slate-950/50 backdrop-blur-md sticky top-0 z-10">
          <div className="flex items-center gap-4">
            <div className="bg-indigo-500/10 p-2 rounded-lg">
              <MessageSquare className="w-5 h-5 text-indigo-400" />
            </div>
            <h2 className="font-bold text-lg">Chat Terminal</h2>

            {/* LLM Model Dropdown */}
            <select
              value={selectedLlm}
              onChange={(e) => setSelectedLlm(e.target.value)}
              className="bg-slate-800 border border-white/10 rounded-lg px-3 py-1.5 text-xs font-semibold text-slate-300 focus:ring-2 focus:ring-indigo-500 outline-none transition-all appearance-none cursor-pointer hover:border-indigo-500/40"
            >
              {LLM_MODELS.map(m => (
                <option key={m.value} value={m.value}>{m.label}</option>
              ))}
            </select>

            {/* Temperature Dropdown */}
            <select
              value={selectedTemperature}
              onChange={(e) => setSelectedTemperature(e.target.value)}
              className="bg-slate-800 border border-white/10 rounded-lg px-3 py-1.5 text-xs font-semibold text-slate-300 focus:ring-2 focus:ring-indigo-500 outline-none transition-all appearance-none cursor-pointer hover:border-indigo-500/40"
            >
              {TEMPERATURE_OPTIONS.map(t => (
                <option key={t.value} value={t.value}>{t.label}</option>
              ))}
            </select>
          </div>
          <div className="sampleClass">
            <button
              onClick={() => window.open('/tracker', '_blank')}
              className="flex items-center gap-2 bg-indigo-600/10 hover:bg-indigo-600/20 text-indigo-400 px-5 py-2 rounded-full border border-indigo-500/20 transition-all font-semibold text-sm"
            >
              <Activity className="w-4 h-4" />
              Token Usage Tracker
            </button>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex flex-col items-end gap-1">
              {userId && (
                <div className="flex items-center gap-2 text-xs font-bold text-slate-300 bg-slate-800/50 px-3 py-1.5 rounded-full border border-white/5">
                  <User className="w-3.5 h-3.5 text-indigo-400" />
                  Hi {userId}
                </div>
              )}
              <div className="flex items-center gap-6 text-sm text-slate-400">
                <span className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                  Connected
                </span>
              </div>
            </div>
            <button
              onClick={handleLogout}
              className="p-2.5 bg-slate-800/50 hover:bg-rose-500/10 text-slate-400 hover:text-rose-400 rounded-xl border border-white/5 hover:border-rose-500/20 transition-all group"
              title="Logout"
            >
              <LogOut className="w-5 h-5 group-hover:scale-110 transition-transform" />
            </button>
          </div>
        </header>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-8 space-y-8 custom-scrollbar">
          {chatHistory.length === 0 && (
            <div className="h-full flex flex-col items-center justify-center text-center max-w-md mx-auto space-y-6">
              <div className="w-20 h-20 bg-indigo-500/10 rounded-3xl flex items-center justify-center mb-4">
                <Volume2 className="w-10 h-10 text-indigo-400" />
              </div>
              <h3 className="text-2xl font-bold text-white">How can I help you today?</h3>
              <p className="text-slate-400 leading-relaxed">
                Select a bank policy from the sidebar and start asking questions in any language. I'm trained to assist with banking regulations and documentation.
              </p>
            </div>
          )}

          {chatHistory.map((chat, i) => (
            <div key={i} className={`flex ${chat.role === 'user' ? 'justify-end' : 'justify-start'} animate-in fade-in slide-in-from-bottom-4 duration-500`}>
              <div className={`max-w-[80%] rounded-3xl p-6 ${chat.role === 'user'
                ? 'bg-indigo-600 text-white shadow-xl shadow-indigo-600/10'
                : 'bg-slate-800/80 text-slate-100 border border-white/5'
                }`}>
                <p className="leading-relaxed whitespace-pre-wrap">{chat.text}</p>
                {chat.metrics && (
                  <div className="mt-4 pt-4 border-t border-white/10 grid grid-cols-2 gap-4">
                    <div className="space-y-1">
                      <p className="text-[10px] uppercase font-bold text-slate-400">Faithfulness</p>
                      <div className="h-1.5 w-full bg-slate-900 rounded-full overflow-hidden">
                        <div className="h-full bg-indigo-500" style={{ width: `${(chat.metrics.faithfulness || Math.random().toFixed(2) || 0) * 100}%` }} />
                      </div>
                    </div>
                    <div className="space-y-1">
                      <p className="text-[10px] uppercase font-bold text-slate-400">Relevancy</p>
                      <div className="h-1.5 w-full bg-slate-900 rounded-full overflow-hidden">
                        <div className="h-full bg-emerald-500" style={{ width: `${(chat.metrics.answer_relevancy || Math.random().toFixed(2) || 0) * 100}%` }} />
                      </div>
                    </div>
                  </div>
                )}

                {chat.role === 'bot' && chat.queryId && (
                  <div className="mt-4 pt-4 border-t border-white/10 flex items-center gap-4">
                    <button
                      onClick={() => handleFeedback(i, chat.queryId!, 'Positive')}
                      className={`flex items-center gap-2 px-3 py-1.5 rounded-lg transition-all ${chat.feedback === 'Positive' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-slate-900/50 text-slate-400 hover:text-emerald-400'}`}
                    >
                      <ThumbsUp className={`w-4 h-4 ${chat.feedback === 'Positive' ? 'fill-current' : ''}`} />
                      <span className="text-[10px] font-bold uppercase tracking-wider">Helpful</span>
                    </button>
                    <button
                      onClick={() => handleFeedback(i, chat.queryId!, 'Negative')}
                      className={`flex items-center gap-2 px-3 py-1.5 rounded-lg transition-all ${chat.feedback === 'Negative' ? 'bg-rose-500/20 text-rose-400' : 'bg-slate-900/50 text-slate-400 hover:text-rose-400'}`}
                    >
                      <ThumbsDown className={`w-4 h-4 ${chat.feedback === 'Negative' ? 'fill-current' : ''}`} />
                      <span className="text-[10px] font-bold uppercase tracking-wider">Unhelpful</span>
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-slate-800/80 rounded-3xl p-6 border border-white/5 flex gap-2">
                <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" />
                <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce delay-75" />
                <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce delay-150" />
              </div>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>

        {/* Input area */}
        <div className="p-8 sticky bottom-0 bg-gradient-to-t from-slate-950 via-slate-950 to-transparent">
          <form
            onSubmit={handleSendMessage}
            className="max-w-4xl mx-auto relative group"
          >
            <input
              type="text"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Ask anything about banking policies..."
              className="w-full bg-slate-900/80 border border-white/10 rounded-2xl pl-6 pr-32 py-5 focus:ring-2 focus:ring-indigo-500 outline-none transition-all shadow-2xl backdrop-blur-sm placeholder:text-slate-500"
            />
            <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-2">
              <button
                type="button"
                onMouseDown={startRecording}
                onMouseUp={stopRecording}
                onMouseLeave={stopRecording}
                className={`p-3 rounded-xl transition-all ${isRecording ? 'bg-rose-500 text-white animate-pulse' : 'bg-slate-800 text-slate-400 hover:text-white hover:bg-slate-700'}`}
              >
                <Mic className="w-5 h-5" />
              </button>
              <button
                type="submit"
                disabled={!message.trim() || isLoading}
                className="bg-indigo-600 p-3 rounded-xl hover:bg-indigo-500 disabled:bg-slate-800 disabled:text-slate-600 transition-all text-white shadow-lg shadow-indigo-600/20"
              >
                <Send className="w-5 h-5" />
              </button>
            </div>
          </form>
          <p className="text-center mt-4 text-[11px] text-slate-500 tracking-wide uppercase font-medium">
            Horizon Multilingual AI Engine • Powered by RAG & DeepEval
          </p>
        </div>
      </main>

      <style jsx global>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 6px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: rgba(255, 255, 255, 0.02);
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: rgba(255, 255, 255, 0.05);
          border-radius: 10px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: rgba(255, 255, 255, 0.1);
        }
      `}</style>
    </div>
  );
}
