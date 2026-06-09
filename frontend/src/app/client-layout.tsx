"use client"

import { useState } from "react"
import { Sidebar } from "@/components/layout/sidebar"
import { Header } from "@/components/layout/header"

export function ClientLayout({ children }: { children: React.ReactNode }) {
  const [sidebarCollapsed] = useState(false)

  return (
    <div className="flex min-h-screen bg-slate-950">
      <Sidebar />
      <div
        className="flex flex-1 flex-col transition-all duration-200"
        style={{ marginLeft: sidebarCollapsed ? 72 : 256 }}
      >
        <Header />
        <main className="flex-1 p-6">{children}</main>
      </div>
    </div>
  )
}
