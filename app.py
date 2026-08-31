"""Vercel-compatible FastAPI entry point for the UP2CLOUD assistant."""

import json
import logging
import os
import threading
import time
import uuid
from collections import defaultdict, deque
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse, Response

from enhanced_features import ArchitectureDiagrammer, CodeGenerator, CostEstimator, SecurityScanner
from model import predict
from schemas import (
    ArchitectureRequest,
    AssistRequest,
    ErrorResponse,
    FeedbackRequest,
    InfrastructureRequest,
    PredictRequest,
    SecurityAssessmentRequest,
    TerraformRequest,
)


STATIC_INDEX = Path(__file__).parent / "static" / "index.html"
CANONICAL_URL = "https://up2cloud.tech/ai-assistent-model/"
APP_VERSION = "3.0.0"
LOGGER = logging.getLogger("up2cloud.api")
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
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
    version=APP_VERSION,
)

allowed_origins = [
    "https://up2cloud.tech",
    "https://www.up2cloud.tech",
    # The public demo intentionally supports a local file preview. No credentials are accepted.
    "null",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)


class SlidingWindowRateLimiter:
    """Small in-process protection suitable for a public serverless demonstration."""

    def __init__(self, requests_per_minute: int = 60):
        self.limit = requests_per_minute
        self.events: dict[str, deque[float]] = defaultdict(deque)
        self.lock = threading.Lock()

    def check(self, key: str) -> tuple[bool, int, int]:
        now = time.monotonic()
        with self.lock:
            events = self.events[key]
            while events and events[0] <= now - 60:
                events.popleft()
            if len(events) >= self.limit:
                retry_after = max(1, int(60 - (now - events[0])))
                return False, 0, retry_after
            events.append(now)
            return True, self.limit - len(events), 0


RATE_LIMITER = SlidingWindowRateLimiter(int(os.getenv("RATE_LIMIT_PER_MINUTE", "60")))


