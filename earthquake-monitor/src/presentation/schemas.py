from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CreateEarthquakeSchema(BaseModel):
    latitude: float = Field(..., ge=-90, le=90, description="Latitude in degrees")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude in degrees")
    depth: float = Field(..., ge=0, description="Depth in kilometers")
    magnitude_value: float = Field(..., ge=0, le=12, description="Magnitude value")
    magnitude_scale: str = Field(default="moment", description="Magnitude scale type")
    occurred_at: Optional[datetime] = Field(
        None, description="When the earthquake occurred"
    )
    source: str = Field(default="USGS", description="Data source")


class EarthquakeResponseSchema(BaseModel):
    id: str
    message: str
