"use client"

import { Search, Bell, User } from "lucide-react"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { ThemeToggle } from "./theme-toggle"

export function Header() {
  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-slate-800 bg-slate-950/80 backdrop-blur-xl px-6">
      <div className="flex items-center gap-4">
        <h1 className="text-lg font-semibold text-slate-100 hidden md:block">
          GitHub Intelligence
        </h1>
        <div className="relative w-64 lg:w-96">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
          <Input
            placeholder="Search repositories, files..."
            className="pl-9 bg-slate-900/50 border-slate-800"
          />
        </div>
      </div>

      <div className="flex items-center gap-2">
        <ThemeToggle />
        <Button variant="ghost" size="icon" className="relative">
          <Bell className="h-5 w-5" />
          <span className="absolute -top-0.5 -right-0.5 h-2 w-2 rounded-full bg-cyan-500" />
        </Button>
        <Button variant="ghost" size="icon" className="rounded-full">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-br from-cyan-500 to-blue-500">
            <User className="h-4 w-4 text-white" />
          </div>
        </Button>
      </div>
    </header>
  )
}
