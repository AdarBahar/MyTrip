"""
Stop schemas
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

from app.models.stop import StopKind


class StopBase(BaseModel):
    """Base stop schema"""
    place_id: str
    seq: int = Field(..., gt=0)
    kind: StopKind
    fixed: bool = False
    notes: Optional[str] = None


class StopCreate(StopBase):
    """Schema for creating a stop"""
    pass


class StopUpdate(BaseModel):
    """Schema for updating a stop"""
    place_id: Optional[str] = None
    seq: Optional[int] = Field(None, gt=0)
    kind: Optional[StopKind] = None
    fixed: Optional[bool] = None
    notes: Optional[str] = None


class Stop(StopBase):
    """Stop schema"""
    model_config = ConfigDict(from_attributes=True)

    id: str
    day_id: str
    trip_id: str
    created_at: datetime
    updated_at: datetime


class StopList(BaseModel):
    """Stop list schema"""
    stops: List[Stop]


class StopsUpdate(BaseModel):
    """Schema for updating multiple stops"""
    stops: List[StopCreate] = Field(..., min_items=2)

    @classmethod
    def validate_stops(cls, v):
        """Validate that there's exactly one start and one end"""
        starts = [s for s in v if s.kind == StopKind.START]
        ends = [s for s in v if s.kind == StopKind.END]

        if len(starts) != 1:
            raise ValueError("Exactly one start stop is required")
        if len(ends) != 1:
            raise ValueError("Exactly one end stop is required")
        if starts[0].seq != 1:
            raise ValueError("Start stop must have seq=1")
        if not starts[0].fixed:
            raise ValueError("Start stop must be fixed")
        if not ends[0].fixed:
            raise ValueError("End stop must be fixed")

        return v