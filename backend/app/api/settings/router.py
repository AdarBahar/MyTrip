"""
Settings API router
"""
from typing import Dict
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.user_setting import UserSetting
from app.schemas.settings import SettingsResponse, SettingsUpdate

router = APIRouter()


def _load_user_settings(db: Session, user_id: str) -> Dict[str, object]:
    items = db.query(UserSetting).filter(UserSetting.user_id == user_id).all()
    out: Dict[str, object] = {}
    for s in items:
        out[s.key] = s.value
    return out


@router.get("/user/settings", response_model=SettingsResponse)
async def get_user_settings(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    settings = _load_user_settings(db, current_user.id)
    return SettingsResponse(settings=settings)


@router.patch("/user/settings", response_model=SettingsResponse)
async def update_user_settings(update: SettingsUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Upsert known settings
    updates = update.model_dump(exclude_none=True)
    for key, val in updates.items():
        existing = db.query(UserSetting).filter(UserSetting.user_id == current_user.id, UserSetting.key == key).first()
        if existing:
            existing.value = val
        else:
            item = UserSetting(user_id=current_user.id, key=key, value=val)
            db.add(item)
    db.commit()
    return SettingsResponse(settings=_load_user_settings(db, current_user.id))

