import { useState, useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { papersApi, Paper } from '../api'
import styles from './PapersPage.module.css'

const STATUS_COLORS: Record<string, string> = {
  unread: 'var(--muted)',
  reading: 'var(--yellow)',
  read: 'var(--green)',
}

export default function PapersPage() {
  const [arxivId, setArxivId] = useState('')
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [keywordFilter, setKeywordFilter] = useState('')
  const [sortOrder, setSortOrder] = useState<'desc' | 'asc'>('desc')
  const qc = useQueryClient()

  const { data: papers = [], isLoading } = useQuery({
    queryKey: ['papers', statusFilter],
    queryFn: () => papersApi.list({ status: statusFilter || undefined }),
  })

  const allKeywords = useMemo(() => {
    const set = new Set<string>()
    papers.forEach(p => p.analysis?.keywords.forEach(kw => set.add(kw)))
    return Array.from(set).sort()
  }, [papers])

  const filtered = useMemo(() => {
    let result = papers
    if (search) {
      const s = search.toLowerCase()
      result = result.filter(p =>
        p.title.toLowerCase().includes(s) ||
        p.authors.some(a => a.toLowerCase().includes(s)) ||
        p.analysis?.keywords.some(kw => kw.toLowerCase().includes(s))
      )
    }
    if (keywordFilter) {
      result = result.filter(p =>
        p.analysis?.keywords.includes(keywordFilter)
      )
    }
    result = [...result].sort((a, b) => {
      const da = a.published_date ?? ''
      const db = b.published_date ?? ''
      return sortOrder === 'desc' ? db.localeCompare(da) : da.localeCompare(db)
    })
    return result
  }, [papers, search, keywordFilter, sortOrder])

  const ids = arxivId.split(/[\n,]+/).map(s => s.trim()).filter(Boolean)
  const isMulti = ids.length > 1

  const addMutation = useMutation({
    mutationFn: () => isMulti
      ? papersApi.bulkAdd(ids)
      : papersApi.add(ids[0]),
    onSuccess: () => { setArxivId(''); qc.invalidateQueries({ queryKey: ['papers'] }) },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) => papersApi.update(id, { status }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['papers'] }),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => papersApi.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['papers'] }),
  })

  return (
    <div>
      <div className={styles.addRow}>
        <textarea
          value={arxivId}
          onChange={e => setArxivId(e.target.value)}
          placeholder={'Paste one or multiple arXiv IDs or URLs, one per line:\n2301.00001\nhttps://arxiv.org/abs/2301.00002'}
          rows={isMulti ? Math.min(ids.length + 1, 6) : 1}
          style={{ maxWidth: 420, resize: 'vertical', fontFamily: 'inherit' }}
        />
        <div className={styles.addActions}>
          <button
            onClick={() => addMutation.mutate()}
            disabled={!arxivId.trim() || addMutation.isPending}
            style={{ background: 'var(--accent)', color: '#fff' }}
          >
            {addMutation.isPending
              ? `Adding${isMulti ? ` ${ids.length} papers` : ''}…`
              : `+ Add${isMulti ? ` ${ids.length} Papers` : ' Paper'}`}
          </button>
          {isMulti && <span className={styles.multiHint}>{ids.length} IDs detected</span>}
          {addMutation.isError && (
            <span className={styles.error}>Failed: {String((addMutation.error as any)?.response?.data?.detail ?? 'Unknown error')}</span>
          )}
          {addMutation.isSuccess && isMulti && (() => {
            const data = (addMutation.data as any)
            if (data?.failed?.length > 0) {
              return <span className={styles.error}>{data.failed.length} failed: {data.failed.map((f: any) => f.arxiv_id).join(', ')}</span>
            }
            return null
          })()}
        </div>
      </div>

      <div className={styles.filters}>
        <input
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder="Search title, author, keyword…"
          style={{ maxWidth: 220 }}
        />
        <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)} style={{ width: 130 }}>
          <option value="">All statuses</option>
          <option value="unread">Unread</option>
          <option value="reading">Reading</option>
          <option value="read">Read</option>
        </select>
        <select value={keywordFilter} onChange={e => setKeywordFilter(e.target.value)} style={{ width: 160 }}>
          <option value="">All keywords</option>
          {allKeywords.map(kw => <option key={kw} value={kw}>{kw}</option>)}
        </select>
        <button
          onClick={() => setSortOrder(o => o === 'desc' ? 'asc' : 'desc')}
          style={{ background: 'var(--surface)', border: '1px solid var(--border)', color: 'var(--text)', whiteSpace: 'nowrap' }}
        >
          Date {sortOrder === 'desc' ? '↓' : '↑'}
        </button>
        <span className={styles.count}>{filtered.length} paper{filtered.length !== 1 ? 's' : ''}</span>
      </div>

      {isLoading ? (
        <p className={styles.empty}>Loading…</p>
      ) : filtered.length === 0 ? (
        <p className={styles.empty}>No papers found.</p>
      ) : (
        <ul className={styles.list}>
          {filtered.map((p: Paper) => (
            <li key={p.id} className={styles.card}>
              <div className={styles.cardHeader}>
                <Link to={`/papers/${p.id}`} className={styles.title}>{p.title}</Link>
                <select
                  value={p.status}
                  onChange={e => updateMutation.mutate({ id: p.id, status: e.target.value })}
                  style={{ width: 110, color: STATUS_COLORS[p.status], flexShrink: 0 }}
                >
                  <option value="unread">Unread</option>
                  <option value="reading">Reading</option>
                  <option value="read">Read</option>
                </select>
              </div>
              <div className={styles.meta}>
                {p.authors.slice(0, 3).join(', ')}{p.authors.length > 3 ? ' et al.' : ''}
                {p.published_date && <span> · {p.published_date}</span>}
                {p.arxiv_url && <> · <a href={p.arxiv_url} target="_blank" rel="noreferrer">{p.source === 'web' ? 'Source' : 'arXiv'}</a></>}
              </div>
              {p.analysis && (
                <>
                  <p className={styles.snippet}>{p.analysis.one_sentence_summary}</p>
                  <div className={styles.keywords}>
                    {p.analysis.keywords.slice(0, 3).map(kw => (
                      <span
                        key={kw}
                        className={`${styles.kw} ${keywordFilter === kw ? styles.kwActive : ''}`}
                        onClick={() => setKeywordFilter(kw === keywordFilter ? '' : kw)}
                      >{kw}</span>
                    ))}
                  </div>
                </>
              )}
              <button
                className={styles.del}
                onClick={() => deleteMutation.mutate(p.id)}
                title="Delete"
              >×</button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