def error_payload(code: str, message: str, request_id: str, details: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    return ErrorResponse(
        error={"code": code, "message": message, "request_id": request_id, "details": details}
    ).model_dump(exclude_none=True)


@app.middleware("http")
async def operational_middleware(request: Request, call_next):
    """Attach request identity, rate limits, latency, and structured logs."""

    request_id = request.headers.get("x-request-id") or uuid.uuid4().hex
    request.state.request_id = request_id[:80]
    started = time.perf_counter()
    remaining = RATE_LIMITER.limit

    if request.url.path.startswith(("/api/", "/v1/")):
        forwarded = request.headers.get("x-forwarded-for", "")
        client_key = forwarded.split(",")[0].strip() or (request.client.host if request.client else "unknown")
        allowed, remaining, retry_after = RATE_LIMITER.check(client_key)
        if not allowed:
            return JSONResponse(
                status_code=429,
                content=error_payload("rate_limit_exceeded", "Too many requests. Please retry shortly.", request.state.request_id),
                headers={"Retry-After": str(retry_after), "X-Request-ID": request.state.request_id},
            )

    response = await call_next(request)
    elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
    response.headers["X-Request-ID"] = request.state.request_id
    response.headers["X-Response-Time-Ms"] = str(elapsed_ms)
    if request.url.path.startswith(("/api/", "/v1/")):
        response.headers["X-RateLimit-Limit"] = str(RATE_LIMITER.limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
    LOGGER.info(json.dumps({
        "event": "http_request",
        "request_id": request.state.request_id,
        "method": request.method,
        "path": request.url.path,
        "status": response.status_code,
        "duration_ms": elapsed_ms,
    }))
    return response


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content=error_payload("validation_error", "The request did not match the API contract.", request.state.request_id, exc.errors()),
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=error_payload("request_failed", str(exc.detail), request.state.request_id),
        headers=exc.headers,
    )


@app.exception_handler(Exception)
async def unexpected_exception_handler(request: Request, exc: Exception):
    LOGGER.exception("Unhandled API error", extra={"request_id": request.state.request_id})
    return JSONResponse(
        status_code=500,
        content=error_payload("internal_error", "The request could not be completed safely.", request.state.request_id),
    )


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    """Serve the Vercel web interface."""

    if not STATIC_INDEX.is_file():
        raise HTTPException(status_code=500, detail="Web interface is unavailable")
    return FileResponse(STATIC_INDEX)


@app.get("/health")
def health() -> dict[str, Any]:
    """Return a lightweight deployment health response."""

    return {
        "status": "ok",
        "service": "up2cloud-ai-assistant",
        "version": APP_VERSION,
        "advisory_engine": "ready",
        "pricing_catalog": CostEstimator.PRICING_METADATA["catalog_version"],
    }


@app.get("/api/status")
def api_status(request: Request) -> dict[str, Any]:
    """Expose non-sensitive capability and provenance information."""

    return {
        "status": "operational",
        "version": APP_VERSION,
        "request_id": request.state.request_id,
        "capabilities": ["structured_advisory", "cost_scenarios", "terraform_validation", "architecture_diagrams", "evidence_assessment"],
        "pricing_metadata": CostEstimator.PRICING_METADATA,
        "limitations": [
            "No cloud account is accessed by the public demo.",
            "Generated infrastructure requires expert review before deployment.",
        ],
    }


@app.get("/robots.txt", include_in_schema=False, response_class=PlainTextResponse)
def robots() -> str:
    """Expose crawler guidance for the public Vercel application."""

    return ROBOTS_TXT


@app.get("/sitemap.xml", include_in_schema=False)
def sitemap() -> Response:
    """Point crawlers at the canonical UP2CLOUD assistant URL."""

    return Response(content=SITEMAP_XML, media_type="application/xml")


@app.post("/api/predict")
def predict_endpoint(payload: PredictRequest, request: Request) -> dict[str, Any]:
    """Run the existing assistant and optional feature handlers."""

    try:
        result = predict(
            payload.prompt,
            context=payload.context.model_dump(exclude_none=True) if payload.context else None,
            features=payload.features.model_dump(exclude_none=True) if payload.features else None,
            session_id=payload.session_id,
        )
        result["request_id"] = request.state.request_id
        result["api_version"] = APP_VERSION
        return result
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/cost")
def cost_endpoint(payload: InfrastructureRequest, request: Request) -> dict[str, Any]:
    """Return the existing deterministic infrastructure cost estimate."""

    try:
        result = CostEstimator.estimate_monthly_cost(payload.infrastructure.model_dump(exclude_none=True))
        result["request_id"] = request.state.request_id
        return result
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/v1/assist")
def assist_endpoint(payload: AssistRequest, request: Request) -> dict[str, Any]:
    """Return a structured, explainable cloud advisory response."""

    result = predict(
        payload.prompt,
        context=payload.context.model_dump(exclude_none=True) if payload.context else None,
        session_id=payload.session_id,
    )
    return {
        **result["advisory"],
        "session_id": result["session_id"],
        "turn_number": result["turn_number"],
        "request_id": request.state.request_id,
        "api_version": APP_VERSION,
    }


@app.post("/v1/cost/estimate")
def cost_v1_endpoint(payload: InfrastructureRequest, request: Request) -> dict[str, Any]:
    """Return a validated baseline, evidence variance, and comparison scenarios."""

    result = CostEstimator.estimate_monthly_cost(payload.infrastructure.model_dump(exclude_none=True))
    result["request_id"] = request.state.request_id
    result["api_version"] = APP_VERSION
    return result


@app.post("/v1/terraform/generate")
def terraform_endpoint(payload: TerraformRequest, request: Request) -> dict[str, Any]:
    """Generate a secure Terraform starter and static validation report."""

    result = CodeGenerator.generate_terraform_bundle(payload.requirement, {"aws_region": payload.aws_region})
    result["request_id"] = request.state.request_id
    result["api_version"] = APP_VERSION
    return result


@app.post("/v1/architecture/generate")
def architecture_endpoint(payload: ArchitectureRequest, request: Request) -> dict[str, Any]:
    """Generate accessible architecture metadata and Mermaid source."""

    result = ArchitectureDiagrammer.generate_architecture(payload.pattern)
    result["requirements"] = payload.requirements
    result["request_id"] = request.state.request_id
    result["api_version"] = APP_VERSION
    return result


@app.post("/v1/security/assess")
def security_endpoint(payload: SecurityAssessmentRequest, request: Request) -> dict[str, Any]:
    """Evaluate controls and corroborate findings against supplied text evidence."""

    result = SecurityScanner.scan_infrastructure(payload.context.model_dump(exclude_none=True))
    result["request_id"] = request.state.request_id
    result["api_version"] = APP_VERSION
    return result


@app.post("/v1/feedback", status_code=202)
def feedback_endpoint(payload: FeedbackRequest, request: Request) -> dict[str, Any]:
    """Record non-sensitive product quality feedback in structured service logs."""

    LOGGER.info(json.dumps({
        "event": "assistant_feedback",
        "request_id": payload.request_id or request.state.request_id,
        "feature": payload.feature,
        "rating": payload.rating,
        "has_comment": bool(payload.comment),
    }))
    return {
        "status": "recorded",
        "request_id": request.state.request_id,
        "message": "Thank you. The feedback was recorded without account credentials or infrastructure data.",
    }
