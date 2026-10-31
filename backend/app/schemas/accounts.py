from datetime import datetime
from pydantic import BaseModel, Field

class UserResponse(BaseModel):
    id: str
    email: str | None = None
    name: str | None = None
    picture: str | None = None

class ActivityResponse(BaseModel):
    operation: str
    filename: str
    marker_count: int | None = Field(default=None, ge=0)
    created_at: datetime

class EndpointCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)

class EndpointUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=80)

class EndpointResponse(BaseModel):
    endpoint_id: str
    name: str
    created_at: datetime
    updated_at: datetime
    image_count: int = 0

class EndpointImageResponse(BaseModel):
    image_id: str
    filename: str
    format: str
    marker_count: int
    size_bytes: int
    created_at: datetime
    url: str
