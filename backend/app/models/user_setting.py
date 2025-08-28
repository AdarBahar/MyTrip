"""
UserSetting model
"""
from sqlalchemy import Column, String, JSON, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class UserSetting(BaseModel):
    """Per-user settings key-value store"""

    __tablename__ = "user_settings"

    user_id = Column(String(26), ForeignKey("users.id"), nullable=False, index=True)
    key = Column(String(64), nullable=False)
    value = Column(JSON, nullable=True)

    # Relationships
    user = relationship("User")

    __table_args__ = (
        UniqueConstraint("user_id", "key", name="uq_user_setting_user_key"),
    )

    def __repr__(self):
        return f"<UserSetting(user_id={self.user_id}, key={self.key})>"

