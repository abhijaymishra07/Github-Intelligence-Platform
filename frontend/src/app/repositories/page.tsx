"use client"

import { useEffect, useState, useCallback } from "react"
import { motion } from "framer-motion"
import { Plus, Search, GitBranch } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { RepoCard } from "@/components/repository/repo-card"
import { AddRepoModal } from "@/components/repository/add-repo-modal"
import { Spinner } from "@/components/ui/loading"
import { getRepos } from "@/lib/api"
import type { Repository } from "@/lib/types"

export default function RepositoriesPage() {
  const [repos, setRepos] = useState<Repository[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState("")
  const [modalOpen, setModalOpen] = useState(false)

  const fetchRepos = useCallback(() => {
    setLoading(true)
    getRepos()
      .then(setRepos)
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    fetchRepos()
  }, [fetchRepos])

  const filtered = repos.filter(
    (r) =>
      r.name.toLowerCase().includes(search.toLowerCase()) ||
      r.url.toLowerCase().includes(search.toLowerCase()) ||
      (r.language && r.language.toLowerCase().includes(search.toLowerCase()))
  )

  return (
    <div className="space-y-6">
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between"
      >
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Repositories</h1>
          <p className="mt-1 text-slate-400">
            Manage and analyze your GitHub repositories
          </p>
        </div>
        <Button onClick={() => setModalOpen(true)} className="gap-2">
          <Plus className="h-4 w-4" />
          Add Repository
        </Button>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, delay: 0.1 }}
        className="flex items-center gap-3"
      >
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
          <Input
            placeholder="Search repositories..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
      </motion.div>

      {loading ? (
        <div className="flex justify-center py-20">
          <Spinner size="lg" />
        </div>
      ) : filtered.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <GitBranch className="h-16 w-16 text-slate-700 mb-4" />
          <h3 className="text-lg font-medium text-slate-300 mb-2">
            {search ? "No matching repositories" : "No repositories yet"}
          </h3>
          <p className="text-sm text-slate-500 mb-6">
            {search
              ? "Try a different search term"
              : "Add a GitHub repository to start analyzing code"}
          </p>
          {!search && (
            <Button onClick={() => setModalOpen(true)}>
              <Plus className="mr-2 h-4 w-4" /> Add Repository
            </Button>
          )}
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {filtered.map((repo, i) => (
            <RepoCard key={repo.id} repo={repo} index={i} />
          ))}
        </div>
      )}

      <AddRepoModal
        open={modalOpen}
        onOpenChange={setModalOpen}
        onSuccess={fetchRepos}
      />
    </div>
  )
}
