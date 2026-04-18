import { useEffect, useRef } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import * as d3 from 'd3'
import { papersApi, Paper } from '../api'

interface Node extends d3.SimulationNodeDatum {
  id: string
  title: string
  status: string
}

interface Link {
  source: string
  target: string
  weight: number
}

function buildGraph(papers: Paper[]) {
  const nodes: Node[] = papers.map(p => ({ id: p.id, title: p.title, status: p.status }))
  const links: Link[] = []

  for (let i = 0; i < papers.length; i++) {
    for (let j = i + 1; j < papers.length; j++) {
      const kws1 = new Set((papers[i].analysis?.keywords ?? []).map(k => k.toLowerCase()))
      const kws2 = (papers[j].analysis?.keywords ?? []).map(k => k.toLowerCase())
      const overlap = kws2.filter(k => kws1.has(k)).length
      if (overlap > 0) {
        links.push({ source: papers[i].id, target: papers[j].id, weight: overlap })
      }
    }
  }
  return { nodes, links }
}

const STATUS_COLOR: Record<string, string> = {
  unread: '#7b7f99',
  reading: '#e6a817',
  read: '#4caf82',
}

export default function GraphPage() {
  const svgRef = useRef<SVGSVGElement>(null)
  const navigate = useNavigate()

  const { data: papers = [], isLoading } = useQuery({
    queryKey: ['papers'],
    queryFn: () => papersApi.list(),
  })

  useEffect(() => {
    if (!papers.length || !svgRef.current) return
    const { nodes, links } = buildGraph(papers)
    const svg = d3.select(svgRef.current)
    svg.selectAll('*').remove()

    const width = svgRef.current.clientWidth || 900
    const height = svgRef.current.clientHeight || 600

    const g = svg.append('g')

    svg.call(
      d3.zoom<SVGSVGElement, unknown>()
        .scaleExtent([0.3, 3])
        .on('zoom', e => g.attr('transform', e.transform))
    )

    const sim = d3.forceSimulation(nodes)
      .force('link', d3.forceLink(links).id((d: any) => d.id).distance(d => 120 / (d as any).weight))
      .force('charge', d3.forceManyBody().strength(-200))
      .force('center', d3.forceCenter(width / 2, height / 2))

    const link = g.append('g')
      .selectAll('line')
      .data(links)
      .join('line')
      .attr('stroke', '#2a2d3a')
      .attr('stroke-width', d => Math.sqrt(d.weight) * 1.5)

    const node = g.append('g')
      .selectAll('circle')
      .data(nodes)
      .join('circle')
      .attr('r', 8)
      .attr('fill', d => STATUS_COLOR[d.status] ?? '#7b7f99')
      .attr('stroke', '#0f1117')
      .attr('stroke-width', 2)
      .style('cursor', 'pointer')
      .on('click', (_, d) => navigate(`/papers/${d.id}`))
      .call(
        d3.drag<SVGCircleElement, Node>()
          .on('start', (event, d) => { if (!event.active) sim.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y })
          .on('drag', (event, d) => { d.fx = event.x; d.fy = event.y })
          .on('end', (event, d) => { if (!event.active) sim.alphaTarget(0); d.fx = null; d.fy = null }) as any
      )

    const label = g.append('g')
      .selectAll('text')
      .data(nodes)
      .join('text')
      .text(d => d.title.slice(0, 35) + (d.title.length > 35 ? '…' : ''))
      .attr('font-size', 11)
      .attr('fill', '#7b7f99')
      .attr('dx', 12)
      .attr('dy', 4)
      .style('pointer-events', 'none')

    sim.on('tick', () => {
      link
        .attr('x1', d => (d.source as any).x)
        .attr('y1', d => (d.source as any).y)
        .attr('x2', d => (d.target as any).x)
        .attr('y2', d => (d.target as any).y)
      node.attr('cx', d => d.x!).attr('cy', d => d.y!)
      label.attr('x', d => d.x!).attr('y', d => d.y!)
    })

    return () => { sim.stop() }
  }, [papers, navigate])

  if (isLoading) return <p style={{ color: 'var(--muted)' }}>Loading…</p>
  if (papers.length < 2) return <p style={{ color: 'var(--muted)' }}>Add at least 2 papers to see the graph.</p>

  return (
    <div style={{ width: '100%', height: 'calc(100vh - 120px)' }}>
      <p style={{ color: 'var(--muted)', fontSize: 12, marginBottom: 12 }}>
        Nodes connected by shared keywords. Scroll to zoom, drag to pan. Click a node to open the paper.
      </p>
      <svg ref={svgRef} width="100%" height="100%" style={{ background: 'var(--surface)', borderRadius: 12 }} />
    </div>
  )
}
