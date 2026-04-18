from pydantic import BaseModel
from typing import Optional
from datetime import date


class PaperBase(BaseModel):
    arxiv_id: str
    title: str
    authors: list[str]
    abstract: str
    published_date: Optional[date] = None
    arxiv_url: Optional[str] = None
    pdf_url: Optional[str] = None


class SuggestedRelated(BaseModel):
    arxiv_id: str
    title: str


class PaperAnalysis(BaseModel):
    keywords: list[str] = []
    one_sentence_summary: str
    preliminaries: str
    problem_statement: str
    core_concept: str
    methods_and_experiments: str
    discussions_and_limitations: str
    future_work: str
    ko_one_sentence_summary: str = ''
    ko_preliminaries: str = ''
    ko_problem_statement: str = ''
    ko_core_concept: str = ''
    ko_methods_and_experiments: str = ''
    ko_discussions_and_limitations: str = ''
    ko_future_work: str = ''
    suggested_related: list[SuggestedRelated] = []


class Paper(PaperBase):
    id: Optional[str] = None
    analysis: Optional[PaperAnalysis] = None
    status: str = "unread"  # "unread" | "reading" | "read"
    notes: Optional[str] = None
    source: str = "arxiv"  # "arxiv" | "web"

    class Config:
        from_attributes = True


class PaperCreate(BaseModel):
    arxiv_id: str
    status: str = "unread"


class PaperUpdate(BaseModel):
    status: Optional[str] = None
    analysis: Optional[PaperAnalysis] = None
    notes: Optional[str] = None


class RelatedPaper(BaseModel):
    arxiv_id: str
    title: str
    authors: list[str]
    published_date: Optional[date] = None
    arxiv_url: str
    one_sentence_summary: Optional[str] = None
    in_archive: bool
    archive_id: Optional[str] = None
