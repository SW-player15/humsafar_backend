# app/routers/video_proxy.py
# Pure proxy — forwards /generate-video and /video-status/* to the
# humsafar-video-service. No FFmpeg, no Supabase, no business logic.

import logging
import os

import httpx
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(tags=["video-proxy"])

# Set VIDEO_SERVICE_URL in Render env vars:
#   e.g. https://humsafar-video-service.onrender.com
VIDEO_SERVICE_URL = os.getenv("VIDEO_SERVICE_URL", "").rstrip("/")
_PROXY_TIMEOUT    = 30.0   # seconds — just for the HTTP call, not FFmpeg


def _video_service_url() -> str:
    if not VIDEO_SERVICE_URL:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="VIDEO_SERVICE_URL is not configured on this server",
        )
    return VIDEO_SERVICE_URL


# ── Request / Response models (mirror video-service schema) ──────────────────

class GenerateVideoRequest(BaseModel):
    prompt:        str
    bot_text:      str
    site_id:       str
    site_name:     str
    language_code: str = "en-IN"


class GenerateVideoResponse(BaseModel):
    job_id: str
    status: str


class VideoStatusResponse(BaseModel):
    job_id:    str
    status:    str
    progress:  int        = 0
    video_url: str | None = None
    message:   str        = ""


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/generate-video", response_model=GenerateVideoResponse)
async def generate_video(req: GenerateVideoRequest):
    """
    Proxy: forward to video-service POST /generate.
    Returns job_id for the client to poll.
    """
    base = _video_service_url()
    logger.info(
        f"[Proxy] POST /generate-video → {base}/generate "
        f"site={req.site_name}"
    )

    async with httpx.AsyncClient(timeout=_PROXY_TIMEOUT) as client:
        try:
            resp = await client.post(
                f"{base}/generate",
                json=req.model_dump(),
            )
        except httpx.RequestError as exc:
            logger.error(f"[Proxy] Connection error: {exc}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Video service unreachable: {exc}",
            )

    if resp.status_code != 200:
        logger.error(f"[Proxy] Video service error {resp.status_code}: {resp.text}")
        raise HTTPException(
            status_code=resp.status_code,
            detail=f"Video service error: {resp.text}",
        )

    data = resp.json()
    logger.info(f"[Proxy] job_id={data.get('job_id')} enqueued")
    return GenerateVideoResponse(**data)


@router.get("/video-status/{job_id}", response_model=VideoStatusResponse)
async def video_status(job_id: str):
    """
    Proxy: forward to video-service GET /status/{job_id}.
    """
    base = _video_service_url()
    logger.info(f"[Proxy] GET /video-status/{job_id} → {base}/status/{job_id}")

    async with httpx.AsyncClient(timeout=_PROXY_TIMEOUT) as client:
        try:
            resp = await client.get(f"{base}/status/{job_id}")
        except httpx.RequestError as exc:
            logger.error(f"[Proxy] Connection error: {exc}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Video service unreachable: {exc}",
            )

    if resp.status_code == 404:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job not found: {job_id}",
        )

    if resp.status_code != 200:
        logger.error(f"[Proxy] Video service error {resp.status_code}: {resp.text}")
        raise HTTPException(
            status_code=resp.status_code,
            detail=f"Video service error: {resp.text}",
        )

    return VideoStatusResponse(**resp.json())