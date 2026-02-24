from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


# -------------------------
# Chat
# -------------------------

class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    site_id: int
    node_id: Optional[int] = None
    message: str
    history: List[ChatMessage] = []


class ChatResponse(BaseModel):
    reply: str


# -------------------------
# Voice
# -------------------------

class VoiceChatResponse(BaseModel):
    user_text: str
    bot_text: str
    audio_base64: str
    audio_format: str


# -------------------------
# Site Listing
# -------------------------

class NearbySiteResponse(BaseModel):
    id: int
    name: str
    distance_meters: float
    inside_geofence: bool


class SiteImageResponse(BaseModel):
    id: int
    image_url: str
    display_order: int


class NodeResponse(BaseModel):
    id: int
    name: str
    latitude: float
    longitude: float
    sequence_order: int


class SiteDetailResponse(BaseModel):
    id: int
    name: str
    summary: Optional[str]
    history: Optional[str]
    fun_facts: Optional[str]
    helpline_number: Optional[str]
    static_map_url: Optional[str]
    intro_video_url: Optional[str]
    rating: float
    upvotes: int
    images: List[SiteImageResponse]
    nodes: List[NodeResponse]

    class Config:
        from_attributes = True


# -------------------------
# Trip
# -------------------------

class StartTripRequest(BaseModel):
    user_id: int
    qr_value: str


class StartTripResponse(BaseModel):
    message: str
    trip_id: int


class EndTripRequest(BaseModel):
    trip_id: int


class EndTripResponse(BaseModel):
    message: str


# -------------------------
# Recommendation
# -------------------------

class RecommendationResponse(BaseModel):
    id: int
    type: str
    name: str
    description: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]