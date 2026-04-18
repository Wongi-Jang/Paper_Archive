import axios from 'axios'

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ? `${import.meta.env.VITE_API_URL}/api` : '/api',
})

export interface PaperAnalysis {
  keywords: string[]
  one_sentence_summary: string
  preliminaries: string
  problem_statement: string
  core_concept: string
  methods_and_experiments: string
  discussions_and_limitations: string
  future_work: string
  ko_one_sentence_summary: string
  ko_preliminaries: string
  ko_problem_statement: string
  ko_core_concept: string
  ko_methods_and_experiments: string
  ko_discussions_and_limitations: string
  ko_future_work: string
}

export interface Paper {
  id: string
  arxiv_id: string
  title: string
  authors: string[]
  abstract: string
  published_date: string | null
  arxiv_url: string | null
  pdf_url: string | null
  status: 'unread' | 'reading' | 'read'
  notes: string | null
  source: 'arxiv' | 'web'
  analysis: PaperAnalysis | null
}

export interface RelatedPaper {
  arxiv_id: string
  title: string
  authors: string[]
  published_date: string | null
  arxiv_url: string
  one_sentence_summary: string | null
  in_archive: boolean
  archive_id: string | null
}

export const papersApi = {
  list: (params?: { status?: string; search?: string }) =>
    api.get<Paper[]>('/papers/', { params }).then(r => r.data),

  get: (id: string) =>
    api.get<Paper>(`/papers/${id}`).then(r => r.data),

  add: (arxiv_id: string, status = 'unread') =>
    api.post<Paper>('/papers/', { arxiv_id, status }).then(r => r.data),

  bulkAdd: (arxiv_ids: string[], status = 'unread') =>
    api.post<{ succeeded: Paper[]; failed: { arxiv_id: string; error: string }[] }>(
      '/papers/bulk', { arxiv_ids, status }
    ).then(r => r.data),

  update: (id: string, payload: { status?: string; notes?: string }) =>
    api.patch<Paper>(`/papers/${id}`, payload).then(r => r.data),

  delete: (id: string) =>
    api.delete(`/papers/${id}`),

  related: (id: string) =>
    api.get<RelatedPaper[]>(`/papers/${id}/related`).then(r => r.data),
}
