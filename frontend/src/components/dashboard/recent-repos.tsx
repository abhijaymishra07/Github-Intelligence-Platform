"use client"

import { useEffect, useState } from "react"
import { motion } from "framer-motion"
import Link from "next/link"
import { GitBranch, Clock, FileCode, Plus } from "lucide-react"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Spinner } from "@/components/ui/loading"
import { getRepos } from "@/lib/api"
import type { Repository } from "@/lib/types"

const statusVariant = (status: string) => {
  switch (status) {
    case "ready":
      return "success" as const
    case "cloning":
    case "parsing":
    case "embedding":
      return "warning" as const
    case "error":
      return "error" as const
    default:
      return "default" as const
  }
}

export function RecentRepos() {
  const [repos, setRepos] = useState<Repository[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getRepos()
      .then(setRepos)
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: 0.4 }}
    >
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-slate-100">
          Recent Repositories
        </h2>
        <Link
          href="/repositories"
          className="text-sm text-cyan-400 hover:text-cyan-300 transition-colors"
        >
          View all
        </Link>
      </div>

      {loading ? (
        <div className="flex justify-center py-8">
          <Spinner />
        </div>
      ) : repos.length === 0 ? (
        <Card className="p-8">
          <div className="flex flex-col items-center text-center">
            <GitBranch className="h-10 w-10 text-slate-600 mb-3" />
            <p className="text-slate-400 mb-1">No repositories yet</p>
            <p className="text-sm text-slate-500 mb-4">Add a GitHub repo to get started</p>
            <Link href="/repositories">
              <Button size="sm">
                <Plus className="mr-2 h-4 w-4" /> Add Repository
              </Button>
            </Link>
          </div>
        </Card>
      ) : (
        <div className="space-y-3">
          {repos.slice(0, 5).map((repo) => (
            <Link key={repo.id} href={`/repositories/${repo.id}`}>
              <Card className="p-4 cursor-pointer hover:border-cyan-500/30 transition-all group">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-slate-800 group-hover:bg-slate-700 transition-colors">
                      <GitBranch className="h-5 w-5 text-slate-400" />
                    </div>
                    <div>
                      <p className="font-medium text-slate-200 group-hover:text-cyan-400 transition-colors">
                        {repo.name}
                      </p>
                      <p className="text-xs text-slate-500">{repo.description || repo.url}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <Badge variant={statusVariant(repo.status)}>
                      {repo.status}
                    </Badge>
                    <div className="hidden sm:flex items-center gap-3 text-xs text-slate-500">
                      <span className="flex items-center gap-1">
                        <FileCode className="h-3 w-3" />
                        {repo.file_count}
                      </span>
                      <span className="flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        {new Date(repo.updated_at).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                </div>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </motion.div>
  )
}
