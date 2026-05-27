"use client"

import { useEffect, useState, useCallback } from "react"
import { useParams } from "next/navigation"
import Link from "next/link"
import { motion } from "framer-motion"
import { ArrowLeft, Network, RefreshCw } from "lucide-react"
import {
  ReactFlow,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  MarkerType,
  type Node,
  type Edge,
  BackgroundVariant,
} from "reactflow"
import "reactflow/dist/style.css"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Spinner } from "@/components/ui/loading"
import { getRepoStatus, getRepoFiles } from "@/lib/api"
import type { Repository, RepoFile } from "@/lib/types"

function buildDependencyGraph(files: RepoFile[]) {
  const dirs = new Set<string>()
  files.forEach((f) => {
    const parts = f.path.split("/")
    if (parts.length > 1) dirs.add(parts[0])
  })

  const nodes: Node[] = []
  const edges: Edge[] = []
  const dirArray = Array.from(dirs)
  const centerX = 400
  const centerY = 300
  const radius = 250

  dirArray.forEach((dir, i) => {
    const angle = (2 * Math.PI * i) / dirArray.length
    const fileCount = files.filter((f) => f.path.startsWith(dir + "/")).length

    nodes.push({
      id: dir,
      position: { x: centerX + radius * Math.cos(angle), y: centerY + radius * Math.sin(angle) },
      data: { label: `${dir} (${fileCount})` },
      style: {
        background: "linear-gradient(135deg, rgba(6,182,212,0.2), rgba(59,130,246,0.2))",
        border: "1px solid rgba(6,182,212,0.3)",
        borderRadius: "12px",
        padding: "12px 20px",
        color: "#e2e8f0",
        fontSize: "13px",
        fontWeight: 600,
      },
    })
  })

  nodes.push({
    id: "root",
    position: { x: centerX, y: centerY },
    data: { label: "root" },
    style: {
      background: "linear-gradient(135deg, #06b6d4, #3b82f6)",
      border: "none",
      borderRadius: "16px",
      padding: "16px 24px",
      color: "#ffffff",
      fontSize: "14px",
      fontWeight: 700,
    },
  })

  dirArray.forEach((dir) => {
    edges.push({
      id: `root-${dir}`,
      source: "root",
      target: dir,
      style: { stroke: "#334155", strokeWidth: 2 },
      markerEnd: { type: MarkerType.ArrowClosed, color: "#475569" },
      animated: true,
    })
  })

  return { nodes, edges }
}

export default function VisualizationsPage() {
  const params = useParams()
  const repoId = params.id as string
  const [repo, setRepo] = useState<Repository | null>(null)
  const [files, setFiles] = useState<RepoFile[]>([])
  const [loading, setLoading] = useState(true)
  const [nodes, setNodes, onNodesChange] = useNodesState([])
  const [edges, setEdges, onEdgesChange] = useEdgesState([])

  const loadData = useCallback(() => {
    setLoading(true)
    Promise.all([
      getRepoStatus(repoId).catch(() => null),
      getRepoFiles(repoId).catch(() => []),
    ]).then(([r, f]) => {
      setRepo(r)
      setFiles(f)
      const graph = buildDependencyGraph(f)
      setNodes(graph.nodes)
      setEdges(graph.edges)
      setLoading(false)
    })
  }, [repoId, setNodes, setEdges])

  useEffect(() => {
    loadData()
  }, [loadData])

  if (loading) {
    return (
      <div className="flex justify-center py-20">
        <Spinner size="lg" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="flex items-center justify-between">
        <div>
          <Link href={`/repositories/${repoId}`}>
            <Button variant="ghost" size="sm" className="mb-2">
              <ArrowLeft className="mr-2 h-4 w-4" /> Back
            </Button>
          </Link>
          <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
            <Network className="h-6 w-6 text-cyan-400" />
            Dependency Visualization
          </h1>
          <p className="text-slate-400">{repo?.name} - Module dependency graph</p>
        </div>
        <Button variant="secondary" size="sm" onClick={loadData}>
          <RefreshCw className="mr-2 h-4 w-4" /> Refresh
        </Button>
      </motion.div>

      <Card>
        <CardContent className="p-0">
          <div className="h-[600px] rounded-xl overflow-hidden">
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              fitView
              className="bg-slate-950"
            >
              <Controls />
              <Background variant={BackgroundVariant.Dots} gap={20} size={1} color="#1e293b" />
            </ReactFlow>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-4 sm:grid-cols-3">
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-bold text-cyan-400">{Math.max(nodes.length - 1, 0)}</p>
            <p className="text-sm text-slate-400">Modules</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-bold text-violet-400">{edges.length}</p>
            <p className="text-sm text-slate-400">Connections</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-bold text-emerald-400">{files.length}</p>
            <p className="text-sm text-slate-400">Total Files</p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
