"""
Date/DateTime Standardization Utilities

Provides consistent ISO-8601 date/datetime handling with timezone awareness
across the entire API for professional-grade date management.
"""
from datetime import datetime, date, timezone, time
from typing import Optional, Union, Any

try:
    import pytz
    PYTZ_AVAILABLE = True
except ImportError:
    PYTZ_AVAILABLE = False


class DateTimeStandards:
    """
    Centralized date/datetime standards for the API
    
    Ensures consistent ISO-8601 formatting and timezone handling
    across all endpoints and data models.
    """
    
    # Standard timezone for the application
    DEFAULT_TIMEZONE = timezone.utc
    
    # ISO-8601 format strings
    DATE_FORMAT = "%Y-%m-%d"                    # 2024-01-15
    DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S%z"     # 2024-01-15T10:30:00+00:00
    DATETIME_FORMAT_Z = "%Y-%m-%dT%H:%M:%SZ"    # 2024-01-15T10:30:00Z (UTC)
    TIME_FORMAT = "%H:%M:%S"                    # 10:30:00
    
    @classmethod
    def now_utc(cls) -> datetime:
        """Get current UTC datetime"""
        return datetime.now(cls.DEFAULT_TIMEZONE)
    
    @classmethod
    def today_utc(cls) -> date:
        """Get current UTC date"""
        return cls.now_utc().date()
    
    @classmethod
    def format_datetime(cls, dt: Optional[datetime]) -> Optional[str]:
        """Format datetime to ISO-8601 string with timezone"""
        if dt is None:
            return None
        
        # Ensure timezone awareness
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=cls.DEFAULT_TIMEZONE)
        
        # Convert to UTC for consistency
        dt_utc = dt.astimezone(cls.DEFAULT_TIMEZONE)
        return dt_utc.strftime(cls.DATETIME_FORMAT_Z)
    
    @classmethod
    def format_date(cls, d: Optional[date]) -> Optional[str]:
        """Format date to ISO-8601 string"""
        if d is None:
            return None
        return d.strftime(cls.DATE_FORMAT)
    
    @classmethod
    def format_time(cls, t: Optional[time]) -> Optional[str]:
        """Format time to ISO-8601 string"""
        if t is None:
            return None
        return t.strftime(cls.TIME_FORMAT)
    
    @classmethod
    def parse_datetime(cls, dt_str: Optional[str]) -> Optional[datetime]:
        """Parse ISO-8601 datetime string to datetime object"""
        if not dt_str:
            return None
        
        try:
            # Handle various ISO-8601 formats
            if dt_str.endswith('Z'):
                # UTC timezone indicator
                dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
            else:
                dt = datetime.fromisoformat(dt_str)
            
            # Ensure timezone awareness
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=cls.DEFAULT_TIMEZONE)
            
            return dt
        except (ValueError, TypeError):
            return None
    
    @classmethod
    def parse_date(cls, date_str: Optional[str]) -> Optional[date]:
        """Parse ISO-8601 date string to date object"""
        if not date_str:
            return None
        
        try:
            return date.fromisoformat(date_str)
        except (ValueError, TypeError):
            return None
    
    @classmethod
    def parse_time(cls, time_str: Optional[str]) -> Optional[time]:
        """Parse ISO-8601 time string to time object"""
        if not time_str:
            return None
        
        try:
            return time.fromisoformat(time_str)
        except (ValueError, TypeError):
            return None
    
    @classmethod
    def get_timezone_info(cls, tz_name: Optional[str] = None) -> dict:
        """Get timezone information for documentation"""
        if not tz_name:
            tz_name = "UTC"

        if not PYTZ_AVAILABLE:
            return {
                "timezone": "UTC",
                "utc_offset": "+0000",
                "is_dst": False,
                "abbreviation": "UTC"
            }

        try:
            tz = pytz.timezone(tz_name)
            now = cls.now_utc()
            localized = tz.normalize(now.astimezone(tz))

            return {
                "timezone": tz_name,
                "utc_offset": localized.strftime("%z"),
                "is_dst": bool(localized.dst()),
                "abbreviation": localized.strftime("%Z")
            }
        except Exception:
            return {
                "timezone": "UTC",
                "utc_offset": "+0000",
                "is_dst": False,
                "abbreviation": "UTC"
            }


def datetime_serializer(dt: Optional[datetime]) -> Optional[str]:
    """Pydantic field serializer for datetime fields"""
    return DateTimeStandards.format_datetime(dt)


def date_serializer(d: Optional[date]) -> Optional[str]:
    """Pydantic field serializer for date fields"""
    return DateTimeStandards.format_date(d)


