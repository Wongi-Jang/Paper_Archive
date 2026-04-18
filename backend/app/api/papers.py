from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from app.models.paper import Paper, PaperCreate, PaperUpdate, RelatedPaper
from app.services import papers as svc
import asyncio

router = APIRouter(prefix="/papers", tags=["papers"])


@router.post("/", response_model=Paper, status_code=201)
async def add_paper(payload: PaperCreate):
    try:
        return await svc.add_paper(payload)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class BulkAddPayload(BaseModel):
    arxiv_ids: list[str]
    status: str = "unread"

class BulkResult(BaseModel):
    succeeded: list[Paper]
    failed: list[dict]

@router.post("/bulk", response_model=BulkResult)
async def bulk_add_papers(payload: BulkAddPayload):
    async def try_add(arxiv_id: str):
        try:
            paper = await svc.add_paper(PaperCreate(arxiv_id=arxiv_id, status=payload.status))
            return ("ok", paper)
        except Exception as e:
            return ("err", {"arxiv_id": arxiv_id, "error": str(e)})

    results = await asyncio.gather(*[try_add(aid.strip()) for aid in payload.arxiv_ids if aid.strip()])
    succeeded = [r for status, r in results if status == "ok"]
    failed = [r for status, r in results if status == "err"]
    return BulkResult(succeeded=succeeded, failed=failed)


@router.get("/", response_model=list[Paper])
async def list_papers(
    status: str | None = Query(None),
    search: str | None = Query(None),
):
    return await svc.list_papers(status=status, search=search)


@router.get("/{paper_id}", response_model=Paper)
async def get_paper(paper_id: str):
    paper = await svc.get_paper(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    return paper


@router.patch("/{paper_id}", response_model=Paper)
async def update_paper(paper_id: str, payload: PaperUpdate):
    paper = await svc.update_paper(paper_id, payload)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    return paper


@router.delete("/{paper_id}", status_code=204)
async def delete_paper(paper_id: str):
    await svc.delete_paper(paper_id)


@router.get("/{paper_id}/related", response_model=list[RelatedPaper])
async def get_related(paper_id: str):
    return await svc.get_related_papers(paper_id)
