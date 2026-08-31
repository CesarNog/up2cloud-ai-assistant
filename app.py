"""Vercel-compatible FastAPI entry point for the UP2CLOUD assistant."""

from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from enhanced_features import CostEstimator
from model import predict


STATIC_INDEX = Path(__file__).parent / "static" / "index.html"

app = FastAPI(
    title="UP2CLOUD AI Cloud Engineering Assistant",
    version="2.0.0",
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
