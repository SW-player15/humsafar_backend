import logging

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from app.schemas import VoiceChatResponse
from app.services import voice_orchestrator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/voice-chat", tags=["voice"])


@router.post("", response_model=VoiceChatResponse)
async def voice_chat(
    audio:     UploadFile = File(..., description="WAV audio from Android AudioRecord"),
    site_name: str        = Form(..., description="Heritage site name"),
    site_id:   str        = Form(..., description="Heritage site ID"),
    language:  str        = Form(..., description="BCP-47 code, e.g. en-IN"),
    lang_name: str        = Form(..., description="ENGLISH | HINDI | HINGLISH"),
):
    if audio.content_type and not audio.content_type.startswith("audio/"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Expected audio/*, received {audio.content_type}"
        )

    audio_bytes = await audio.read()
    if len(audio_bytes) < 1000:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Audio too short — minimum ~1 second required"
        )

    logger.info(
        f"[/voice-chat] site='{site_name}' lang={lang_name}({language}) "
        f"audio={len(audio_bytes)}B"
    )

    try:
        result = await voice_orchestrator.run(
            audio_bytes   = audio_bytes,
            site_name     = site_name,
            site_id       = site_id,
            language_code = language,
            lang_name     = lang_name.upper(),
        )
    except RuntimeError as exc:
        msg = str(exc)
        logger.error(f"[/voice-chat] Pipeline failed: {msg}")

        if msg.startswith("STT_FAILED"):
            raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail=msg)
        if msg.startswith("LLM_FAILED"):
            raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail=msg)
        if msg.startswith("TTS_FAILED"):
            raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail=msg)
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail=msg)

    return VoiceChatResponse(
        user_text    = result.user_text,
        bot_text     = result.bot_text,
        audio_base64 = result.audio_base64,
        audio_format = "wav",
    )