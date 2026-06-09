"use client"

import { useEffect, useState } from "react"
import { useParams } from "next/navigation"
import Link from "next/link"
import { motion } from "framer-motion"
import { ArrowLeft } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Spinner } from "@/components/ui/loading"
import { ChatInterface } from "@/components/chat/chat-interface"
import { getRepoStatus } from "@/lib/api"
import type { Repository } from "@/lib/types"

export default function ChatPage() {
  const params = useParams()
  const repoId = params.id as string
  const [repo, setRepo] = useState<Repository | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getRepoStatus(repoId)
      .then(setRepo)
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [repoId])

  if (loading) {
    return (
      <div className="flex justify-center py-20">
        <Spinner size="lg" />
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className="flex items-center gap-3"
      >
        <Link href={`/repositories/${repoId}`}>
          <Button variant="ghost" size="icon">
            <ArrowLeft className="h-4 w-4" />
          </Button>
        </Link>
        <div>
          <h1 className="text-xl font-bold text-slate-100">AI Chat</h1>
          <p className="text-sm text-slate-400">
            Ask questions about {repo?.name || "the repository"} codebase
          </p>
        </div>
      </motion.div>

      <ChatInterface repoId={repoId} repoName={repo?.name || "Repository"} />
    </div>
  )
}
