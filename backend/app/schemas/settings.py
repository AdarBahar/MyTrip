"""
User settings schemas
"""
from typing import Any, Dict, Optional
from pydantic import BaseModel


class SettingsResponse(BaseModel):
    settings: Dict[str, Any]


class SettingsUpdate(BaseModel):
    show_country_suffix: Optional[bool] = None

