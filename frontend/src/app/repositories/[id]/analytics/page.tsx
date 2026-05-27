"use client"

import { useEffect, useState } from "react"
import { useParams } from "next/navigation"
import Link from "next/link"
import { motion } from "framer-motion"
import { ArrowLeft, BarChart3, AlertTriangle, Shield, FileCode2, TrendingUp, Layers } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Spinner } from "@/components/ui/loading"
import { getRepoStatus, getRepoFiles } from "@/lib/api"
import type { Repository, RepoFile } from "@/lib/types"

export default function AnalyticsPage() {
  const params = useParams()
  const repoId = params.id as string
  const [repo, setRepo] = useState<Repository | null>(null)
  const [files, setFiles] = useState<RepoFile[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      getRepoStatus(repoId).catch(() => null),
      getRepoFiles(repoId).catch(() => []),
    ]).then(([r, f]) => {
      setRepo(r)
      setFiles(f)
      setLoading(false)
    })
  }, [repoId])

  if (loading) {
    return (
      <div className="flex justify-center py-20">
        <Spinner size="lg" />
      </div>
    )
  }

  const languageStats = files.reduce<Record<string, number>>((acc, f) => {
    const lang = f.language || "Other"
    acc[lang] = (acc[lang] || 0) + 1
    return acc
  }, {})

  const sortedLanguages = Object.entries(languageStats).sort(([, a], [, b]) => b - a)
  const totalSize = files.reduce((sum, f) => sum + f.size, 0)
  const avgFileSize = files.length > 0 ? totalSize / files.length : 0
  const largeFiles = files.filter((f) => f.size > 5000).sort((a, b) => b.size - a.size).slice(0, 10)

  const extStats = files.reduce<Record<string, number>>((acc, f) => {
    const ext = f.extension || "none"
    acc[ext] = (acc[ext] || 0) + 1
    return acc
  }, {})

  return (
    <div className="space-y-6">
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
        <Link href={`/repositories/${repoId}`}>
          <Button variant="ghost" size="sm" className="mb-2">
            <ArrowLeft className="mr-2 h-4 w-4" /> Back
          </Button>
        </Link>
        <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
          <BarChart3 className="h-6 w-6 text-cyan-400" />
          Analytics
        </h1>
        <p className="text-slate-400">{repo?.name} - Code insights & metrics</p>
      </motion.div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[
          { label: "Total Files", value: String(files.length), icon: FileCode2, color: "text-cyan-400" },
          { label: "Total Size", value: `${(totalSize / 1024).toFixed(1)} KB`, icon: Layers, color: "text-violet-400" },
          { label: "Avg File Size", value: `${(avgFileSize / 1024).toFixed(1)} KB`, icon: TrendingUp, color: "text-emerald-400" },
          { label: "Large Files", value: String(largeFiles.length), icon: AlertTriangle, color: "text-amber-400" },
        ].map((stat, i) => (
          <motion.div key={stat.label} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.1 }}>
            <Card>
              <CardContent className="flex items-center gap-3 p-4">
                <stat.icon className={`h-8 w-8 ${stat.color}`} />
                <div>
                  <p className="text-xs text-slate-500">{stat.label}</p>
                  <p className="text-xl font-bold text-slate-200">{stat.value}</p>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileCode2 className="h-5 w-5 text-cyan-400" />
              Language Distribution
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {sortedLanguages.map(([lang, count]) => {
                const pct = ((count / files.length) * 100).toFixed(1)
                return (
                  <div key={lang}>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm text-slate-300">{lang}</span>
                      <span className="text-xs text-slate-500">{count} files ({pct}%)</span>
                    </div>
                    <div className="h-2 rounded-full bg-slate-800 overflow-hidden">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${pct}%` }}
                        transition={{ duration: 0.8, delay: 0.2 }}
                        className="h-full rounded-full bg-gradient-to-r from-cyan-500 to-blue-500"
                      />
                    </div>
                  </div>
                )
              })}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-amber-400" />
              Large Files
            </CardTitle>
          </CardHeader>
          <CardContent>
            {largeFiles.length === 0 ? (
              <div className="flex flex-col items-center py-8 text-center">
                <Shield className="h-8 w-8 text-emerald-400 mb-2" />
                <p className="text-sm text-slate-400">No large files detected</p>
              </div>
            ) : (
              <div className="space-y-2">
                {largeFiles.map((f) => (
                  <div key={f.path} className="flex items-center justify-between rounded-lg bg-slate-800/30 px-3 py-2">
                    <span className="text-sm text-slate-300 truncate max-w-[60%]">{f.path}</span>
                    <Badge variant={f.size > 20000 ? "error" : "warning"}>
                      {(f.size / 1024).toFixed(1)} KB
                    </Badge>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Layers className="h-5 w-5 text-violet-400" />
            File Extension Breakdown
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            {Object.entries(extStats).sort(([, a], [, b]) => b - a).map(([ext, count]) => (
              <Badge key={ext} variant="default" className="text-sm">
                {ext} <span className="ml-1 text-slate-500">({count})</span>
              </Badge>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
