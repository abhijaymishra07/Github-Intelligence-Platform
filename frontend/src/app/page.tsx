"use client"

import { motion } from "framer-motion"
import Link from "next/link"
import { Plus, MessageSquare, BarChart3, Sparkles } from "lucide-react"
import { Button } from "@/components/ui/button"
import { StatsCards } from "@/components/dashboard/stats-cards"
import { RecentRepos } from "@/components/dashboard/recent-repos"

export default function DashboardPage() {
  return (
    <div className="space-y-8">
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
      >
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-100">
              Welcome back
            </h1>
            <p className="mt-1 text-slate-400">
              Your AI-powered GitHub intelligence platform. Analyze repos, ask
              questions, and discover insights.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Link href="/repositories">
              <Button variant="primary" className="gap-2">
                <Plus className="h-4 w-4" />
                Add Repository
              </Button>
            </Link>
          </div>
        </div>
      </motion.div>

      <StatsCards />

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <RecentRepos />
        </div>
        <div className="space-y-4">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.5 }}
          >
            <h2 className="text-lg font-semibold text-slate-100 mb-4">
              Quick Actions
            </h2>
            <div className="space-y-3">
              <Link href="/repositories" className="block">
                <div className="flex items-center gap-3 rounded-xl border border-slate-800 bg-slate-900/50 p-4 transition-all hover:border-cyan-500/30 hover:bg-slate-900 cursor-pointer group">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-cyan-500/10 text-cyan-400 group-hover:bg-cyan-500/20 transition-colors">
                    <Plus className="h-5 w-5" />
                  </div>
                  <div>
                    <p className="font-medium text-slate-200">Add Repository</p>
                    <p className="text-xs text-slate-500">
                      Ingest a new GitHub repo
                    </p>
                  </div>
                </div>
              </Link>
              <div className="flex items-center gap-3 rounded-xl border border-slate-800 bg-slate-900/50 p-4 transition-all hover:border-cyan-500/30 hover:bg-slate-900 cursor-pointer group">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-500/10 text-blue-400 group-hover:bg-blue-500/20 transition-colors">
                  <MessageSquare className="h-5 w-5" />
                </div>
                <div>
                  <p className="font-medium text-slate-200">Start Chat</p>
                  <p className="text-xs text-slate-500">
                    Ask questions about your code
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3 rounded-xl border border-slate-800 bg-slate-900/50 p-4 transition-all hover:border-cyan-500/30 hover:bg-slate-900 cursor-pointer group">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-purple-500/10 text-purple-400 group-hover:bg-purple-500/20 transition-colors">
                  <BarChart3 className="h-5 w-5" />
                </div>
                <div>
                  <p className="font-medium text-slate-200">View Analytics</p>
                  <p className="text-xs text-slate-500">
                    Explore repository insights
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3 rounded-xl border border-slate-800 bg-slate-900/50 p-4 transition-all hover:border-cyan-500/30 hover:bg-slate-900 cursor-pointer group">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-amber-500/10 text-amber-400 group-hover:bg-amber-500/20 transition-colors">
                  <Sparkles className="h-5 w-5" />
                </div>
                <div>
                  <p className="font-medium text-slate-200">AI Insights</p>
                  <p className="text-xs text-slate-500">
                    Auto-generated code summaries
                  </p>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  )
}
