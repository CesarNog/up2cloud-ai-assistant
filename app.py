"""Vercel-compatible FastAPI entry point for the UP2CLOUD assistant."""

from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse, Response
from pydantic import BaseModel, Field

from enhanced_features import CostEstimator
from model import predict


STATIC_INDEX = Path(__file__).parent / "static" / "index.html"
CANONICAL_URL = "https://up2cloud.tech/ai-assistent-model/"
ROBOTS_TXT = f"""User-agent: *
Allow: /
Disallow: /api/
Disallow: /docs
Disallow: /redoc
Disallow: /openapi.json

Sitemap: https://up2cloud.tech/sitemap.xml
"""
SITEMAP_XML = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>{CANONICAL_URL}</loc>
    <lastmod>2026-08-31</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.9</priority>
  </url>
</urlset>
"""

app = FastAPI(
    title="UP2CLOUD AI Cloud Engineering Assistant",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://up2cloud.tech",
        "https://www.up2cloud.tech",
        "null",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)


class PredictRequest(BaseModel):
    """Request accepted by the shared prediction endpoint."""

    prompt: str = Field(min_length=1, max_length=10_000)
    context: dict[str, Any] | None = None
    features: dict[str, Any] | None = None


class InfrastructureRequest(BaseModel):
    """Infrastructure payload accepted by the cost endpoint."""

    infrastructure: dict[str, Any]


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    """Serve the Vercel web interface."""

    if not STATIC_INDEX.is_file():
        raise HTTPException(status_code=500, detail="Web interface is unavailable")
    return FileResponse(STATIC_INDEX)


@app.get("/health")
def health() -> dict[str, str]:
    """Return a lightweight deployment health response."""

    return {"status": "ok", "service": "up2cloud-ai-assistant"}


@app.get("/robots.txt", include_in_schema=False, response_class=PlainTextResponse)
def robots() -> str:
    """Expose crawler guidance for the public Vercel application."""

    return ROBOTS_TXT


@app.get("/sitemap.xml", include_in_schema=False)
def sitemap() -> Response:
    """Point crawlers at the canonical UP2CLOUD assistant URL."""

    return Response(content=SITEMAP_XML, media_type="application/xml")


@app.post("/api/predict")
def predict_endpoint(request: PredictRequest) -> dict[str, Any]:
    """Run the existing assistant and optional feature handlers."""

    try:
        return predict(
            request.prompt,
            context=request.context,
            features=request.features,
        )
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/cost")
def cost_endpoint(request: InfrastructureRequest) -> dict[str, Any]:
    """Return the existing deterministic infrastructure cost estimate."""

    try:
        return CostEstimator.estimate_monthly_cost(request.infrastructure)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