def time_serializer(t: Optional[time]) -> Optional[str]:
    """Pydantic field serializer for time fields"""
    return DateTimeStandards.format_time(t)


def datetime_validator(v: Any) -> Optional[datetime]:
    """Pydantic field validator for datetime fields"""
    if v is None:
        return None
    
    if isinstance(v, datetime):
        # Ensure timezone awareness
        if v.tzinfo is None:
            v = v.replace(tzinfo=DateTimeStandards.DEFAULT_TIMEZONE)
        return v
    
    if isinstance(v, str):
        return DateTimeStandards.parse_datetime(v)
    
    raise ValueError(f"Invalid datetime value: {v}")


def date_validator(v: Any) -> Optional[date]:
    """Pydantic field validator for date fields.

    Behavior:
    - None -> None (clears the date)
    - date instance -> returned as-is
    - string -> must be a valid ISO date (YYYY-MM-DD); invalid strings raise ValueError to trigger 422
    - other types -> raise ValueError
    """
    if v is None:
        return None

    if isinstance(v, date):
        return v

    if isinstance(v, str):
        parsed = DateTimeStandards.parse_date(v)
        if parsed is None:
            raise ValueError(f"Invalid date value: {v}")
        return parsed

    raise ValueError(f"Invalid date value: {v}")


def time_validator(v: Any) -> Optional[time]:
    """Pydantic field validator for time fields"""
    if v is None:
        return None
    
    if isinstance(v, time):
        return v
    
    if isinstance(v, str):
        return DateTimeStandards.parse_time(v)
    
    raise ValueError(f"Invalid time value: {v}")


# Simplified JSON Schema information for OpenAPI documentation
DATETIME_JSON_SCHEMA = {
    "type": "string",
    "format": "date-time",
    "pattern": r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{3})?Z$",
    "description": "ISO-8601 datetime in UTC timezone (YYYY-MM-DDTHH:MM:SSZ)",
    "examples": [
        "2024-01-15T10:30:00Z",
        "2024-07-04T14:45:30Z",
        "2024-12-25T00:00:00Z"
    ]
}

DATE_JSON_SCHEMA = {
    "type": "string",
    "format": "date",
    "pattern": r"^\d{4}-\d{2}-\d{2}$",
    "description": "ISO-8601 date format (YYYY-MM-DD)",
    "examples": [
        "2024-01-15",
        "2024-07-04",
        "2024-12-25"
    ]
}

TIME_JSON_SCHEMA = {
    "type": "string",
    "format": "time",
    "pattern": r"^\d{2}:\d{2}:\d{2}$",
    "description": "ISO-8601 time format (HH:MM:SS)",
    "examples": [
        "10:30:00",
        "14:45:30",
        "00:00:00"
    ]
}


# Common timezone constants for documentation
COMMON_TIMEZONES = {
    "UTC": "Coordinated Universal Time",
    "America/New_York": "Eastern Time (US & Canada)",
    "America/Chicago": "Central Time (US & Canada)",
    "America/Denver": "Mountain Time (US & Canada)",
    "America/Los_Angeles": "Pacific Time (US & Canada)",
    "Europe/London": "Greenwich Mean Time",
    "Europe/Paris": "Central European Time",
    "Asia/Tokyo": "Japan Standard Time",
    "Australia/Sydney": "Australian Eastern Time"
} if PYTZ_AVAILABLE else {
    "UTC": "Coordinated Universal Time"
}


def get_timezone_documentation() -> dict:
    """Get comprehensive timezone documentation for API docs"""
    return {
        "timezone_handling": {
            "description": "All datetime fields use ISO-8601 format with timezone awareness",
            "default_timezone": "UTC",
            "format": "YYYY-MM-DDTHH:MM:SSZ",
            "examples": {
                "utc": "2024-01-15T10:30:00Z",
                "with_offset": "2024-01-15T10:30:00+05:00"
            }
        },
        "date_handling": {
            "description": "All date fields use ISO-8601 date format",
            "format": "YYYY-MM-DD",
            "examples": ["2024-01-15", "2024-07-04", "2024-12-25"]
        },
        "time_handling": {
            "description": "All time fields use ISO-8601 time format",
            "format": "HH:MM:SS",
            "examples": ["10:30:00", "14:45:30", "00:00:00"]
        },
        "common_timezones": COMMON_TIMEZONES,
        "best_practices": [
            "Always store datetimes in UTC",
            "Convert to user timezone for display only",
            "Use ISO-8601 format for all date/time fields",
            "Include timezone information when relevant"
        ]
    }
