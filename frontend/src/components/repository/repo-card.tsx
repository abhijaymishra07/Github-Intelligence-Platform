"use client"

import Link from "next/link"
import { motion } from "framer-motion"
import { GitBranch, FileCode, Clock, ExternalLink } from "lucide-react"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import type { Repository } from "@/lib/types"
import { formatDate } from "@/lib/utils"

interface RepoCardProps {
  repo: Repository
  index?: number
}

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

const languageColors: Record<string, string> = {
  TypeScript: "bg-blue-500",
  JavaScript: "bg-yellow-500",
  Python: "bg-green-500",
  Rust: "bg-orange-500",
  Go: "bg-cyan-500",
  Java: "bg-red-500",
  Ruby: "bg-red-400",
  PHP: "bg-indigo-500",
  "C++": "bg-pink-500",
  C: "bg-gray-500",
}

export function RepoCard({ repo, index = 0 }: RepoCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: index * 0.05 }}
    >
      <Link href={`/repositories/${repo.id}`}>
        <Card className="p-5 cursor-pointer hover:border-cyan-500/30 group">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-slate-800 group-hover:bg-slate-700 transition-colors">
                <GitBranch className="h-5 w-5 text-slate-400" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="font-semibold text-slate-200 group-hover:text-cyan-400 transition-colors">
                    {repo.name}
                  </h3>
                  <Badge variant={statusVariant(repo.status)}>
                    {repo.status}
                  </Badge>
                </div>
                <p className="mt-0.5 text-xs text-slate-500 line-clamp-1">
                  {repo.description || repo.url}
                </p>
              </div>
            </div>
            <Button variant="ghost" size="icon" className="opacity-0 group-hover:opacity-100 transition-opacity">
              <ExternalLink className="h-4 w-4" />
            </Button>
          </div>

          <div className="mt-4 flex items-center gap-4 text-xs text-slate-500">
            {repo.language && (
              <span className="flex items-center gap-1.5">
                <span
                  className={`h-2.5 w-2.5 rounded-full ${
                    languageColors[repo.language] || "bg-slate-500"
                  }`}
                />
                {repo.language}
              </span>
            )}
            <span className="flex items-center gap-1">
              <FileCode className="h-3 w-3" />
              {repo.file_count} files
            </span>
            <span className="flex items-center gap-1">
              <Clock className="h-3 w-3" />
              {formatDate(repo.updated_at)}
            </span>
          </div>
        </Card>
      </Link>
    </motion.div>
  )
}
