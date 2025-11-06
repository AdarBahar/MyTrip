"""
Schemas for legacy-compatible batch synchronization endpoint
- POST /location/api/batch-sync
"""
from __future__ import annotations
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, model_validator


class BatchSyncRequest(BaseModel):
    sync_id: str = Field(..., min_length=1, max_length=200)
    device_id: str = Field(..., min_length=1, max_length=100)
    user_name: str = Field(..., min_length=1, max_length=100)

    # Accept either 'part' or 'part_number'
    part: Optional[int] = Field(None, ge=1)
    part_number: Optional[int] = Field(None, ge=1)
    total_parts: int = Field(..., ge=1)

    # Be permissive: accept arbitrary record dicts; validate in endpoint
    records: List[dict] = Field(..., min_length=1)

    @model_validator(mode="before")
    @classmethod
    def _normalize_part(cls, data: dict):
        if not isinstance(data, dict):
            return data
        if data.get("part") is None and data.get("part_number") is not None:
            data["part"] = data["part_number"]
        return data

    @model_validator(mode="after")
    def _require_part(self):
        if self.part is None:
            raise ValueError("'part' (or 'part_number') is required")
        return self


class ProcessingResults(BaseModel):
    location: int
    driving: int
    errors: int
    details: list[str]


class BatchSyncResponse(BaseModel):
    status: Literal["success", "error"]
    message: str
    sync_id: str
    part: int
    total_parts: int
    records_processed: int
    storage_mode: str
    sync_complete: bool
    processing_results: ProcessingResults
    request_id: str

