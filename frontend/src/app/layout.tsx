"use client"

import { Inter } from "next/font/google"
import "./globals.css"
import { Sidebar } from "@/components/layout/sidebar"
import { Header } from "@/components/layout/header"

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
})

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className={`${inter.variable} dark h-full antialiased`}>
      <head>
        <title>GitHub Intelligence Platform</title>
        <meta name="description" content="AI-powered platform for understanding, analyzing, and querying GitHub repositories" />
      </head>
      <body className="min-h-full bg-slate-950 text-slate-100">
        <div className="flex h-screen overflow-hidden">
          <Sidebar />
          <div className="flex flex-1 flex-col ml-[72px] lg:ml-64 transition-all duration-200">
            <Header />
            <main className="flex-1 overflow-y-auto p-6">
              {children}
            </main>
          </div>
        </div>
      </body>
    </html>
  )
}
