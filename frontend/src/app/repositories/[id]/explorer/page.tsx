"use client"

import { useEffect, useState } from "react"
import { useParams } from "next/navigation"
import Link from "next/link"
import { motion } from "framer-motion"
import { ArrowLeft, FolderTree, FileCode2 } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Spinner } from "@/components/ui/loading"
import { FileTree } from "@/components/repository/file-tree"
import { getRepoStatus, getRepoFiles } from "@/lib/api"
import type { Repository, RepoFile } from "@/lib/types"

export default function ExplorerPage() {
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

  return (
    <div className="space-y-6">
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
        <Link href={`/repositories/${repoId}`}>
          <Button variant="ghost" size="sm" className="mb-2">
            <ArrowLeft className="mr-2 h-4 w-4" /> Back
          </Button>
        </Link>
        <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
          <FolderTree className="h-6 w-6 text-cyan-400" />
          File Explorer
        </h1>
        <p className="text-slate-400">{repo?.name} - {files.length} files</p>
      </motion.div>

      <div className="grid gap-6 lg:grid-cols-4">
        <div className="lg:col-span-3">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FolderTree className="h-5 w-5 text-cyan-400" />
                Repository Structure
              </CardTitle>
            </CardHeader>
            <CardContent>
              <FileTree files={files} />
            </CardContent>
          </Card>
        </div>

        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">File Statistics</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-400">Total Files</span>
                <span className="font-medium text-slate-200">{files.length}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-400">Total Size</span>
                <span className="font-medium text-slate-200">
                  {(files.reduce((sum, f) => sum + f.size, 0) / 1024).toFixed(1)} KB
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-400">Languages</span>
                <span className="font-medium text-slate-200">{sortedLanguages.length}</span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Languages</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {sortedLanguages.slice(0, 10).map(([lang, count]) => (
                  <div key={lang} className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <FileCode2 className="h-3.5 w-3.5 text-slate-500" />
                      <span className="text-sm text-slate-300">{lang}</span>
                    </div>
                    <Badge variant="default">{count}</Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
