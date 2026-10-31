from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class CleanMode(str, Enum):
    AI_ONLY = "ai_only"
    ALL = "all"


class MetadataField(BaseModel):
    key: str
    value: Any


class AIMarker(BaseModel):
    name: str
    source: str
    description: str


class ImageInfo(BaseModel):
    format: str | None = None
    width: int
    height: int
    mode: str = "RGB"
    has_transparency: bool = False


class MetadataExtractionStatus(BaseModel):
    available: bool
    error: str | None = None


class AIMarkerSignal(BaseModel):
    tool: str
    matched_markers: list[str]
    evidence_type: str
    description: str | None = None


class AIAnalysis(BaseModel):
    detected: bool
    signal_count: int
    signals: list[AIMarkerSignal]


class C2PAAnalysis(BaseModel):
    available: bool
    has_manifest: bool
    active_manifest: str | None = None
    manifest_count: int = 0
    digital_source_type: str | None = None
    recorded_actions: list[str] = []
    ingredients: list[Any] = []
    assertions: list[Any] = []
    signature_info: dict[str, Any] = {}
    validation_state: str | None = None
    validation_results: Any = None
    raw_manifest: dict[str, Any] | None = None
    error: str | None = None


class Verdict(BaseModel):
    kind: str = "no-ai-signals"  # "ai-signals" or "clean"
    headline: str = "No known AI metadata detected"
    detail: str = "No known AI generator signatures were detected in readable metadata."


class GroupField(BaseModel):
    label: str
    value: Any


class MetadataGroup(BaseModel):
    id: str
    title: str
    fields: list[GroupField] = []


class MetadataCheckResponse(BaseModel):
    filename: str
    format: str | None = None
    width: int | None = None
    height: int | None = None
    file_size_bytes: int = 0
    metadata_count: int = 0
    metadata: list[dict[str, Any]] = []
    ai_marker_count: int = 0
    ai_markers: list[dict[str, Any]] = []
    warnings: list[str] = []
    verdict: Verdict | None = None
    ai_signals: dict[str, Any] | None = None
    groups: list[MetadataGroup] = []
    ai_analysis: AIAnalysis | None = None
    c2pa: C2PAAnalysis | None = None
    image: ImageInfo | None = None
    metadata_extraction: MetadataExtractionStatus | None = None
    raw_metadata: dict[str, Any] = {}


class CompleteMetadataResponse(BaseModel):
    image: ImageInfo
    metadata: dict[str, Any]
    metadata_extraction: MetadataExtractionStatus
    c2pa: C2PAAnalysis
    ai_analysis: AIAnalysis
