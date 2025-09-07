"""
Places API router
"""
from typing import Optional, List, Dict, Any, Set, Union
from fastapi import APIRouter, Depends, HTTPException, Query, Response, Request
from sqlalchemy.orm import Session
import logging
from datetime import datetime, timedelta
import httpx
from urllib.parse import quote
import time
from functools import lru_cache

from app.core.database import get_db
from app.core.auth import get_current_user
from app.core.config import settings
from app.models.user import User
from app.models.place import Place, OwnerType
from app.schemas.place import (
    PlaceCreate, PlaceUpdate, PlaceSchema,
    PlaceSearchResult, PlaceSearchItem, GeocodingResult, PlaceSearchPaginatedResponse
)
from app.schemas.pagination import create_paginated_response, get_base_url
from fastapi.encoders import jsonable_encoder

router = APIRouter()

# Utilities for ETag generation
import hashlib

# Simple in-memory cache for place search results
class PlaceSearchCache:
    def __init__(self, ttl_seconds=300):  # 5 minutes TTL
        self.cache = {}
        self.ttl_seconds = ttl_seconds

    def _make_key(self, query: str, lat: Optional[float], lon: Optional[float], limit: int) -> str:
        """Create cache key from search parameters"""
        return f"{query.lower().strip()}:{lat}:{lon}:{limit}"

    def get(self, query: str, lat: Optional[float], lon: Optional[float], limit: int) -> Optional[List[Dict]]:
        """Get cached results if still valid"""
        key = self._make_key(query, lat, lon, limit)
        if key in self.cache:
            result, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl_seconds:
                return result
            else:
                # Expired, remove from cache
                del self.cache[key]
        return None

    def set(self, query: str, lat: Optional[float], lon: Optional[float], limit: int, results: List[Dict]):
        """Cache search results"""
        key = self._make_key(query, lat, lon, limit)
        self.cache[key] = (results, time.time())

        # Simple cleanup: remove expired entries if cache gets too large
        if len(self.cache) > 1000:
            current_time = time.time()
            expired_keys = [k for k, (_, ts) in self.cache.items() if current_time - ts >= self.ttl_seconds]
            for k in expired_keys:
                del self.cache[k]

# Global cache instance
place_search_cache = PlaceSearchCache()

# ---------------- Address Normalization Utilities ---------------- #

def _extract_components(meta: dict) -> dict:
    comps = {}
    if not isinstance(meta, dict):
        return comps
    raw = meta.get("raw") if isinstance(meta.get("raw"), dict) else meta
    props = raw.get("properties", {}) if isinstance(raw, dict) else {}

    # Try multiple keys across providers
    def pick(*keys):
        for k in keys:
            v = props.get(k) if k in props else raw.get(k)
            if v:
                return v
        return None

    comps["street"] = pick("street", "road", "thoroughfare")
    comps["house_number"] = pick("house_number", "housenumber", "address_number")
    comps["city"] = pick("city", "town", "village", "municipality", "locality")
    comps["state_code"] = pick("state_code")
    comps["state"] = pick("state", "region")
    comps["postcode"] = pick("postcode", "zip", "postal_code")
    comps["country"] = pick("country")
    comps["country_code"] = pick("country_code", "cc")

    # Clean
    if isinstance(comps.get("state_code"), str):
        comps["state_code"] = comps["state_code"].upper()
    if isinstance(comps.get("country_code"), str):
        comps["country_code"] = comps["country_code"].upper()

    return {k: v for k, v in comps.items() if v}


def _format_display_short(address: str, comps: dict, include_country: bool = False) -> str:
    """Build a short display string: street number, city, state (US) without ZIP; optional country."""
    # Prefer structured
    street = comps.get("street")
    number = comps.get("house_number")
    city = comps.get("city")
    state = comps.get("state_code") or comps.get("state")
    country = comps.get("country_code") or comps.get("country")

    parts = []
    if street:
        parts.append("%s%s" % (street, f" {number}" if number else ""))
    if city or state:
        cs = ", ".join([p for p in [city, state] if p])
        if cs:
            parts.append(cs)
    if include_country and country and (country.upper() != "US" and country.upper() != "USA"):
        parts.append(country)
    if parts:
        return ", ".join(parts)

    # Fallback: return original address truncated without ZIP
    try:
        trimmed = (address or "").split(",")
        trimmed = [p.strip() for p in trimmed if p.strip()]
        if len(trimmed) >= 3:
            # Remove numeric ZIP portion from the third segment
            seg2 = trimmed[2]
            token = next((t for t in seg2.split() if any(c.isalpha() for c in t)), seg2)
            trimmed[2] = token
        return ", ".join(trimmed[:3]) if trimmed else address
    except Exception:
        return address


