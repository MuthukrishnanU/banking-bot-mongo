"use client";

import { useState, useEffect } from "react";
import { Activity, ArrowLeft, Loader2, Database } from "lucide-react";
import axios from "axios";

const API_BASE_URL = "http://localhost:8000";

interface UsageData {
  _id: string;
  userId?: string;
  query: string;
  tokens: number;
  timestamp: number;
}

export default function TrackerPage() {
  const [usage, setUsage] = useState<UsageData[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchUsage();
  }, []);

  const fetchUsage = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/usage`);
      setUsage(response.data);
    } catch (error) {
      console.error("Error fetching usage data:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const totalTokens = usage.reduce((acc, curr) => acc + (curr.tokens || 0), 0);

  return (
    <div className="min-h-screen bg-slate-950 text-white font-sans p-8 md:p-12">
      <div className="max-w-6xl mx-auto space-y-10">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-indigo-600 rounded-2xl flex items-center justify-center shadow-lg shadow-indigo-500/20">
              <Activity className="w-7 h-7 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold tracking-tight">Token Usage Tracker</h1>
              <p className="text-slate-400 font-medium uppercase tracking-wider text-xs">Analytics Dashboard</p>
            </div>
          </div>
          <button 
            onClick={() => window.close()}
            className="flex items-center gap-2 text-slate-400 hover:text-white transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Chat
          </button>
        </div>

        {/* Stats Card */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-slate-900 border border-white/5 p-6 rounded-3xl shadow-xl">
            <p className="text-slate-400 text-sm font-medium mb-1">Total Queries</p>
            <p className="text-3xl font-bold text-white">{usage.length}</p>
          </div>
          <div className="bg-slate-900 border border-white/5 p-6 rounded-3xl shadow-xl">
            <p className="text-slate-400 text-sm font-medium mb-1">Total Tokens Consumed</p>
            <p className="text-3xl font-bold text-indigo-400">{totalTokens.toLocaleString()}</p>
          </div>
          <div className="bg-slate-900 border border-white/5 p-6 rounded-3xl shadow-xl">
            <p className="text-slate-400 text-sm font-medium mb-1">Avg Tokens / Query</p>
            <p className="text-3xl font-bold text-white">
              {usage.length > 0 ? Math.round(totalTokens / usage.length) : 0}
            </p>
          </div>
        </div>

        {/* Table */}
        <div className="bg-slate-900 border border-white/5 rounded-3xl overflow-hidden shadow-2xl">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-white/5">
                  <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-400 border-b border-white/5">ID</th>
                  <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-400 border-b border-white/5">User ID</th>
                  <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-400 border-b border-white/5">Query</th>
                  <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-400 border-b border-white/5">Timestamp</th>
                  <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-400 border-b border-white/5 text-right">Tokens Used</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {isLoading ? (
                  <tr>
                    <td colSpan={5} className="px-6 py-20 text-center text-slate-500">
                      <div className="flex flex-col items-center gap-3">
                        <Loader2 className="w-8 h-8 animate-spin text-indigo-500" />
                        <p className="font-medium">Loading usage analytics...</p>
                      </div>
                    </td>
                  </tr>
                ) : usage.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-6 py-20 text-center text-slate-500">
                      <div className="flex flex-col items-center gap-3">
                        <Database className="w-8 h-8 opacity-20" />
                        <p className="font-medium">No usage data found in semantic cache.</p>
                      </div>
                    </td>
                  </tr>
                ) : (
                  <>
                    {usage.map((item) => (
                      <tr key={item._id} className="hover:bg-white/[0.02] transition-colors group">
                        <td className="px-6 py-4 font-mono text-[10px] text-slate-500 group-hover:text-slate-400">
                          {item._id}
                        </td>
                        <td className="px-6 py-4 text-sm font-medium text-slate-300">
                          {item.userId || "NA"}
                        </td>
                        <td className="px-6 py-4 text-sm font-medium text-slate-200">
                          {item.query || "NA"}
                        </td>
                        <td className="px-6 py-4 text-sm text-slate-400">
                          {item.timestamp 
                            ? new Date(item.timestamp * 1000).toLocaleString() 
                            : "NA"}
                        </td>
                        <td className="px-6 py-4 text-sm font-bold text-right text-indigo-400">
                          {item.tokens !== undefined ? item.tokens.toLocaleString() : "NA"}
                        </td>
                      </tr>
                    ))}
                    <tr className="bg-indigo-600/5 font-bold">
                      <td colSpan={4} className="px-6 py-5 text-sm text-white uppercase tracking-wider">
                        Total Tokens
                      </td>
                      <td className="px-6 py-5 text-lg text-right text-indigo-400">
                        {totalTokens.toLocaleString()}
                      </td>
                    </tr>
                  </>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
