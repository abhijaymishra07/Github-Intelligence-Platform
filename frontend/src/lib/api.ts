import axios, { AxiosError } from "axios"
import type {
  Repository,
  RepoFile,
  ChatMessage,
  DependencyNode,
  DependencyEdge,
  ApiError,
} from "./types"

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1",
  headers: { "Content-Type": "application/json" },
  timeout: 300000,
})

api.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ detail?: string }>) => {
    const apiError: ApiError = {
      message: error.message,
      status: error.response?.status || 500,
      detail: error.response?.data?.detail || "An unexpected error occurred",
    }
    return Promise.reject(apiError)
  }
)

export async function uploadRepo(url: string, branch: string = "main"): Promise<Repository> {
  const { data } = await api.post<Repository>("/repo/upload", { url, branch })
  return data
}

export async function getRepos(): Promise<Repository[]> {
  const { data } = await api.get<Repository[]>("/repo/")
  return data
}

export async function getRepoStatus(repoId: string | number): Promise<Repository> {
  const { data } = await api.get<Repository>(`/repo/${repoId}/status`)
  return data
}

export async function getRepoFiles(repoId: string | number): Promise<RepoFile[]> {
  const { data } = await api.get<RepoFile[]>(`/repo/${repoId}/files`)
  return data
}

export async function deleteRepo(repoId: string | number): Promise<void> {
  await api.delete(`/repo/${repoId}`)
}

interface ChatApiResponse {
  question: string
  answer: string
  sources: string[]
  model: string
}

export async function askQuestion(repoId: string | number, question: string): Promise<ChatApiResponse> {
  const { data } = await api.post<ChatApiResponse>(`/chat/${repoId}/ask`, { question })
  return data
}

export async function getRepoSummary(repoId: string | number) {
  const { data } = await api.get(`/analysis/${repoId}/summary`)
  return data
}

export async function getRepoComplexity(repoId: string | number) {
  const { data } = await api.get(`/analysis/${repoId}/complexity`)
  return data
}

export async function getDependencyGraph(
  repoId: string | number
): Promise<{ nodes: DependencyNode[]; edges: DependencyEdge[] }> {
  const { data } = await api.get(`/viz/${repoId}/dependency-graph`)
  return data
}

export default api
