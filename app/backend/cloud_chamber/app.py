"""FastAPI application skeleton for local Cloud Chamber services."""

from __future__ import annotations

from fastapi import FastAPI

from cloud_chamber.cli import ENGINE_NOTE

app = FastAPI(
    title="Cloud Chamber Backend",
    summary="Local backend API for Cloud Chamber CM1 experiment workflows.",
    version="0.1.0",
)


@app.get("/health")
def health() -> dict[str, str]:
    """Return a lightweight readiness response that does not require CM1."""
    return {
        "status": "ok",
        "product": "Cloud Chamber",
        "engine_note": ENGINE_NOTE,
    }
