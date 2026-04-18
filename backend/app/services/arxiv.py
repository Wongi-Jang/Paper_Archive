import httpx
import xml.etree.ElementTree as ET
from datetime import date
from app.models.paper import PaperBase


ARXIV_API = "https://export.arxiv.org/api/query"
NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "arxiv": "http://arxiv.org/schemas/atom",
}


def _clean_id(arxiv_id: str) -> str:
    arxiv_id = arxiv_id.strip()
    for prefix in ("https://arxiv.org/abs/", "http://arxiv.org/abs/", "arxiv.org/abs/"):
        if arxiv_id.startswith(prefix):
            arxiv_id = arxiv_id[len(prefix):]
    # Strip version suffix (e.g. 2301.00001v2 → 2301.00001)
    if 'v' in arxiv_id.split('.')[-1]:
        arxiv_id = arxiv_id[:arxiv_id.rfind('v')]
    return arxiv_id


async def fetch_paper_metadata(arxiv_id: str) -> PaperBase:
    clean_id = _clean_id(arxiv_id)
    async with httpx.AsyncClient() as client:
        resp = await client.get(ARXIV_API, params={"id_list": clean_id, "max_results": 1})
        resp.raise_for_status()

    root = ET.fromstring(resp.text)
    entry = root.find("atom:entry", NS)
    if entry is None:
        raise ValueError(f"Paper not found: {arxiv_id}")

    title = entry.findtext("atom:title", namespaces=NS, default="").strip().replace("\n", " ")
    abstract = entry.findtext("atom:summary", namespaces=NS, default="").strip().replace("\n", " ")
    authors = [
        a.findtext("atom:name", namespaces=NS, default="")
        for a in entry.findall("atom:author", NS)
    ]
    published_str = entry.findtext("atom:published", namespaces=NS, default="")
    published_date = date.fromisoformat(published_str[:10]) if published_str else None

    arxiv_url = f"https://arxiv.org/abs/{clean_id}"
    pdf_url = f"https://arxiv.org/pdf/{clean_id}"

    return PaperBase(
        arxiv_id=clean_id,
        title=title,
        authors=authors,
        abstract=abstract,
        published_date=published_date,
        arxiv_url=arxiv_url,
        pdf_url=pdf_url,
    )
