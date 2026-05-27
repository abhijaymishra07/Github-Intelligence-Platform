"use client"

import { useEffect, useState } from "react"
import { useParams } from "next/navigation"
import Link from "next/link"
import { motion } from "framer-motion"
import {
  GitBranch,
  MessageSquare,
  FolderTree,
  BarChart3,
  Network,
  FileCode2,
  Clock,
  ArrowLeft,
} from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Spinner } from "@/components/ui/loading"
import { FileTree } from "@/components/repository/file-tree"
import { getRepoStatus, getRepoFiles } from "@/lib/api"
import type { Repository, RepoFile } from "@/lib/types"

const navLinks = [
  { label: "Chat", href: "chat", icon: MessageSquare, description: "Ask AI about this repo" },
  { label: "Explorer", href: "explorer", icon: FolderTree, description: "Browse file tree" },
  { label: "Analytics", href: "analytics", icon: BarChart3, description: "View code insights" },
  { label: "Visualizations", href: "visualizations", icon: Network, description: "Dependency graphs" },
]

export default function RepoOverviewPage() {
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

  if (!repo) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <p className="text-slate-400">Repository not found</p>
        <Link href="/repositories">
          <Button variant="ghost" className="mt-4">
            <ArrowLeft className="mr-2 h-4 w-4" /> Back to repositories
          </Button>
        </Link>
      </div>
    )
  }

  const statusVariant: Record<string, "success" | "warning" | "error" | "info"> = {
    ready: "success",
    cloning: "warning",
    parsing: "warning",
    embedding: "info",
    error: "error",
  }

  return (
    <div className="space-y-6">
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
        <Link href="/repositories">
          <Button variant="ghost" size="sm" className="mb-4">
            <ArrowLeft className="mr-2 h-4 w-4" /> Back
          </Button>
        </Link>

        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-cyan-500 to-blue-500">
              <GitBranch className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-slate-100">{repo.name}</h1>
              <p className="text-sm text-slate-400">{repo.url}</p>
            </div>
          </div>
          <Badge variant={statusVariant[repo.status] || "default"} className="text-sm">
            {repo.status}
          </Badge>
        </div>
      </motion.div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[
          { label: "Branch", value: repo.branch, icon: GitBranch },
          { label: "Language", value: repo.language || "N/A", icon: FileCode2 },
          { label: "Files", value: String(repo.file_count || files.length), icon: FolderTree },
          { label: "Added", value: new Date(repo.created_at).toLocaleDateString(), icon: Clock },
        ].map((stat) => (
          <Card key={stat.label}>
            <CardContent className="flex items-center gap-3 p-4">
              <stat.icon className="h-5 w-5 text-cyan-400 shrink-0" />
              <div>
                <p className="text-xs text-slate-500">{stat.label}</p>
                <p className="font-medium text-slate-200">{stat.value}</p>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {navLinks.map((link, i) => (
          <motion.div
            key={link.label}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
          >
            <Link href={`/repositories/${repoId}/${link.href}`}>
              <Card className="group cursor-pointer transition-all hover:border-cyan-500/30">
                <CardContent className="flex flex-col items-center p-6 text-center">
                  <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-xl bg-slate-800 group-hover:bg-cyan-500/10 transition-colors">
                    <link.icon className="h-6 w-6 text-slate-400 group-hover:text-cyan-400 transition-colors" />
                  </div>
                  <h3 className="font-semibold text-slate-200">{link.label}</h3>
                  <p className="mt-1 text-xs text-slate-500">{link.description}</p>
                </CardContent>
              </Card>
            </Link>
          </motion.div>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FolderTree className="h-5 w-5 text-cyan-400" />
            File Tree
          </CardTitle>
        </CardHeader>
        <CardContent>
          <FileTree files={files} />
        </CardContent>
      </Card>
    </div>
  )
}
