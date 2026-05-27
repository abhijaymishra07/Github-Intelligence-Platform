"use client"

import { useState, useRef, useEffect } from "react"
import { Send, Loader2, Sparkles } from "lucide-react"
import { motion } from "framer-motion"
import { Button } from "@/components/ui/button"
import { MessageBubble } from "./message-bubble"
import { askQuestion } from "@/lib/api"
import type { ChatMessage } from "@/lib/types"

interface ChatInterfaceProps {
  repoId: string
  repoName?: string
}

export function ChatInterface({ repoId, repoName }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "welcome",
      role: "assistant",
      content: `Hello! I'm your AI assistant for the **${repoName || "repository"}**. Ask me anything about the codebase - architecture, functions, dependencies, or any code-related questions.`,
      timestamp: new Date().toISOString(),
    },
  ])
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || loading) return

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: "user",
      content: input.trim(),
      timestamp: new Date().toISOString(),
    }

    setMessages((prev) => [...prev, userMessage])
    const question = input.trim()
    setInput("")
    setLoading(true)

    try {
      const response = await askQuestion(repoId, question)
      const aiMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: response.answer || "I couldn't generate a response. Please try again.",
        timestamp: new Date().toISOString(),
        sources: response.sources?.map((s, i) => ({
          file_path: s,
          start_line: 0,
          end_line: 0,
          content: "",
          relevance_score: 1 - i * 0.1,
        })),
      }
      setMessages((prev) => [...prev, aiMessage])
    } catch {
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: "Sorry, I encountered an error processing your question. Make sure the backend server is running and the repository has been fully processed.",
        timestamp: new Date().toISOString(),
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  return (
    <div className="flex h-[calc(100vh-10rem)] flex-col rounded-xl border border-slate-800 bg-slate-900/30">
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.map((msg, i) => (
          <MessageBubble key={msg.id} message={msg} index={i} />
        ))}
        {loading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex gap-3"
          >
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-cyan-500/20 to-blue-500/20 border border-cyan-500/20">
              <Sparkles className="h-4 w-4 text-cyan-400 animate-pulse" />
            </div>
            <div className="rounded-2xl bg-slate-800/80 border border-slate-700/50 px-4 py-3">
              <div className="flex items-center gap-2 text-sm text-slate-400">
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
                Analyzing code and generating response (this may take up to a few minutes)...
              </div>
            </div>
          </motion.div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="border-t border-slate-800 p-4">
        <form onSubmit={handleSubmit} className="flex items-end gap-3">
          <div className="relative flex-1">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask a question about the codebase..."
              rows={1}
              className="w-full resize-none rounded-xl border border-slate-700 bg-slate-800/50 px-4 py-3 pr-12 text-sm text-slate-200 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500 transition-colors"
              style={{ maxHeight: "120px" }}
            />
          </div>
          <Button
            type="submit"
            disabled={!input.trim() || loading}
            size="icon"
            className="h-11 w-11 shrink-0 rounded-xl"
          >
            <Send className="h-4 w-4" />
          </Button>
        </form>
        <p className="mt-2 text-center text-xs text-slate-500">
          AI responses are generated from indexed code. Results may not be
          exhaustive.
        </p>
      </div>
    </div>
  )
}
