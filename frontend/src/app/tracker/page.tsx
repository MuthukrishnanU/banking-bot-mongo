"use client";

import { useState, useEffect, useMemo } from "react";
import { useRouter } from "next/navigation";
import {
  Activity,
  ArrowLeft,
  Loader2,
  Database,
  Calendar,
  Cpu,
  Tag,
  LayoutDashboard,
  PieChart as PieChartIcon
} from "lucide-react";
import axios from "axios";
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
  ResponsiveContainer
} from "recharts";

const API_BASE_URL = "http://localhost:8000";

interface UsageData {
  _id: string;
  userId?: string;
  query: string;
  tokens: number;
  timestamp: number;
  feedback?: string;
  model?: string;
  temperature?: number;
  latency?: number;
}

interface MonthlyData {
  month: string;
  tokens: number;
}

interface ModelData {
  model: string;
  count: number;
}

interface TopicData {
  topic: string;
  count: number;
}

const COLORS = ["#6366f1", "#10b981", "#f59e0b", "#ec4899", "#8b5cf6", "#06b6d4"];

type TabType = "tracker" | "monthly" | "llm" | "topics";

export default function TrackerPage() {
  const router = useRouter();
  const [userId, setUserId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<TabType>("tracker");
  const [isLoading, setIsLoading] = useState(false);

  // Data States
  const [usage, setUsage] = useState<UsageData[]>([]);
  const [monthlyUsage, setMonthlyUsage] = useState<MonthlyData[]>([]);
  const [modelUsage, setModelUsage] = useState<ModelData[]>([]);
  const [topicUsage, setTopicUsage] = useState<TopicData[]>([]);

  // Caching mechanism
  const [loadedTabs, setLoadedTabs] = useState<Set<TabType>>(new Set());

  useEffect(() => {
    const storedUserId = localStorage.getItem("userId");
    if (!storedUserId) {
      router.push("/login");
    } else {
      setUserId(storedUserId);
    }
  }, [router]);

  useEffect(() => {
    if (userId && !loadedTabs.has(activeTab)) {
      fetchData(activeTab);
    }
  }, [activeTab, userId]);

  const fetchData = async (tab: TabType) => {
    if (!userId) return;
    setIsLoading(true);
    try {
      let endpoint = "";
      switch (tab) {
        case "tracker":
          endpoint = `${API_BASE_URL}/usage?userId=${userId}`;
          const resTracker = await axios.get(endpoint);
          setUsage(resTracker.data);
          break;
        case "monthly":
          endpoint = `${API_BASE_URL}/usage/monthly?userId=${userId}`;
          const resMonthly = await axios.get(endpoint);
          setMonthlyUsage(resMonthly.data);
          break;
        case "llm":
          endpoint = `${API_BASE_URL}/usage/models?userId=${userId}`;
          const resModels = await axios.get(endpoint);
          setModelUsage(resModels.data);
          break;
        case "topics":
          endpoint = `${API_BASE_URL}/usage/topics?userId=${userId}`;
          const resTopics = await axios.get(endpoint);
          setTopicUsage(resTopics.data);
          break;
      }
      setLoadedTabs(prev => new Set(prev).add(tab));
    } catch (error) {
      console.error(`Error fetching ${tab} data:`, error);
    } finally {
      setIsLoading(false);
    }
  };

  const totalTokens = useMemo(() => usage.reduce((acc, curr) => acc + (curr.tokens || 0), 0), [usage]);

  const renderContent = () => {
    if (isLoading && !loadedTabs.has(activeTab)) {
      return (
        <div className="flex flex-col items-center justify-center py-32 animate-in fade-in duration-500">
          <Loader2 className="w-12 h-12 animate-spin text-indigo-500 mb-4" />
          <p className="text-slate-400 font-medium">Analyzing data patterns...</p>
        </div>
      );
    }

    switch (activeTab) {
      case "tracker":
        return (
          <div className="space-y-8 animate-in slide-in-from-bottom-4 duration-500">
            {/* Stats Overview */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-slate-900/50 backdrop-blur-xl border border-white/5 p-6 rounded-3xl shadow-xl">
                <p className="text-slate-400 text-sm font-medium mb-1">Total Queries</p>
                <p className="text-3xl font-bold text-white">{usage.length}</p>
              </div>
              <div className="bg-slate-900/50 backdrop-blur-xl border border-white/5 p-6 rounded-3xl shadow-xl">
                <p className="text-slate-400 text-sm font-medium mb-1">Total Tokens Consumed</p>
                <p className="text-3xl font-bold text-indigo-400">{totalTokens.toLocaleString()}</p>
              </div>
              <div className="bg-slate-900/50 backdrop-blur-xl border border-white/5 p-6 rounded-3xl shadow-xl">
                <p className="text-slate-400 text-sm font-medium mb-1">Avg Tokens / Query</p>
                <p className="text-3xl font-bold text-white">
                  {usage.length > 0 ? Math.round(totalTokens / usage.length) : 0}
                </p>
              </div>
            </div>

            {/* Table */}
            <div className="bg-slate-900/50 backdrop-blur-xl border border-white/5 rounded-3xl overflow-hidden shadow-2xl">
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-white/5">
                      <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-400">Query ID</th>
                      <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-400">Query</th>
                      <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-400">Timestamp</th>
                      <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-400">Model</th>
                      <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-400">Temperature</th>
                      <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-400 text-right">Tokens</th>
                      <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-400">Latency</th>
                      <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-400 text-center">Feedback</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5">
                    {usage.length === 0 ? (
                      <tr>
                        <td colSpan={5} className="px-6 py-20 text-center text-slate-500 italic">No data available</td>
                      </tr>
                    ) : (
                      usage.map((item) => (
                        <tr key={item._id} className="hover:bg-white/[0.02] transition-colors group">
                          <td className="px-6 py-4 text-sm font-medium text-slate-200 max-w-md truncate">
                            {item._id}
                          </td>
                          <td className="px-6 py-4 text-sm font-medium text-slate-200 max-w-md truncate">
                            {item.query}
                          </td>
                          <td className="px-6 py-4 text-sm text-slate-400">
                            {new Date(item.timestamp * 1000).toLocaleString()}
                          </td>
                          <td className="px-6 py-4 text-sm text-slate-300">
                            {item.model}
                          </td>
                          <td className="px-6 py-4 text-sm text-slate-300 text-center">
                            {item.temperature}
                          </td>
                          <td className="px-6 py-4 text-sm font-bold text-center text-indigo-400">
                            {item.tokens.toLocaleString()}
                          </td>
                          <td className="px-6 py-4 text-sm text-slate-300 text-center">
                            {item.latency?.toFixed(2)}s
                          </td>
                          <td className="px-6 py-4 text-sm text-center">
                            <span className={`px-2 py-1 rounded-full text-[10px] font-bold ${item.feedback === 'Positive' ? 'bg-emerald-500/10 text-emerald-400' : item.feedback === 'Negative' ? 'bg-rose-500/10 text-rose-400' : 'bg-slate-800 text-slate-500'}`}>
                              {item.feedback || "NA"}
                            </span>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        );

      case "monthly":
        return (
          <div className="max-w-3xl mx-auto animate-in slide-in-from-bottom-4 duration-500">
            <div className="bg-slate-900/50 backdrop-blur-xl border border-white/5 rounded-3xl overflow-hidden shadow-2xl">
              <div className="px-8 py-6 border-b border-white/5 bg-white/5">
                <h3 className="text-xl font-bold flex items-center gap-2">
                  <Calendar className="w-5 h-5 text-indigo-400" />
                  Monthly Token Consumption
                </h3>
              </div>
              <table className="w-full text-left">
                <thead>
                  <tr className="bg-white/2">
                    <th className="px-8 py-4 text-xs font-bold uppercase tracking-wider text-slate-400">Month</th>
                    <th className="px-8 py-4 text-xs font-bold uppercase tracking-wider text-slate-400 text-right">Tokens Used</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {monthlyUsage.length === 0 ? (
                    <tr><td colSpan={2} className="px-8 py-12 text-center text-slate-500 italic">No monthly data found</td></tr>
                  ) : (
                    monthlyUsage.map((data, i) => (
                      <tr key={i} className="hover:bg-white/[0.02] transition-colors">
                        <td className="px-8 py-5 text-lg font-medium text-slate-200">{data.month}</td>
                        <td className="px-8 py-5 text-2xl font-bold text-right text-indigo-400">{data.tokens.toLocaleString()}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        );

      case "llm":
        return (
          <div className="max-w-4xl mx-auto animate-in slide-in-from-bottom-4 duration-500">
            <div className="bg-slate-900/50 backdrop-blur-xl border border-white/5 rounded-3xl p-8 shadow-2xl">
              <div className="text-center mb-8">
                <h3 className="text-2xl font-bold text-white mb-2">Most Interacted LLM</h3>
                <p className="text-slate-400">Top 3 models you've used for your queries</p>
              </div>

              <div className="h-[400px] w-full">
                {modelUsage.length > 0 ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={modelUsage}
                        cx="50%"
                        cy="50%"
                        innerRadius={80}
                        outerRadius={140}
                        paddingAngle={5}
                        dataKey="count"
                        nameKey="model"
                      >
                        {modelUsage.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip
                        contentStyle={{ backgroundColor: '#0f172a', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px', color: '#fff' }}
                        itemStyle={{ color: '#fff' }}
                      />
                      <Legend verticalAlign="bottom" height={36} />
                    </PieChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="h-full flex items-center justify-center text-slate-500 italic">No model usage data available</div>
                )}
              </div>
            </div>
          </div>
        );

      case "topics":
        return (
          <div className="max-w-4xl mx-auto animate-in slide-in-from-bottom-4 duration-500">
            <div className="bg-slate-900/50 backdrop-blur-xl border border-white/5 rounded-3xl p-8 shadow-2xl">
              <div className="text-center mb-8">
                <h3 className="text-2xl font-bold text-white mb-2">Most Queried Topic</h3>
                <p className="text-slate-400">The core topics analyzed from your document queries</p>
              </div>

              <div className="h-[400px] w-full">
                {topicUsage.length > 0 ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={topicUsage}
                        cx="50%"
                        cy="50%"
                        innerRadius={80}
                        outerRadius={140}
                        paddingAngle={5}
                        dataKey="count"
                        nameKey="topic"
                      >
                        {topicUsage.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[(index + 3) % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip
                        contentStyle={{ backgroundColor: '#0f172a', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px', color: '#fff' }}
                        itemStyle={{ color: '#fff' }}
                      />
                      <Legend verticalAlign="bottom" height={36} />
                    </PieChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="h-full flex items-center justify-center text-slate-500 italic">No topic usage data available</div>
                )}
              </div>
            </div>
          </div>
        );
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-white font-sans p-6 md:p-12 selection:bg-indigo-500/30">
      <div className="max-w-7xl mx-auto space-y-12">

        {/* Header & Nav */}
        <div className="space-y-8">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div className="flex items-center gap-5">
              <div className="w-14 h-14 bg-gradient-to-br from-indigo-600 to-violet-700 rounded-2xl flex items-center justify-center shadow-2xl shadow-indigo-500/20">
                <Activity className="w-8 h-8 text-white" />
              </div>
              <div>
                <h1 className="text-4xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white to-slate-400">Usage Analytics for User ID - {userId}</h1>
                <p className="text-indigo-400 font-bold uppercase tracking-widest text-[10px]">Horizon Intelligent Token Tracker</p>
              </div>
            </div>

            <button
              onClick={() => router.push("/")}
              className="flex items-center gap-2 bg-white/5 hover:bg-white/10 text-slate-300 hover:text-white px-6 py-3 rounded-2xl border border-white/10 transition-all font-semibold shadow-lg backdrop-blur-sm"
            >
              <ArrowLeft className="w-4 h-4" />
              Back to Chat
            </button>
          </div>

          {/* Navigation Links */}
          <nav className="flex flex-wrap items-center gap-2 p-2 bg-slate-900/50 backdrop-blur-md rounded-2xl border border-white/5 shadow-inner">
            <button
              onClick={() => setActiveTab("tracker")}
              className={`flex items-center gap-2 px-6 py-3 rounded-xl text-sm font-bold transition-all ${activeTab === 'tracker' ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/20' : 'text-slate-400 hover:text-white hover:bg-white/5'}`}
            >
              <LayoutDashboard className="w-4 h-4" />
              Token Usage Tracker
            </button>
            <button
              onClick={() => setActiveTab("monthly")}
              className={`flex items-center gap-2 px-6 py-3 rounded-xl text-sm font-bold transition-all ${activeTab === 'monthly' ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/20' : 'text-slate-400 hover:text-white hover:bg-white/5'}`}
            >
              <Calendar className="w-4 h-4" />
              Month-wise Consumption
            </button>
            <button
              onClick={() => setActiveTab("llm")}
              className={`flex items-center gap-2 px-6 py-3 rounded-xl text-sm font-bold transition-all ${activeTab === 'llm' ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/20' : 'text-slate-400 hover:text-white hover:bg-white/5'}`}
            >
              <Cpu className="w-4 h-4" />
              Most Interacted LLM
            </button>
            <button
              onClick={() => setActiveTab("topics")}
              className={`flex items-center gap-2 px-6 py-3 rounded-xl text-sm font-bold transition-all ${activeTab === 'topics' ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/20' : 'text-slate-400 hover:text-white hover:bg-white/5'}`}
            >
              <PieChartIcon className="w-4 h-4" />
              Most Queried Topic
            </button>
          </nav>
        </div>

        {/* Dynamic Content */}
        <div className="min-h-[500px]">
          {renderContent()}
        </div>

        {/* Footer info */}
        <div className="pt-12 border-t border-white/5 flex flex-col md:flex-row justify-between items-center gap-4 text-[11px] text-slate-500 font-bold uppercase tracking-widest">
          <p>© 2026 Horizon Banking AI • Internal Analytics Engine</p>
          <div className="flex items-center gap-6">
            <span className="flex items-center gap-2"><div className="w-2 h-2 rounded-full bg-indigo-500" /> Real-time Sync</span>
            <span className="flex items-center gap-2"><div className="w-2 h-2 rounded-full bg-emerald-500" /> MongoDB Atlas Secured</span>
          </div>
        </div>
      </div>
    </div>
  );
}
