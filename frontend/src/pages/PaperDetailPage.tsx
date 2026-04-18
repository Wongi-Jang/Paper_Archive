import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { papersApi, PaperAnalysis, RelatedPaper } from '../api'
import styles from './PaperDetailPage.module.css'

type Lang = 'en' | 'ko'

const SECTIONS: { label: string; en: keyof PaperAnalysis; ko: keyof PaperAnalysis }[] = [
  { label: 'One-sentence Summary / 한 줄 요약',  en: 'one_sentence_summary',    ko: 'ko_one_sentence_summary' },
  { label: 'Preliminaries / 사전 지식',           en: 'preliminaries',           ko: 'ko_preliminaries' },
  { label: 'Problem Statement / 문제 정의',       en: 'problem_statement',       ko: 'ko_problem_statement' },
  { label: 'Core Concept / 핵심 아이디어',        en: 'core_concept',            ko: 'ko_core_concept' },
  { label: 'Methods & Experiments / 방법 및 실험', en: 'methods_and_experiments', ko: 'ko_methods_and_experiments' },
  { label: 'Discussions & Limitations / 논의 및 한계', en: 'discussions_and_limitations', ko: 'ko_discussions_and_limitations' },
  { label: 'Future Work / 향후 연구',             en: 'future_work',             ko: 'ko_future_work' },
]

export default function PaperDetailPage() {
  const { id } = useParams<{ id: string }>()
  const qc = useQueryClient()
  const [lang, setLang] = useState<Lang>('en')
  const [notes, setNotes] = useState('')
  const [saved, setSaved] = useState(false)

  const { data: paper, isLoading } = useQuery({
    queryKey: ['paper', id],
    queryFn: () => papersApi.get(id!),
    enabled: !!id,
  })

  const { data: related = [] } = useQuery<RelatedPaper[]>({
    queryKey: ['related', id],
    queryFn: () => papersApi.related(id!),
    enabled: !!id,
  })

  useEffect(() => {
    if (paper) setNotes(paper.notes ?? '')
  }, [paper])

  const saveNotes = useMutation({
    mutationFn: () => papersApi.update(id!, { notes }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['paper', id] })
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
    },
  })

  if (isLoading) return <p style={{ color: 'var(--muted)' }}>Loading…</p>
  if (!paper) return <p style={{ color: 'var(--red)' }}>Paper not found.</p>

  return (
    <div className={styles.container}>
      <Link to="/" className={styles.back}>← Back</Link>

      <h1 className={styles.title}>{paper.title}</h1>
      <div className={styles.meta}>
        <span>{paper.authors.join(', ')}</span>
        {paper.published_date && <span> · {paper.published_date}</span>}
        {paper.arxiv_url && <> · <a href={paper.arxiv_url} target="_blank" rel="noreferrer">{paper.source === 'web' ? 'Source' : 'arXiv'}</a></>}
        {paper.pdf_url && <> · <a href={paper.pdf_url} target="_blank" rel="noreferrer">PDF</a></>}
      </div>

      {paper.analysis && (
        <>
          <div className={styles.langToggle}>
            <button
              className={lang === 'en' ? styles.langActive : styles.langBtn}
              onClick={() => setLang('en')}
            >EN</button>
            <button
              className={lang === 'ko' ? styles.langActive : styles.langBtn}
              onClick={() => setLang('ko')}
            >한국어</button>
          </div>

          {SECTIONS.map(({ label, en, ko }) => {
            const content = lang === 'ko'
              ? (paper.analysis![ko] as string) || (paper.analysis![en] as string)
              : paper.analysis![en] as string
            return (
              <section key={label} className={styles.section}>
                <h2>{label}</h2>
                <p className={styles.sectionContent}>{content}</p>
              </section>
            )
          })}
        </>
      )}

      <section className={styles.section}>
        <h2>My Notes</h2>
        <textarea
          className={styles.notesArea}
          value={notes}
          onChange={e => setNotes(e.target.value)}
          placeholder="Write your thoughts, questions, or annotations here…"
          rows={6}
        />
        <div className={styles.notesFooter}>
          <button
            onClick={() => saveNotes.mutate()}
            disabled={saveNotes.isPending}
            style={{ background: 'var(--accent)', color: '#fff' }}
          >
            {saveNotes.isPending ? 'Saving…' : 'Save Notes'}
          </button>
          {saved && <span className={styles.savedMsg}>Saved</span>}
        </div>
      </section>

      <section className={styles.section}>
        <h2>Related Papers</h2>
        {related.length === 0 ? (
          <p style={{ color: 'var(--muted)', fontSize: 13 }}>No related papers found.</p>
        ) : (
          <ul className={styles.related}>
            {related.map(r => (
              <li key={r.arxiv_id} className={styles.relatedItem}>
                <div className={styles.relatedHeader}>
                  <span className={styles.relatedTitle}>{r.title}</span>
                  {r.in_archive && (
                    <span className={styles.inArchiveBadge}>In Archive</span>
                  )}
                </div>
                <div className={styles.relMeta}>
                  <span>{r.authors[0] ?? ''}{r.published_date ? ` · ${r.published_date}` : ''}</span>
                  <span className={styles.relLinks}>
                    {r.in_archive && r.archive_id && (
                      <Link to={`/papers/${r.archive_id}`}>Archive ↗</Link>
                    )}
                    <a href={r.arxiv_url} target="_blank" rel="noreferrer">arXiv ↗</a>
                  </span>
                </div>
                {r.one_sentence_summary && (
                  <p className={styles.relSnippet}>{r.one_sentence_summary}</p>
                )}
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  )
}
