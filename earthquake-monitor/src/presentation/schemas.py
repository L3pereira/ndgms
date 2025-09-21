from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


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


class LocationSchema(BaseModel):
    latitude: float
    longitude: float
    depth: float


class MagnitudeSchema(BaseModel):
    value: float
    scale: str
    alert_level: str
    description: str
    is_significant: bool


class EarthquakeDetailSchema(BaseModel):
    id: str
    location: LocationSchema
    magnitude: MagnitudeSchema
    occurred_at: datetime
    source: str
    is_reviewed: bool
    affected_radius_km: float
    requires_immediate_alert: bool
    impact_assessment: dict

    model_config = ConfigDict(from_attributes=True)


class EarthquakeListItemSchema(BaseModel):
    id: str
    latitude: float
    longitude: float
    depth: float
    magnitude_value: float
    magnitude_scale: str
    alert_level: str
    occurred_at: datetime
    source: str
    is_reviewed: bool

    model_config = ConfigDict(from_attributes=True)


class PaginationSchema(BaseModel):
    total: int
    page: int
    size: int
    pages: int


class EarthquakeListResponseSchema(BaseModel):
    earthquakes: List[EarthquakeListItemSchema]
    pagination: PaginationSchema


class EarthquakeFiltersSchema(BaseModel):
    min_magnitude: Optional[float] = Field(None, ge=0, le=12)
    max_magnitude: Optional[float] = Field(None, ge=0, le=12)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    radius_km: Optional[float] = Field(None, ge=0, le=20000)
    is_reviewed: Optional[bool] = None
    source: Optional[str] = None
    page: int = Field(1, ge=1)
    size: int = Field(50, ge=1, le=1000)
