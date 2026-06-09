"use client"

import { useEffect, useState } from "react"
import { motion } from "framer-motion"
import { GitBranch, FileCode, MessageSquare, Zap } from "lucide-react"
import { Card } from "@/components/ui/card"
import { formatNumber } from "@/lib/utils"
import { getRepos } from "@/lib/api"
import type { Repository } from "@/lib/types"

interface StatCardProps {
  title: string
  value: number
  icon: React.ReactNode
  delay?: number
}

function StatCard({ title, value, icon, delay = 0 }: StatCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay }}
    >
      <Card className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-slate-400">{title}</p>
            <p className="mt-1 text-3xl font-bold text-slate-100">
              {formatNumber(value)}
            </p>
          </div>
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-cyan-500/10 text-cyan-400">
            {icon}
          </div>
        </div>
      </Card>
    </motion.div>
  )
}

export function StatsCards() {
  const [repos, setRepos] = useState<Repository[]>([])

  useEffect(() => {
    getRepos().then(setRepos).catch(() => {})
  }, [])

  const totalFiles = repos.reduce((sum, r) => sum + (r.file_count || 0), 0)

  const stats = [
    {
      title: "Total Repos",
      value: repos.length,
      icon: <GitBranch className="h-6 w-6" />,
    },
    {
      title: "Files Analyzed",
      value: totalFiles,
      icon: <FileCode className="h-6 w-6" />,
    },
    {
      title: "Queries Made",
      value: 0,
      icon: <MessageSquare className="h-6 w-6" />,
    },
    {
      title: "Active Sessions",
      value: 1,
      icon: <Zap className="h-6 w-6" />,
    },
  ]

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {stats.map((stat, i) => (
        <StatCard key={stat.title} {...stat} delay={i * 0.1} />
      ))}
    </div>
  )
}
