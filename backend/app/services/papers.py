from app.core.supabase import get_supabase
from app.models.paper import Paper, PaperCreate, PaperUpdate, PaperAnalysis, RelatedPaper
from app.services.arxiv import fetch_paper_metadata
from app.services.web import fetch_web_paper, _detect_source
from app.services.claude import analyze_paper
import json


def _row_to_paper(row: dict) -> Paper:
    analysis = None
    if row.get("analysis"):
        raw = row["analysis"]
        if isinstance(raw, str):
            raw = json.loads(raw)
        analysis = PaperAnalysis(**raw)
    authors = row.get("authors", [])
    if isinstance(authors, str):
        authors = json.loads(authors)
    return Paper(
        id=str(row["id"]),
        arxiv_id=row["arxiv_id"],
        title=row["title"],
        authors=authors,
        abstract=row["abstract"],
        published_date=row.get("published_date"),
        arxiv_url=row.get("arxiv_url"),
        pdf_url=row.get("pdf_url"),
        status=row.get("status", "unread"),
        notes=row.get("notes"),
        source=row.get("source", "arxiv"),
        analysis=analysis,
    )


def _build_analysis_row(analysis: PaperAnalysis) -> dict:
    return {
        "keywords": analysis.keywords,
        "one_sentence_summary": analysis.one_sentence_summary,
        "preliminaries": analysis.preliminaries,
        "problem_statement": analysis.problem_statement,
        "core_concept": analysis.core_concept,
        "methods_and_experiments": analysis.methods_and_experiments,
        "discussions_and_limitations": analysis.discussions_and_limitations,
        "future_work": analysis.future_work,
        "ko_one_sentence_summary": analysis.ko_one_sentence_summary,
        "ko_preliminaries": analysis.ko_preliminaries,
        "ko_problem_statement": analysis.ko_problem_statement,
        "ko_core_concept": analysis.ko_core_concept,
        "ko_methods_and_experiments": analysis.ko_methods_and_experiments,
        "ko_discussions_and_limitations": analysis.ko_discussions_and_limitations,
        "ko_future_work": analysis.ko_future_work,
        "suggested_related": [r.model_dump() for r in analysis.suggested_related],
    }


async def add_paper(payload: PaperCreate) -> Paper:
    db = get_supabase()
    source_type, clean_input = _detect_source(payload.arxiv_id)

    # Duplicate check
    lookup_id = clean_input if source_type == "web" else clean_input
    existing = db.table("papers").select("*").eq("arxiv_id", lookup_id).execute()
    if existing.data:
        return _row_to_paper(existing.data[0])

    if source_type == "web":
        metadata = await fetch_web_paper(clean_input)
        analysis = await analyze_paper(metadata, web_content=True)
    else:
        metadata = await fetch_paper_metadata(clean_input)
        analysis = await analyze_paper(metadata, web_content=False)

    row = {
        "arxiv_id": metadata.arxiv_id,
        "title": metadata.title,
        "authors": metadata.authors,
        "abstract": metadata.abstract,
        "published_date": metadata.published_date.isoformat() if metadata.published_date else None,
        "arxiv_url": metadata.arxiv_url,
        "pdf_url": metadata.pdf_url,
        "status": payload.status,
        "source": source_type,
        "analysis": _build_analysis_row(analysis),
    }
    try:
        result = db.table("papers").insert(row).execute()
        return _row_to_paper(result.data[0])
    except Exception as e:
        if "23505" in str(e):
            existing = db.table("papers").select("*").eq("arxiv_id", row["arxiv_id"]).execute()
            if existing.data:
                return _row_to_paper(existing.data[0])
        raise


async def list_papers(status: str | None = None, search: str | None = None) -> list[Paper]:
    db = get_supabase()
    query = db.table("papers").select("*").order("published_date", desc=True)
    if status:
        query = query.eq("status", status)
    result = query.execute()
    papers = [_row_to_paper(r) for r in result.data]
    if search:
        s = search.lower()
        papers = [
            p for p in papers
            if s in p.title.lower() or s in p.abstract.lower()
            or any(s in a.lower() for a in p.authors)
        ]
    return papers


async def get_paper(paper_id: str) -> Paper | None:
    db = get_supabase()
    result = db.table("papers").select("*").eq("id", paper_id).execute()
    if not result.data:
        return None
    return _row_to_paper(result.data[0])


async def update_paper(paper_id: str, payload: PaperUpdate) -> Paper | None:
    db = get_supabase()
    updates = payload.model_dump(exclude_none=True)
    result = db.table("papers").update(updates).eq("id", paper_id).execute()
    if not result.data:
        return None
    return _row_to_paper(result.data[0])


async def delete_paper(paper_id: str) -> bool:
    db = get_supabase()
    db.table("papers").delete().eq("id", paper_id).execute()
    return True


async def get_related_papers(paper_id: str) -> list[RelatedPaper]:
    paper = await get_paper(paper_id)
    if not paper or not paper.analysis:
        return []

    suggestions = paper.analysis.suggested_related
    if not suggestions:
        return []

    db = get_supabase()
    results: list[RelatedPaper] = []

    for s in suggestions[:3]:
        existing = db.table("papers").select("id").eq("arxiv_id", s.arxiv_id).execute()
        if existing.data:
            archive_paper = await get_paper(str(existing.data[0]["id"]))
            results.append(RelatedPaper(
                arxiv_id=s.arxiv_id,
                title=archive_paper.title if archive_paper else s.title,
                authors=archive_paper.authors if archive_paper else [],
                published_date=archive_paper.published_date if archive_paper else None,
                arxiv_url=f"https://arxiv.org/abs/{s.arxiv_id}",
                one_sentence_summary=archive_paper.analysis.one_sentence_summary if archive_paper and archive_paper.analysis else None,
                in_archive=True,
                archive_id=str(existing.data[0]["id"]),
            ))
        else:
            try:
                meta = await fetch_paper_metadata(s.arxiv_id)
                results.append(RelatedPaper(
                    arxiv_id=s.arxiv_id,
                    title=meta.title,
                    authors=meta.authors,
                    published_date=meta.published_date,
                    arxiv_url=f"https://arxiv.org/abs/{s.arxiv_id}",
                    in_archive=False,
                ))
            except Exception:
                results.append(RelatedPaper(
                    arxiv_id=s.arxiv_id,
                    title=s.title,
                    authors=[],
                    arxiv_url=f"https://arxiv.org/abs/{s.arxiv_id}",
                    in_archive=False,
                ))

    return results
