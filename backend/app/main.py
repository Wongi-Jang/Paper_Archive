from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.papers import router as papers_router

app = FastAPI(title="Paper Archive API", version="0.1.0")

import os

ALLOWED_ORIGINS = [
    "http://localhost:5173",
    *[o.strip() for o in os.getenv("ALLOWED_ORIGINS", "").split(",") if o.strip()],
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(papers_router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok"}
