import { cn } from "@/lib/utils"

interface SpinnerProps {
  size?: "sm" | "md" | "lg"
  className?: string
}

export function Spinner({ size = "md", className }: SpinnerProps) {
  const sizeClasses = {
    sm: "h-4 w-4",
    md: "h-6 w-6",
    lg: "h-8 w-8",
  }

  return (
    <div
      className={cn(
        "animate-spin rounded-full border-2 border-slate-700 border-t-cyan-500",
        sizeClasses[size],
        className
      )}
    />
  )
}

interface SkeletonProps {
  className?: string
}

export function Skeleton({ className }: SkeletonProps) {
  return (
    <div
      className={cn(
        "animate-pulse rounded-lg bg-slate-800/50",
        className
      )}
    />
  )
}

export function PageLoader() {
  return (
    <div className="flex h-[50vh] items-center justify-center">
      <div className="flex flex-col items-center gap-4">
        <Spinner size="lg" />
        <p className="text-sm text-slate-400">Loading...</p>
      </div>
    </div>
  )
}
