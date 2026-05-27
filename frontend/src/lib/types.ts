export interface Repository {
  id: number
  name: string
  url: string
  branch: string
  description: string | null
  language: string | null
  stars: number
  status: "cloning" | "parsing" | "embedding" | "ready" | "error"
  file_count: number
  total_size: number
  created_at: string
  updated_at: string
}

export interface RepoFile {
  id: number
  path: string
  filename: string
  extension: string | null
  size: number
  language: string | null
  parsed: boolean
}

export interface ChatMessage {
  id: string
  role: "user" | "assistant"
  content: string
  timestamp: string
  sources?: CodeSource[]
}

export interface CodeSource {
  file_path: string
  start_line: number
  end_line: number
  content: string
  relevance_score: number
}

export interface AnalyticsData {
  total_repos: number
  total_files: number
  total_queries: number
  active_sessions: number
  languages: LanguageStat[]
  activity: ActivityPoint[]
}

export interface LanguageStat {
  language: string
  count: number
  percentage: number
}

export interface ActivityPoint {
  date: string
  queries: number
  repos_added: number
}

export interface DependencyNode {
  id: string
  label: string
  type: "module" | "package" | "file"
  size?: number
}

export interface DependencyEdge {
  id: string
  source: string
  target: string
  type: "import" | "dependency"
}

export interface ApiError {
  message: string
  status: number
  detail?: string
}
