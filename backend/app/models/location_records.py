"""
SQLAlchemy models mapping to baharc5_location schema (subset needed for Phase 1)

We intentionally mirror the legacy PHP schema naming and types where practical.
These models are bound to the separate location database via LocationBase.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
    Index,
)
from sqlalchemy.orm import relationship

from app.core.location_database import LocationBase


class LocationUser(LocationBase):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), nullable=False, unique=True, index=True)
    display_name = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    is_active = Column(Boolean, nullable=False, server_default="1")

    devices = relationship("Device", back_populates="user")


class Device(LocationBase):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(String(100), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    device_name = Column(String(100), nullable=True)
    first_seen = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_seen = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    is_active = Column(Boolean, nullable=False, server_default="1")

    user = relationship("LocationUser", back_populates="devices")

    __table_args__ = (
        Index("idx_device_user", "user_id", "device_id", unique=False),
    )


class LocationRecord(LocationBase):
    __tablename__ = "location_records"

    # Use Integer for cross-DB autoincrement compatibility in tests (SQLite)
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign-ish references (not enforced to external main DB)
    user_id = Column(Integer, nullable=False, index=True)
    device_id = Column(String(100), nullable=False, index=True)

    # Timestamps
    server_time = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    client_time = Column(BigInteger, nullable=True)
    client_time_iso = Column(String(40), nullable=True)

    # Geo + telemetry
    latitude = Column(Numeric(10, 8), nullable=False, index=True)
    longitude = Column(Numeric(11, 8), nullable=False, index=True)
    accuracy = Column(Float, nullable=True)
    altitude = Column(Float, nullable=True)
    speed = Column(Float, nullable=True)
    bearing = Column(Float, nullable=True)
    battery_level = Column(Integer, nullable=True)
    network_type = Column(String(20), nullable=True)
    provider = Column(String(20), nullable=True)

    # Request context
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)

    # Source
    source_type = Column(String(20), nullable=False, server_default="realtime")
    batch_sync_id = Column(String(50), nullable=True)

    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_location_user_time", "user_id", "server_time"),
        Index("idx_location_device_time", "device_id", "server_time"),
        Index("idx_location_coords", "latitude", "longitude"),
    )



class DrivingRecord(LocationBase):
    __tablename__ = "driving_records"

    # Integer PK for cross-dialect autoincrement compatibility in tests (SQLite)
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign-ish references
    user_id = Column(Integer, nullable=False, index=True)
    device_id = Column(String(100), nullable=False, index=True)

    # Event info
    event_type = Column(String(20), nullable=False)  # start | data | stop

    # Timestamps
    server_time = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    client_time = Column(BigInteger, nullable=True)

    # Geo + telemetry
    latitude = Column(Numeric(10, 8), nullable=False, index=True)
    longitude = Column(Numeric(11, 8), nullable=False, index=True)
    accuracy = Column(Float, nullable=True)
    altitude = Column(Float, nullable=True)
    speed = Column(Float, nullable=True)
    bearing = Column(Float, nullable=True)

    # Trip association
    trip_id = Column(String(100), nullable=True)

    # Request context
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)

    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_driving_user_time", "user_id", "server_time"),
        Index("idx_driving_device_time", "device_id", "server_time"),
    )

