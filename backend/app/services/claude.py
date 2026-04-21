import anthropic
from app.core.config import settings
from app.models.paper import PaperBase, PaperAnalysis, SuggestedRelated
import json

_client: anthropic.Anthropic | None = None


def get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    return _client


ANALYSIS_PROMPT = """You are a research assistant that analyzes academic papers.
Return ONLY a valid JSON object with exactly these keys:

{
  "title": "...",
  "authors": ["author1", "author2"],
  "published_date": "YYYY-MM-DD or null",
  "keywords": ["keyword1", "keyword2", "keyword3"],
  "one_sentence_summary": "...",
  "preliminaries": "...",
  "problem_statement": "...",
  "core_concept": "...",
  "methods_and_experiments": "...",
  "discussions_and_limitations": "...",
  "future_work": "...",
  "suggested_related": [
    {"arxiv_id": "XXXX.XXXXX", "title": "..."},
    {"arxiv_id": "XXXX.XXXXX", "title": "..."},
    {"arxiv_id": "XXXX.XXXXX", "title": "..."}
  ]
}

Rules:
- "title": extract or infer the paper title from the content provided.
- "authors": extract author names as a list. Use [] if not found.
- "published_date": extract the publication or submission date in YYYY-MM-DD format. Use null if not found.
- "keywords" MUST be a JSON array of exactly 3 short technical keywords. Use standard abbreviations where they exist (e.g. "Large Language Models" → "LLM", "Test-Time Training" → "TTT", "Reinforcement Learning" → "RL", "Natural Language Processing" → "NLP", "Retrieval-Augmented Generation" → "RAG"). Each keyword should be at most 4 words or its common abbreviation.
- "suggested_related" MUST be a list of exactly 3 real arXiv papers closely related to this paper. Use real arXiv IDs you are confident exist.
- All other values must be plain strings (no nested objects or arrays).
- Do not add any text outside the JSON object.
"""

TRANSLATION_PROMPT = """You are a Korean translator for academic paper analysis.
You will receive a JSON object with English analysis fields.
Return ONLY a valid JSON object with the same keys but all values translated into Korean.
Do not add any text outside the JSON object.
"""


def _parse_json(text: str) -> dict:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Extract content from inside ``` fences
    parts = text.split("```")
    for part in parts[1::2]:
        if part.startswith("json"):
            part = part[4:]
        part = part.strip()
        try:
            return json.loads(part)
        except json.JSONDecodeError:
            continue
    raise ValueError(f"Could not parse JSON from response: {text[:200]}")


def _to_str(v: object) -> str:
    if isinstance(v, list):
        return "\n".join(f"• {item}" for item in v)
    if isinstance(v, dict):
        return "\n".join(f"{k}: {val}" for k, val in v.items())
    return str(v)


def _to_list(v: object) -> list[str]:
    if isinstance(v, list):
        return [str(i) for i in v]
    return [str(v)]


async def analyze_paper(paper: PaperBase, web_content: bool = False) -> PaperAnalysis:
    client = get_client()
    if web_content:
        user_msg = f"""The following is scraped text from a research paper webpage at: {paper.arxiv_url}

{paper.abstract}

Extract the paper information and analyze it. Return JSON."""
    else:
        user_msg = f"""Title: {paper.title}
Authors: {', '.join(paper.authors)}
Abstract: {paper.abstract}

Analyze this paper and return JSON."""

    # Step 1: English analysis
    en_response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=ANALYSIS_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
    )
    en_data = _parse_json(en_response.content[0].text)

    # Step 2: Korean translation (exclude keywords array)
    fields_to_translate = {
        k: v for k, v in en_data.items() if k != "keywords"
    }
    ko_response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=TRANSLATION_PROMPT,
        messages=[{"role": "user", "content": json.dumps(fields_to_translate, ensure_ascii=False)}],
    )
    ko_data = _parse_json(ko_response.content[0].text)

    raw_related = en_data.get("suggested_related", [])
    suggested = [
        SuggestedRelated(arxiv_id=r["arxiv_id"], title=r["title"])
        for r in raw_related if isinstance(r, dict) and r.get("arxiv_id")
    ][:3]

    # Expose extracted metadata so callers can update the PaperBase if needed
    paper.title = en_data.get("title") or paper.title
    extracted_authors = en_data.get("authors")
    if extracted_authors and not paper.authors:
        paper.authors = _to_list(extracted_authors)
    if not paper.published_date:
        raw_date = en_data.get("published_date")
        if raw_date and raw_date != "null":
            try:
                from datetime import date
                paper.published_date = date.fromisoformat(str(raw_date)[:10])
            except Exception:
                pass

    return PaperAnalysis(
        keywords=_to_list(en_data.get("keywords", [])),
        one_sentence_summary=_to_str(en_data["one_sentence_summary"]),
        preliminaries=_to_str(en_data["preliminaries"]),
        problem_statement=_to_str(en_data["problem_statement"]),
        core_concept=_to_str(en_data["core_concept"]),
        methods_and_experiments=_to_str(en_data["methods_and_experiments"]),
        discussions_and_limitations=_to_str(en_data["discussions_and_limitations"]),
        future_work=_to_str(en_data["future_work"]),
        suggested_related=suggested,
        ko_one_sentence_summary=_to_str(ko_data.get("one_sentence_summary", "")),
        ko_preliminaries=_to_str(ko_data.get("preliminaries", "")),
        ko_problem_statement=_to_str(ko_data.get("problem_statement", "")),
        ko_core_concept=_to_str(ko_data.get("core_concept", "")),
        ko_methods_and_experiments=_to_str(ko_data.get("methods_and_experiments", "")),
        ko_discussions_and_limitations=_to_str(ko_data.get("discussions_and_limitations", "")),
        ko_future_work=_to_str(ko_data.get("future_work", "")),
    )