def _normalize_address(address: str, meta: dict) -> dict:
    comps = _extract_components(meta or {})
    display_short = _format_display_short(address, comps, include_country=False)
    return {
        "components": comps,
        "display_short": display_short,
    }


def _quote_etag(tag: str) -> str:
    if tag.startswith('"') and tag.endswith('"'):
        return tag
    return '"' + tag + '"'



@router.get("/search", response_model=Union[PlaceSearchPaginatedResponse, PlaceSearchResult])
async def search_places(
    request: Request,
    query: str = Query(..., min_length=2, description="Search term (minimum 2 characters)"),
    lat: Optional[float] = Query(None, ge=-90, le=90, description="Latitude for proximity search"),
    lon: Optional[float] = Query(None, ge=-180, le=180, description="Longitude for proximity search"),
    radius: Optional[int] = Query(50000, ge=1, description="Search radius in meters"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results"),
    format: Optional[str] = Query("modern", regex="^(legacy|modern)$", description="Response format"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    **Enhanced Place Search with Modern Pagination**

    Search for places by name using MapTiler geocoding API with aggressive caching and modern pagination.

    **Features:**
    - Aggressive caching (5-minute TTL) for improved performance
    - Proximity-based search with lat/lon parameters
    - Integration with user's saved places
    - Modern pagination with navigation links

    **Parameters:**
    - `query`: Search term (minimum 2 characters)
    - `lat/lon`: Optional coordinates for proximity-based results
    - `radius`: Search radius in meters (default: 50km)
    - `limit`: Maximum results (1-50, default: 10)
    - `format`: Response format - 'modern' (default) or 'legacy'

    **Modern Response Format:**
    ```json
    {
      "data": [...],
      "meta": {
        "current_page": 1,
        "per_page": 10,
        "total_items": 25,
        "total_pages": 3,
        "has_next": true,
        "has_prev": false
      },
      "links": {
        "self": "http://localhost:8000/places/search?query=jerusalem&page=1",
        "first": "http://localhost:8000/places/search?query=jerusalem&page=1",
        "next": "http://localhost:8000/places/search?query=jerusalem&page=2"
      }
    }
    ```

    **Returns:** List of candidate places without creating database records.
    """
    if not settings.MAPTILER_API_KEY:
        # Return empty but valid response if no API key configured
        return PlaceSearchResult(places=[], total=0)

    # Check cache first
    cached_results = place_search_cache.get(query, lat, lon, limit)
    if cached_results is not None:
        logging.info(f"Place search cache hit for query: {query}")
        return PlaceSearchResult(places=cached_results, total=len(cached_results))

    # Build MapTiler Geocoding API request (Mapbox-compatible style)
    params: Dict[str, Any] = {
        "key": settings.MAPTILER_API_KEY,
        "limit": limit,
        "autocomplete": True,
    }
    if lat is not None and lon is not None:
        params["proximity"] = f"{lon},{lat}"  # MapTiler expects lon,lat
    if radius is not None:
        params["radius"] = radius

    safe_query = quote(query)
    url = f"https://api.maptiler.com/geocoding/{safe_query}.json"

    places: List[PlaceSearchItem] = []
    total = 0

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url, params=params, timeout=10.0)
            resp.raise_for_status()
            data = resp.json()

            # MapTiler returns features in GeoJSON FeatureCollection
            features = data.get("features", [])
            total = len(features)
            # Preload user's saved places for matching
            saved_places = db.query(Place).filter(Place.owner_type == OwnerType.USER, Place.owner_id == current_user.id).all()

            def is_match(saved: Place, feat: dict, name: str, lat_v: float, lon_v: float) -> bool:
                # Prefer provider_place_id if present in either side
                feat_id = feat.get("id") or feat.get("place_id") or feat.get("properties", {}).get("id")
                if feat_id and saved.provider_place_id and str(saved.provider_place_id) == str(feat_id):
                    return True
                # Otherwise, compare name and proximity (~75 meters)
                try:
                    from math import radians, sin, cos, sqrt, atan2
                    R = 6371000.0
                    dlat = radians(float(saved.lat) - lat_v)
                    dlon = radians(float(saved.lon) - lon_v)
                    a = sin(dlat/2)**2 + cos(radians(lat_v)) * cos(radians(float(saved.lat))) * sin(dlon/2)**2
                    c = 2 * atan2(sqrt(a), sqrt(1-a))
                    dist_m = R * c
                except Exception:
                    dist_m = 999999
                name_match = saved.name.strip().lower() == name.strip().lower()
                return name_match and dist_m < 75

            for f in features:
                geom = f.get("geometry", {})
                coords = (geom.get("coordinates") or [None, None])
                lon_val = float(coords[0]) if coords and len(coords) >= 2 else None
                lat_val = float(coords[1]) if coords and len(coords) >= 2 else None
                if lat_val is None or lon_val is None:
                    continue
                name = f.get("text") or f.get("place_name") or f.get("properties", {}).get("name") or "Unknown"
                is_saved_flag = any(is_match(sp, f, name, lat_val, lon_val) for sp in saved_places)
                place = PlaceSearchItem(
                    id=f.get("id") or f.get("place_id") or f.get("properties", {}).get("id", "unknown"),
                    name=name,
                    address=f.get("place_name") or f.get("properties", {}).get("address"),
                    lat=lat_val,
                    lon=lon_val,
                    meta={"source": "maptiler", "raw": f, "normalized": _normalize_address(f.get("place_name") or name, {"raw": f})},
                    is_saved=is_saved_flag,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
                places.append(place)
        except httpx.HTTPError as e:
            logging.warning(f"MapTiler search failed: {e}")
            # On failure, return empty result to not break UX
            return PlaceSearchResult(places=[], total=0)

    # Cache the results for future requests
    place_search_cache.set(query, lat, lon, limit, places)
    logging.info(f"Place search cached for query: {query}, found {len(places)} results")

    # Support both legacy and modern response formats
    if format == "legacy":
        return PlaceSearchResult(places=places, total=total)

    # Modern response with navigation links
    # For search results, we treat it as a single page since external API doesn't support pagination
    base_url = get_base_url(request, "/places/search")
    query_params = {"query": query}
    if lat is not None:
        query_params["lat"] = lat
    if lon is not None:
        query_params["lon"] = lon
    if radius != 50000:  # Only include if not default
        query_params["radius"] = radius
    if limit != 10:  # Only include if not default
        query_params["limit"] = limit

    return create_paginated_response(
        items=places,
        total_items=len(places),  # Search results are single page
        current_page=1,
        per_page=len(places) if places else limit,
        base_url=base_url,
        query_params=query_params
    )


@router.get("/geocode", response_model=List[GeocodingResult])
async def geocode_address(
    address: str = Query(..., min_length=2),
    current_user: User = Depends(get_current_user),
):
    """Geocode a free-form address using MapTiler."""
    if not settings.MAPTILER_API_KEY:
        return []

    safe_query = quote(address)
    url = f"https://api.maptiler.com/geocoding/{safe_query}.json"
    params = {"key": settings.MAPTILER_API_KEY, "limit": 5, "autocomplete": True}

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url, params=params, timeout=10.0)
            resp.raise_for_status()
            data = resp.json()
            results: List[GeocodingResult] = []
            for f in data.get("features", []):
                coords = (f.get("geometry", {}).get("coordinates") or [None, None])
                lon_val = float(coords[0]) if coords and len(coords) >= 2 else None
                lat_val = float(coords[1]) if coords and len(coords) >= 2 else None
                if lat_val is None or lon_val is None:
                    continue
                results.append(GeocodingResult(
                    address=f.get("place_name") or f.get("text") or address,
                    formatted_address=f.get("place_name") or "",
                    lat=lat_val,
                    lon=lon_val,
                    place_id=f.get("id") or None,
                    types=f.get("place_type") or None,
                ))
            return results
        except httpx.HTTPError as e:
            logging.warning(f"MapTiler geocode failed: {e}")
            return []


@router.get("/reverse-geocode", response_model=List[GeocodingResult])
async def reverse_geocode(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    current_user: User = Depends(get_current_user),
):
    """Reverse geocode coordinates using MapTiler."""
    if not settings.MAPTILER_API_KEY:
        return []

    # Reverse geocoding with coordinates in path
    url = f"https://api.maptiler.com/geocoding/{lon},{lat}.json"
    params = {"key": settings.MAPTILER_API_KEY, "reverse": True, "limit": 5}

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url, params=params, timeout=10.0)
            resp.raise_for_status()
            data = resp.json()
            results: List[GeocodingResult] = []
            for f in data.get("features", []):
                coords = (f.get("geometry", {}).get("coordinates") or [lon, lat])
                lon_val = float(coords[0])
                lat_val = float(coords[1])
                results.append(GeocodingResult(
                    address=f.get("place_name") or f.get("text") or "",
                    formatted_address=f.get("place_name") or "",
                    lat=lat_val,
                    lon=lon_val,
                    place_id=f.get("id") or None,
                    types=f.get("place_type") or None,
                ))
            return results
        except httpx.HTTPError as e:
            logging.warning(f"MapTiler reverse geocode failed: {e}")
            return []


@router.post("/", response_model=PlaceSchema, status_code=201)
async def create_place(
    place_data: PlaceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new place owned by the current user."""
    # Try to capture provider_place_id from meta if present (e.g., from MapTiler feature id)
    provider_id = None
    try:
        raw = (place_data.meta or {}).get("raw")
        if isinstance(raw, dict):
            provider_id = raw.get("id") or raw.get("place_id") or raw.get("properties", {}).get("id")
    except Exception:
        provider_id = None

    # Normalize address/meta for display (keep exact address as provided)
    normalized = _normalize_address(place_data.address, place_data.meta or {})
    merged_meta = dict(place_data.meta or {})
    merged_meta["normalized"] = normalized

    place = Place(
        owner_type=OwnerType.USER,
        owner_id=current_user.id,
        provider_place_id=str(provider_id) if provider_id else None,
        name=place_data.name,
        address=place_data.address,
        lat=place_data.lat,
        lon=place_data.lon,
        meta=merged_meta,
    )
    db.add(place)
    db.commit()
    db.refresh(place)
    return PlaceSchema.model_validate(place)


@router.get("/{place_id}", response_model=PlaceSchema)
async def get_place(place_id: str, request: Request, response: Response, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    place = db.query(Place).filter(Place.id == place_id).first()
    if not place:
        raise HTTPException(status_code=404, detail="Place not found")
    # ETag based on id + updated_at
    raw_tag = hashlib.sha256(f"{place.id}:{place.updated_at.isoformat()}".encode()).hexdigest()
    etag = _quote_etag(raw_tag)
    inm = request.headers.get("if-none-match")
    if inm and inm.strip(' W/').strip() == etag.strip(' W/').strip():
        # Not modified
        response.headers["ETag"] = etag
        response.headers["Cache-Control"] = "public, max-age=86400, stale-while-revalidate=60"
        return Response(status_code=304)
    # Cache headers
    response.headers["ETag"] = etag
    response.headers["Cache-Control"] = "public, max-age=86400, stale-while-revalidate=60"
    return PlaceSchema.model_validate(place)


@router.patch("/{place_id}", response_model=PlaceSchema)
async def update_place(
    place_id: str,
    place_data: PlaceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    place = db.query(Place).filter(Place.id == place_id).first()
    if not place:
        raise HTTPException(status_code=404, detail="Place not found")
    # Authorization: ensure the current user owns the place
    if not (place.owner_type == OwnerType.USER and place.owner_id == current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized to update this place")

    update_data = place_data.model_dump(exclude_unset=True)

    # If address or meta updated, recompute normalization
    addr = update_data.get("address", place.address)
    meta_in = update_data.get("meta", place.meta or {})
    normalized = _normalize_address(addr, meta_in or {})
    merged_meta = dict(place.meta or {})
    # Merge new meta fields if provided
    if "meta" in update_data:
        merged_meta.update(update_data["meta"] or {})
    merged_meta["normalized"] = normalized

    # Apply updates
    for k, v in update_data.items():
        if k == "meta":
            continue
        setattr(place, k, v)
    place.meta = merged_meta

    db.commit()
    db.refresh(place)
    return PlaceSchema.model_validate(place)


@router.delete("/{place_id}")
async def delete_place(place_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    place = db.query(Place).filter(Place.id == place_id).first()
    if not place:
        raise HTTPException(status_code=404, detail="Place not found")
    # Authorization: ensure the current user owns the place
    if not (place.owner_type == OwnerType.USER and place.owner_id == current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized to delete this place")
    db.delete(place)
    db.commit()
    return {"status": "deleted"}

@router.get("/bulk", response_model=List[PlaceSchema])
async def get_places_bulk(
    ids: str = Query(..., description="Comma-separated place IDs"),
    request: Request = None,
    response: Response = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Batch fetch places by IDs. Use comma-separated ids param."""
    id_list = [i.strip() for i in ids.split(',') if i.strip()]
    if not id_list:
        return []

    unique_ids = list(dict.fromkeys(id_list))
    places = db.query(Place).filter(Place.id.in_(unique_ids)).all()

    # ETag: independent of requested order; hash sorted id:updated_at
    sorted_parts = sorted([f"{p.id}:{p.updated_at.isoformat()}" for p in places])
    raw_tag = hashlib.sha256("|".join(sorted_parts).encode()).hexdigest()
    etag = _quote_etag(raw_tag)

    if request is not None:
        inm = request.headers.get("if-none-match")
        if inm and inm.strip(' W/').strip() == etag.strip(' W/').strip():
            if response is not None:
                response.headers["ETag"] = etag
                response.headers["Cache-Control"] = "public, max-age=86400, stale-while-revalidate=60"
            # For response_model=List[PlaceSchema], return an empty list on 304 case
            return []

    if response is not None:
        response.headers["ETag"] = etag
        response.headers["Cache-Control"] = "public, max-age=86400, stale-while-revalidate=60"

    # Preserve requested order in body
    place_map = {p.id: p for p in places}
    ordered = [place_map[i] for i in unique_ids if i in place_map]

    return [PlaceSchema.model_validate(p) for p in ordered]

