"use client"

import { useState } from "react"
import { ChevronRight, ChevronDown, FileCode2, Folder, FolderOpen } from "lucide-react"
import { cn } from "@/lib/utils"
import type { RepoFile } from "@/lib/types"

interface TreeNode {
  name: string
  path: string
  type: "file" | "directory"
  extension?: string | null
  language?: string | null
  size?: number
  children: TreeNode[]
}

function buildTree(files: RepoFile[]): TreeNode[] {
  const root: TreeNode = { name: "", path: "", type: "directory", children: [] }

  for (const file of files) {
    const parts = file.path.split("/")
    let current = root

    for (let i = 0; i < parts.length; i++) {
      const part = parts[i]
      const isFile = i === parts.length - 1

      let child = current.children.find((c) => c.name === part)
      if (!child) {
        child = {
          name: part,
          path: parts.slice(0, i + 1).join("/"),
          type: isFile ? "file" : "directory",
          extension: isFile ? file.extension : undefined,
          language: isFile ? file.language : undefined,
          size: isFile ? file.size : undefined,
          children: [],
        }
        current.children.push(child)
      }
      current = child
    }
  }

  const sortNodes = (nodes: TreeNode[]): TreeNode[] => {
    return nodes
      .map((n) => ({ ...n, children: sortNodes(n.children) }))
      .sort((a, b) => {
        if (a.type !== b.type) return a.type === "directory" ? -1 : 1
        return a.name.localeCompare(b.name)
      })
  }

  return sortNodes(root.children)
}

function TreeItem({
  node,
  depth = 0,
  onFileSelect,
  selectedFile,
}: {
  node: TreeNode
  depth?: number
  onFileSelect?: (path: string) => void
  selectedFile?: string
}) {
  const [expanded, setExpanded] = useState(depth < 2)
  const isDir = node.type === "directory"
  const isSelected = selectedFile === node.path

  const handleClick = () => {
    if (isDir) {
      setExpanded(!expanded)
    } else {
      onFileSelect?.(node.path)
    }
  }

  return (
    <div>
      <button
        onClick={handleClick}
        className={cn(
          "flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-sm transition-colors hover:bg-slate-800/50",
          isSelected && "bg-cyan-500/10 text-cyan-400",
          !isSelected && (isDir ? "cursor-pointer" : "cursor-default")
        )}
        style={{ paddingLeft: `${depth * 16 + 8}px` }}
      >
        {isDir ? (
          <>
            {expanded ? (
              <ChevronDown className="h-3.5 w-3.5 text-slate-500 shrink-0" />
            ) : (
              <ChevronRight className="h-3.5 w-3.5 text-slate-500 shrink-0" />
            )}
            {expanded ? (
              <FolderOpen className="h-4 w-4 text-cyan-400 shrink-0" />
            ) : (
              <Folder className="h-4 w-4 text-cyan-400 shrink-0" />
            )}
          </>
        ) : (
          <>
            <span className="w-3.5" />
            <FileCode2 className="h-4 w-4 text-slate-500 shrink-0" />
          </>
        )}
        <span className={cn("truncate", isDir ? "text-slate-200" : "text-slate-400")}>
          {node.name}
        </span>
        {node.size !== undefined && (
          <span className="ml-auto text-xs text-slate-600 shrink-0">
            {node.size > 1024 ? `${(node.size / 1024).toFixed(1)}KB` : `${node.size}B`}
          </span>
        )}
      </button>
      {isDir && expanded && (
        <div>
          {node.children.map((child) => (
            <TreeItem
              key={child.path}
              node={child}
              depth={depth + 1}
              onFileSelect={onFileSelect}
              selectedFile={selectedFile}
            />
          ))}
        </div>
      )}
    </div>
  )
}

interface FileTreeProps {
  files: RepoFile[]
  onFileSelect?: (path: string) => void
  selectedFile?: string
}

export function FileTree({ files, onFileSelect, selectedFile }: FileTreeProps) {
  const tree = buildTree(files)

  if (tree.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-8 text-center">
        <FileCode2 className="h-8 w-8 text-slate-600 mb-2" />
        <p className="text-sm text-slate-400">No files found</p>
      </div>
    )
  }

  return (
    <div className="py-2 max-h-[600px] overflow-y-auto">
      {tree.map((node) => (
        <TreeItem
          key={node.path}
          node={node}
          onFileSelect={onFileSelect}
          selectedFile={selectedFile}
        />
      ))}
    </div>
  )
}
