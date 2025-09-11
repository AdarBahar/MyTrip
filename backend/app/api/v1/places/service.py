"""
Places Service

Core business logic for address and POI search with type-ahead suggestions.
"""

import asyncio
import time
import uuid
import re
import math
import unicodedata
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
import logging

from .models import (
    PlaceSuggestion, PlaceSearchResult, PlaceDetails, Coordinates, BoundingBox,
    PlaceType, GeometryType, PlaceMetadata, SuggestRequest, SearchRequest
)

logger = logging.getLogger(__name__)


class PlacesService:
    """Service for address and POI search operations"""
    
    def __init__(self):
        self.start_time = time.time()
        self._cache = {}  # Simple in-memory cache
        self._session_cache = {}  # Session-based cache
        
        # Mock data for demonstration
        self._mock_places = self._initialize_mock_data()
    
    def _initialize_mock_data(self) -> List[Dict[str, Any]]:
        """Initialize mock place data for demonstration"""
        return [
            {
                "id": "poi_tel_aviv_museum",
                "name": "Tel Aviv Museum of Art",
                "formatted_address": "27 Shaul Hamelech Blvd, Tel Aviv-Yafo, Israel",
                "types": [PlaceType.MUSEUM, PlaceType.POI],
                "center": {"lat": 32.0773, "lng": 34.7863},
                "categories": ["museum", "art", "culture"],
                "country": "IL",
                "timezone": "Asia/Jerusalem",
                "rating": 4.5,
                "popularity": 0.85,
                "phone": "+972-3-607-7020",
                "website": "https://www.tamuseum.org.il"
            },
            {
                "id": "poi_hotel_montefiore",
                "name": "Hotel Montefiore",
                "formatted_address": "36 Montefiore St, Tel Aviv-Yafo, Israel",
                "types": [PlaceType.LODGING, PlaceType.POI],
                "center": {"lat": 32.0643, "lng": 34.7748},
                "categories": ["hotel", "lodging", "boutique"],
                "country": "IL",
                "timezone": "Asia/Jerusalem",
                "rating": 4.3,
                "popularity": 0.78,
                "phone": "+972-3-564-6100",
                "website": "https://hotelmontefiore.co.il"
            },
            {
                "id": "poi_carmel_market",
                "name": "Carmel Market",
                "formatted_address": "HaCarmel St, Tel Aviv-Yafo, Israel",
                "types": [PlaceType.ATTRACTION, PlaceType.POI],
                "center": {"lat": 32.0692, "lng": 34.7751},
                "categories": ["market", "food", "shopping"],
                "country": "IL",
                "timezone": "Asia/Jerusalem",
                "rating": 4.2,
                "popularity": 0.92,
                "hours": {"monday": "08:00-19:00", "sunday": "08:00-19:00"}
            },
            {
                "id": "addr_rothschild_1",
                "name": "1 Rothschild Boulevard",
                "formatted_address": "1 Rothschild Blvd, Tel Aviv-Yafo, Israel",
                "types": [PlaceType.ADDRESS],
                "center": {"lat": 32.0644, "lng": 34.7719},
                "categories": ["address"],
                "country": "IL",
                "timezone": "Asia/Jerusalem"
            },
            {
                "id": "poi_restaurant_orna_ella",
                "name": "Orna and Ella",
                "formatted_address": "33 Sheinkin St, Tel Aviv-Yafo, Israel",
                "types": [PlaceType.RESTAURANT, PlaceType.POI],
                "center": {"lat": 32.0656, "lng": 34.7739},
                "categories": ["restaurant", "israeli", "breakfast"],
                "country": "IL",
                "timezone": "Asia/Jerusalem",
                "rating": 4.4,
                "popularity": 0.73,
                "phone": "+972-3-525-9519"
            },
            {
                "id": "addr_london_downing",
                "name": "10 Downing Street",
                "formatted_address": "10 Downing St, London SW1A 2AA, UK",
                "types": [PlaceType.ADDRESS],
                "center": {"lat": 51.5034, "lng": -0.1276},
                "categories": ["address", "government"],
                "country": "GB",
                "timezone": "Europe/London",
                "postcode": "SW1A 2AA"
            },
            {
                "id": "poi_british_museum",
                "name": "British Museum",
                "formatted_address": "Great Russell St, London WC1B 3DG, UK",
                "types": [PlaceType.MUSEUM, PlaceType.POI],
                "center": {"lat": 51.5194, "lng": -0.1270},
                "categories": ["museum", "history", "culture"],
                "country": "GB",
                "timezone": "Europe/London",
                "rating": 4.6,
                "popularity": 0.95,
                "phone": "+44 20 7323 8299",
                "website": "https://www.britishmuseum.org"
            },
            # Hebrew places for testing
            {
                "id": "poi_tel_aviv_museum_he",
                "name": "מוזיאון תל אביב לאמנות",
                "name_ascii": "Tel Aviv Museum of Art",
                "name_local": "מוזיאון תל אביב לאמנות",
                "formatted_address": "שדרות שאול המלך 27, תל אביב-יפו, ישראל",
                "formatted_address_ascii": "27 Shaul Hamelech Blvd, Tel Aviv-Yafo, Israel",
                "types": [PlaceType.MUSEUM, PlaceType.POI],
                "center": {"lat": 32.0773, "lng": 34.7863},
                "categories": ["museum", "art", "culture", "מוזיאון", "אמנות", "תרבות"],
                "country": "IL",
                "timezone": "Asia/Jerusalem",
                "rating": 4.5,
                "popularity": 0.85,
                "phone": "+972-3-607-7020",
                "website": "https://www.tamuseum.org.il",
                "aliases": ["מוזיאון תל אביב", "מוזיאון האמנות תל אביב", "Tel Aviv Art Museum"]
            },
            {
                "id": "poi_carmel_market_he",
                "name": "שוק הכרמל",
                "name_ascii": "Carmel Market",
                "name_local": "שוק הכרמל",
                "formatted_address": "רחוב הכרמל, תל אביב-יפו, ישראל",
                "formatted_address_ascii": "HaCarmel St, Tel Aviv-Yafo, Israel",
                "types": [PlaceType.ATTRACTION, PlaceType.POI],
                "center": {"lat": 32.0692, "lng": 34.7751},
                "categories": ["market", "food", "shopping", "שוק", "אוכל", "קניות"],
                "country": "IL",
                "timezone": "Asia/Jerusalem",
                "rating": 4.2,
                "popularity": 0.92,
                "hours": {"monday": "08:00-19:00", "sunday": "08:00-19:00"},
                "aliases": ["שוק כרמל", "הכרמל", "Carmel Shuk", "Shuk HaCarmel"]
            },
            {
                "id": "poi_dizengoff_center_he",
                "name": "דיזנגוף סנטר",
                "name_ascii": "Dizengoff Center",
                "name_local": "דיזנגוף סנטר",
                "formatted_address": "רחוב דיזנגוף 50, תל אביב-יפו, ישראל",
                "formatted_address_ascii": "50 Dizengoff St, Tel Aviv-Yafo, Israel",
                "types": [PlaceType.ATTRACTION, PlaceType.POI],
                "center": {"lat": 32.0740, "lng": 34.7749},
                "categories": ["shopping", "mall", "center", "קניות", "קניון", "מרכז"],
                "country": "IL",
                "timezone": "Asia/Jerusalem",
                "rating": 4.0,
                "popularity": 0.75,
                "phone": "+972-3-621-2400",
                "website": "https://www.dizengoff-center.co.il",
                "aliases": ["דיזנגוף", "קניון דיזנגוף", "Dizengoff Mall"]
            },
            {
                "id": "addr_rothschild_he",
                "name": "שדרות רוטשילד 1",
                "name_ascii": "1 Rothschild Boulevard",
                "name_local": "שדרות רוטשילד 1",
                "formatted_address": "שדרות רוטשילד 1, תל אביב-יפו, ישראל",
                "formatted_address_ascii": "1 Rothschild Blvd, Tel Aviv-Yafo, Israel",
                "types": [PlaceType.ADDRESS],
                "center": {"lat": 32.0644, "lng": 34.7719},
                "categories": ["address", "כתובת"],
                "country": "IL",
                "timezone": "Asia/Jerusalem",
                "aliases": ["רוטשילד 1", "שדרות רוטשילד", "Rothschild 1"]
            },
            {
                "id": "poi_restaurant_miznon_he",
                "name": "מזנון",
                "name_ascii": "Miznon",
                "name_local": "מזנון",
                "formatted_address": "רחוב קינג ג'ורג' 23, תל אביב-יפו, ישראל",
                "formatted_address_ascii": "23 King George St, Tel Aviv-Yafo, Israel",
                "types": [PlaceType.RESTAURANT, PlaceType.POI],
                "center": {"lat": 32.0719, "lng": 34.7758},
                "categories": ["restaurant", "israeli", "pita", "מסעדה", "ישראלי", "פיתה"],
                "country": "IL",
                "timezone": "Asia/Jerusalem",
                "rating": 4.3,
                "popularity": 0.88,
                "phone": "+972-3-560-1007",
                "aliases": ["מזנון תל אביב", "Miznon Tel Aviv"]
            },
            # Additional Hebrew streets and places
            {
                "id": "addr_yarkon_street",
                "name": "רחוב ירקון",
                "name_ascii": "Yarkon Street",
                "name_local": "רחוב ירקון",
                "formatted_address": "רחוב ירקון, תל אביב-יפו, ישראל",
                "formatted_address_ascii": "Yarkon St, Tel Aviv-Yafo, Israel",
                "types": [PlaceType.ADDRESS],
                "center": {"lat": 32.0851, "lng": 34.7692},
                "categories": ["address", "street", "כתובת", "רחוב"],
                "country": "IL",
                "timezone": "Asia/Jerusalem",
                "aliases": ["ירקון", "רח' ירקון", "Yarkon St", "Yarkon Street"]
            },
            {
                "id": "addr_yigal_alon_street",
                "name": "רחוב יגאל אלון",
                "name_ascii": "Yigal Alon Street",
                "name_local": "רחוב יגאל אלון",
                "formatted_address": "רחוב יגאל אלון, תל אביב-יפו, ישראל",
                "formatted_address_ascii": "Yigal Alon St, Tel Aviv-Yafo, Israel",
                "types": [PlaceType.ADDRESS],
                "center": {"lat": 32.0567, "lng": 34.7925},
                "categories": ["address", "street", "כתובת", "רחוב"],
                "country": "IL",
                "timezone": "Asia/Jerusalem",
                "aliases": ["יגאל אלון", "רח' יגאל אלון", "Yigal Alon St", "Yigal Alon Street"]
            },
            {
                "id": "addr_ben_yehuda_street",
                "name": "רחוב בן יהודה",
                "name_ascii": "Ben Yehuda Street",
                "name_local": "רחוב בן יהודה",
                "formatted_address": "רחוב בן יהודה, תל אביב-יפו, ישראל",
                "formatted_address_ascii": "Ben Yehuda St, Tel Aviv-Yafo, Israel",
                "types": [PlaceType.ADDRESS],
                "center": {"lat": 32.0808, "lng": 34.7709},
                "categories": ["address", "street", "כתובת", "רחוב"],
                "country": "IL",
                "timezone": "Asia/Jerusalem",
                "aliases": ["בן יהודה", "רח' בן יהודה", "Ben Yehuda St", "Ben Yehuda Street"]
            },
            {
                "id": "addr_allenby_street",
                "name": "רחוב אלנבי",
                "name_ascii": "Allenby Street",
                "name_local": "רחוב אלנבי",
                "formatted_address": "רחוב אלנבי, תל אביב-יפו, ישראל",
                "formatted_address_ascii": "Allenby St, Tel Aviv-Yafo, Israel",
                "types": [PlaceType.ADDRESS],
                "center": {"lat": 32.0668, "lng": 34.7701},
                "categories": ["address", "street", "כתובת", "רחוב"],
                "country": "IL",
                "timezone": "Asia/Jerusalem",
                "aliases": ["אלנבי", "רח' אלנבי", "Allenby St", "Allenby Street"]
            },
            {
                "id": "addr_sheinkin_street",
                "name": "רחוב שינקין",
                "name_ascii": "Sheinkin Street",
                "name_local": "רחוב שינקין",
                "formatted_address": "רחוב שינקין, תל אביב-יפו, ישראל",
                "formatted_address_ascii": "Sheinkin St, Tel Aviv-Yafo, Israel",
                "types": [PlaceType.ADDRESS],
                "center": {"lat": 32.0656, "lng": 34.7739},
                "categories": ["address", "street", "כתובת", "רחוב"],
                "country": "IL",
                "timezone": "Asia/Jerusalem",
                "aliases": ["שינקין", "רח' שינקין", "Sheinkin St", "Sheinkin Street"]
            },
            {
                "id": "addr_king_george_street",
                "name": "רחוב קינג ג'ורג'",
                "name_ascii": "King George Street",
                "name_local": "רחוב קינג ג'ורג'",
                "formatted_address": "רחוב קינג ג'ורג', תל אביב-יפו, ישראל",
                "formatted_address_ascii": "King George St, Tel Aviv-Yafo, Israel",
                "types": [PlaceType.ADDRESS],
                "center": {"lat": 32.0719, "lng": 34.7758},
                "categories": ["address", "street", "כתובת", "רחוב"],
                "country": "IL",
                "timezone": "Asia/Jerusalem",
                "aliases": ["קינג ג'ורג'", "רח' קינג ג'ורג'", "King George St", "King George Street"]
            },
            {
                "id": "addr_hayarkon_park",
                "name": "פארק הירקון",
                "name_ascii": "Hayarkon Park",
                "name_local": "פארק הירקון",
                "formatted_address": "פארק הירקון, תל אביב-יפו, ישראל",
                "formatted_address_ascii": "Hayarkon Park, Tel Aviv-Yafo, Israel",
                "types": [PlaceType.ATTRACTION, PlaceType.POI],
                "center": {"lat": 32.1067, "lng": 34.7925},
                "categories": ["park", "nature", "recreation", "פארק", "טבע", "נופש"],
                "country": "IL",
                "timezone": "Asia/Jerusalem",
                "rating": 4.4,
                "popularity": 0.88,
                "aliases": ["הירקון", "פארק ירקון", "Yarkon Park", "Hayarkon Park"]
            },
            {
                "id": "poi_azrieli_towers",
                "name": "מגדלי עזריאלי",
                "name_ascii": "Azrieli Towers",
                "name_local": "מגדלי עזריאלי",
                "formatted_address": "מגדלי עזריאלי, תל אביב-יפו, ישראל",
                "formatted_address_ascii": "Azrieli Towers, Tel Aviv-Yafo, Israel",
                "types": [PlaceType.ATTRACTION, PlaceType.POI],
                "center": {"lat": 32.0742, "lng": 34.7915},
                "categories": ["building", "tower", "shopping", "בניין", "מגדל", "קניות"],
                "country": "IL",
                "timezone": "Asia/Jerusalem",
                "rating": 4.3,
                "popularity": 0.85,
                "phone": "+972-3-608-1179",
                "website": "https://www.azrieli.com",
                "aliases": ["עזריאלי", "מגדלי עזריאלי", "Azrieli Center", "Azrieli Mall"]
            },
            {
                "id": "poi_old_jaffa",
                "name": "יפו העתיקה",
                "name_ascii": "Old Jaffa",
                "name_local": "יפו העתיקה",
                "formatted_address": "יפו העתיקה, תל אביב-יפו, ישראל",
                "formatted_address_ascii": "Old Jaffa, Tel Aviv-Yafo, Israel",
                "types": [PlaceType.ATTRACTION, PlaceType.POI],
                "center": {"lat": 32.0546, "lng": 34.7506},
                "categories": ["historic", "culture", "tourism", "היסטורי", "תרבות", "תיירות"],
                "country": "IL",
                "timezone": "Asia/Jerusalem",
                "rating": 4.6,
                "popularity": 0.92,
                "aliases": ["יפו", "העיר העתיקה", "Old City", "Jaffa Old City"]
            },
            # Specific numbered addresses
            {
                "id": "addr_yarkon_1",
                "name": "ירקון 1",
                "name_ascii": "1 Yarkon Street",
                "name_local": "ירקון 1",
                "formatted_address": "ירקון 1, תל אביב-יפו, ישראל",
                "formatted_address_ascii": "1 Yarkon St, Tel Aviv-Yafo, Israel",
                "types": [PlaceType.ADDRESS],
                "center": {"lat": 32.0851, "lng": 34.7692},
                "categories": ["address", "כתובת"],
                "country": "IL",
                "timezone": "Asia/Jerusalem",
                "aliases": ["1 ירקון", "ירקון 1 תל אביב", "1 Yarkon Street Tel Aviv", "1 Yarkon St"]
            },
            {
                "id": "addr_ben_yehuda_123",
                "name": "בן יהודה 123",
                "name_ascii": "123 Ben Yehuda Street",
                "name_local": "בן יהודה 123",
                "formatted_address": "בן יהודה 123, תל אביב-יפו, ישראל",
                "formatted_address_ascii": "123 Ben Yehuda St, Tel Aviv-Yafo, Israel",
                "types": [PlaceType.ADDRESS],
                "center": {"lat": 32.0808, "lng": 34.7709},
                "categories": ["address", "כתובת"],
                "country": "IL",
                "timezone": "Asia/Jerusalem",
                "aliases": ["123 בן יהודה", "בן יהודה 123 תל אביב", "123 Ben Yehuda Street Tel Aviv", "123 Ben Yehuda St"]
            },
            {
                "id": "addr_allenby_45",
                "name": "אלנבי 45",
                "name_ascii": "45 Allenby Street",
                "name_local": "אלנבי 45",
                "formatted_address": "אלנבי 45, תל אביב-יפו, ישראל",
                "formatted_address_ascii": "45 Allenby St, Tel Aviv-Yafo, Israel",
                "types": [PlaceType.ADDRESS],
                "center": {"lat": 32.0668, "lng": 34.7701},
                "categories": ["address", "כתובת"],
                "country": "IL",
                "timezone": "Asia/Jerusalem",
                "aliases": ["45 אלנבי", "אלנבי 45 תל אביב", "45 Allenby Street Tel Aviv", "45 Allenby St"]
            },
            {
                "id": "addr_sheinkin_67",
                "name": "שינקין 67",
                "name_ascii": "67 Sheinkin Street",
                "name_local": "שינקין 67",
                "formatted_address": "שינקין 67, תל אביב-יפו, ישראל",
                "formatted_address_ascii": "67 Sheinkin St, Tel Aviv-Yafo, Israel",
                "types": [PlaceType.ADDRESS],
                "center": {"lat": 32.0656, "lng": 34.7739},
                "categories": ["address", "כתובת"],
                "country": "IL",
                "timezone": "Asia/Jerusalem",
                "aliases": ["67 שינקין", "שינקין 67 תל אביב", "67 Sheinkin Street Tel Aviv", "67 Sheinkin St"]
            },
            # International addresses
            {
                "id": "addr_oxford_street_100",
                "name": "100 Oxford Street",
                "formatted_address": "100 Oxford St, London W1D 1LL, UK",
                "types": [PlaceType.ADDRESS],
                "center": {"lat": 51.5155, "lng": -0.1426},
                "categories": ["address"],
                "country": "GB",
                "timezone": "Europe/London",
                "postcode": "W1D 1LL",
                "aliases": ["100 Oxford St", "Oxford Street 100", "100 Oxford Street London"]
            },
            {
                "id": "addr_broadway_1234",
                "name": "1234 Broadway",
                "formatted_address": "1234 Broadway, New York, NY 10001, USA",
                "types": [PlaceType.ADDRESS],
                "center": {"lat": 40.7505, "lng": -73.9934},
                "categories": ["address"],
                "country": "US",
                "timezone": "America/New_York",
                "postcode": "10001",
                "aliases": ["1234 Broadway NYC", "Broadway 1234", "1234 Broadway New York"]
            }
        ]
    
    async def get_suggestions(self, request: SuggestRequest) -> List[PlaceSuggestion]:
        """Get type-ahead suggestions for a query"""
        start_time = time.time()
        
        try:
            # Normalize query
            query = request.q.lower().strip()
            
            # Filter and score places
            suggestions = []
            user_location = None
            if request.lat is not None and request.lng is not None:
                user_location = (request.lat, request.lng)
            
            for place_data in self._mock_places:
                score = self._calculate_relevance_score(query, place_data, user_location, request)
                
                if score > 0.1:  # Minimum relevance threshold
                    suggestion = self._create_suggestion(place_data, query, score, user_location)
                    suggestions.append(suggestion)
            
            # Sort by score and limit results
            suggestions.sort(key=lambda x: x.confidence, reverse=True)
            suggestions = suggestions[:request.limit]
            
            # Cache results
            cache_key = f"suggest:{request.session_token}:{query}"
            self._session_cache[cache_key] = {
                "suggestions": suggestions,
                "timestamp": time.time()
            }
            
            logger.info(f"Suggestions query completed in {(time.time() - start_time)*1000:.1f}ms")
            return suggestions
            
        except Exception as e:
            logger.error(f"Error in get_suggestions: {e}")
            raise
    
    async def search_places(self, request: SearchRequest) -> Tuple[List[PlaceSearchResult], Optional[str]]:
        """Search for places with full details"""
        start_time = time.time()
        
        try:
            query = request.q.lower().strip()
            user_location = None
            if request.lat is not None and request.lng is not None:
                user_location = (request.lat, request.lng)
            
            # Filter and score places
            results = []
            for place_data in self._mock_places:
                score = self._calculate_relevance_score(query, place_data, user_location, request)
                
                if score > 0.05:  # Lower threshold for search
                    result = self._create_search_result(place_data, score, user_location)
                    results.append(result)
            
            # Sort results
            if request.sort == "distance" and user_location:
                results.sort(key=lambda x: x.center.lat**2 + x.center.lng**2)  # Simplified distance
            elif request.sort == "rating":
                results.sort(key=lambda x: getattr(x, 'rating', 0), reverse=True)
            else:  # relevance
                results.sort(key=lambda x: x.score, reverse=True)
            
            # Apply pagination
            offset = request.offset or 0
            limit = request.limit
            total_results = len(results)
            results = results[offset:offset + limit]
            
            # Generate page token if more results available
            page_token = None
            if offset + limit < total_results:
                page_token = f"page_{offset + limit}_{int(time.time())}"
            
            logger.info(f"Search query completed in {(time.time() - start_time)*1000:.1f}ms")
            return results, page_token
            
        except Exception as e:
            logger.error(f"Error in search_places: {e}")
            raise
    
    async def get_place_details(self, place_id: str) -> Optional[PlaceDetails]:
        """Get detailed information for a specific place"""
        try:
            # Find place in mock data
            place_data = None
            for p in self._mock_places:
                if p["id"] == place_id:
                    place_data = p
                    break
            
            if not place_data:
                return None
            
            # Create detailed response
            details = PlaceDetails(
                id=place_data["id"],
                name=place_data["name"],
                formatted_address=place_data["formatted_address"],
                types=place_data["types"],
                center=Coordinates(**place_data["center"]),
                bbox=self._calculate_bbox(place_data["center"]),
                categories=place_data.get("categories", []),
                score=1.0,  # Perfect match for direct lookup
                timezone=place_data.get("timezone"),
                metadata=PlaceMetadata(
                    country=place_data.get("country"),
                    postcode=place_data.get("postcode")
                ),
                geometry_type=GeometryType.ROOFTOP,
                phone=place_data.get("phone"),
                website=place_data.get("website"),
                hours=place_data.get("hours"),
                rating=place_data.get("rating"),
                popularity=place_data.get("popularity"),
                aliases=[],
                source_refs={"internal": place_data["id"]},
                name_local=place_data.get("name_local"),
                name_ascii=place_data.get("name_ascii")
            )
            
            return details
            
        except Exception as e:
            logger.error(f"Error in get_place_details: {e}")
            raise
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for better matching (handles Hebrew and English)"""
        if not text:
            return ""

        # Convert to lowercase and strip
        text = text.lower().strip()

        # Remove diacritics and normalize unicode
        text = unicodedata.normalize('NFD', text)
        text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')

        return text

    def _calculate_text_similarity(self, query: str, text: str) -> float:
        """Calculate text similarity score between query and text"""
        if not query or not text:
            return 0.0

        query_norm = self._normalize_text(query)
        text_norm = self._normalize_text(text)

        # Exact match
        if query_norm == text_norm:
            return 1.0

        # Prefix match
        if text_norm.startswith(query_norm):
            return 0.9

        # Contains match
        if query_norm in text_norm:
            return 0.7

        # Word prefix match
        words = text_norm.split()
        for word in words:
            if word.startswith(query_norm):
                return 0.6

        # Partial word match
        for word in words:
            if query_norm in word:
                return 0.4

        return 0.0

    def _calculate_address_component_score(self, query: str, place_data: Dict[str, Any]) -> float:
        """Calculate score based on address components (street, number, city)"""
        if not query or len(query) < 3:
            return 0.0

        query_norm = self._normalize_text(query)
        score = 0.0

        # Check if query contains numbers (likely street number)
        has_numbers = bool(re.search(r'\d+', query))

        # Split query into components
        query_parts = query_norm.split()

        # Get address components
        name = place_data.get("name", "")
        formatted_address = place_data.get("formatted_address", "")
        formatted_address_ascii = place_data.get("formatted_address_ascii", "")

        # Combine all address text for matching
        address_texts = [name, formatted_address, formatted_address_ascii]
        address_texts = [text for text in address_texts if text]

        # Check each query part against address components
        for query_part in query_parts:
            if len(query_part) < 2:
                continue

            part_score = 0.0
            for address_text in address_texts:
                if not address_text:
                    continue

                address_norm = self._normalize_text(address_text)

                # Exact word match
                if query_part in address_norm.split():
                    part_score = max(part_score, 1.0)
                # Partial word match
                elif query_part in address_norm:
                    part_score = max(part_score, 0.7)
                # Word starts with query part
                elif any(word.startswith(query_part) for word in address_norm.split()):
                    part_score = max(part_score, 0.8)

            score += part_score

        # Bonus for number matching if query has numbers
        if has_numbers:
            query_numbers = re.findall(r'\d+', query)
            for address_text in address_texts:
                address_numbers = re.findall(r'\d+', address_text)
                for query_num in query_numbers:
                    if query_num in address_numbers:
                        score += 0.5  # Bonus for matching street numbers

        # Normalize score by number of query parts
        if query_parts:
            score = score / len(query_parts)

        return min(score, 1.0)

    def _calculate_relevance_score(
        self,
        query: str,
        place_data: Dict[str, Any],
        user_location: Optional[Tuple[float, float]],
        request: Any
    ) -> float:
        """Calculate relevance score for a place given a query"""
        score = 0.0
        query_norm = self._normalize_text(query)

        # Text matching - check multiple name fields
        name_score = 0.0

        # Primary name (could be Hebrew or English)
        name_score = max(name_score, self._calculate_text_similarity(query, place_data["name"]))

        # ASCII name (English transliteration)
        if place_data.get("name_ascii"):
            name_score = max(name_score, self._calculate_text_similarity(query, place_data["name_ascii"]))

        # Local name (native language)
        if place_data.get("name_local"):
            name_score = max(name_score, self._calculate_text_similarity(query, place_data["name_local"]))

        # Aliases (alternative names)
        for alias in place_data.get("aliases", []):
            name_score = max(name_score, self._calculate_text_similarity(query, alias))

        score += name_score * 0.8

        # Address matching - check both Hebrew and English addresses
        address_score = 0.0
        address_score = max(address_score, self._calculate_text_similarity(query, place_data["formatted_address"]))

        if place_data.get("formatted_address_ascii"):
            address_score = max(address_score, self._calculate_text_similarity(query, place_data["formatted_address_ascii"]))

        score += address_score * 0.3

        # Enhanced address component matching
        address_component_score = self._calculate_address_component_score(query, place_data)
        score += address_component_score * 0.4

        # Category matching - support Hebrew and English categories
        if hasattr(request, 'categories') and request.categories:
            requested_categories = [self._normalize_text(c.strip()) for c in request.categories.split(',')]
            place_categories = [self._normalize_text(c) for c in place_data.get("categories", [])]

            category_match = False
            for req_cat in requested_categories:
                for place_cat in place_categories:
                    if req_cat in place_cat or place_cat in req_cat:
                        category_match = True
                        break
                if category_match:
                    break

            if category_match:
                score += 0.2

        # Query category matching - check if query matches any category
        query_categories = place_data.get("categories", [])
        for category in query_categories:
            cat_score = self._calculate_text_similarity(query, category)
            if cat_score > 0.5:
                score += 0.15 * cat_score
        
        # Country filtering
        if hasattr(request, 'countries') and request.countries:
            requested_countries = [c.strip().upper() for c in request.countries.split(',')]
            place_country = place_data.get("country", "").upper()
            if place_country not in requested_countries:
                score *= 0.1  # Heavily penalize wrong country
        
        # Proximity boost
        if user_location and score > 0:
            distance = self._calculate_distance(
                user_location[0], user_location[1],
                place_data["center"]["lat"], place_data["center"]["lng"]
            )
            
            # Boost nearby places
            if distance < 1000:  # Within 1km
                score *= 1.2
            elif distance < 5000:  # Within 5km
                score *= 1.1
            elif distance > 50000:  # More than 50km
                score *= 0.8
        
        # Popularity boost
        popularity = place_data.get("popularity", 0.5)
        score *= (0.8 + 0.4 * popularity)  # Scale between 0.8 and 1.2
        
        return min(score, 1.0)
    
    def _create_suggestion(
        self, 
        place_data: Dict[str, Any], 
        query: str, 
        score: float,
        user_location: Optional[Tuple[float, float]]
    ) -> PlaceSuggestion:
        """Create a suggestion from place data"""
        # Highlight matching text
        highlighted = self._highlight_text(place_data["name"], query)
        
        # Calculate distance
        distance_m = None
        if user_location:
            distance_m = int(self._calculate_distance(
                user_location[0], user_location[1],
                place_data["center"]["lat"], place_data["center"]["lng"]
            ))
        
        return PlaceSuggestion(
            id=place_data["id"],
            name=place_data["name"],
            highlighted=highlighted,
            formatted_address=place_data["formatted_address"],
            types=place_data["types"],
            center=Coordinates(**place_data["center"]),
            distance_m=distance_m,
            confidence=score,
            source="internal"
        )
    
    def _create_search_result(
        self, 
        place_data: Dict[str, Any], 
        score: float,
        user_location: Optional[Tuple[float, float]]
    ) -> PlaceSearchResult:
        """Create a search result from place data"""
        return PlaceSearchResult(
            id=place_data["id"],
            name=place_data["name"],
            formatted_address=place_data["formatted_address"],
            types=place_data["types"],
            center=Coordinates(**place_data["center"]),
            bbox=self._calculate_bbox(place_data["center"]),
            categories=place_data.get("categories", []),
            score=score,
            timezone=place_data.get("timezone"),
            metadata=PlaceMetadata(
                country=place_data.get("country"),
                postcode=place_data.get("postcode")
            ),
            geometry_type=GeometryType.ROOFTOP
        )
    
    def _highlight_text(self, text: str, query: str) -> str:
        """Highlight matching text with HTML bold tags (supports Hebrew and English)"""
        if not query or not text:
            return text

        # Normalize for matching but preserve original case
        query_norm = self._normalize_text(query)
        text_norm = self._normalize_text(text)

        # Find the best match position
        match_start = -1
        match_length = 0

        # Try exact match first
        if query_norm in text_norm:
            match_start = text_norm.find(query_norm)
            match_length = len(query)
        else:
            # Try word prefix match
            words = text.split()
            for i, word in enumerate(words):
                word_norm = self._normalize_text(word)
                if word_norm.startswith(query_norm):
                    # Find position in original text
                    word_start = 0
                    for j in range(i):
                        word_start += len(words[j]) + 1  # +1 for space
                    match_start = word_start
                    match_length = len(query)
                    break

        # Apply highlighting if match found
        if match_start >= 0 and match_length > 0:
            # Find the actual characters to highlight in original text
            highlighted_part = text[match_start:match_start + match_length]
            return text[:match_start] + f"<b>{highlighted_part}</b>" + text[match_start + match_length:]

        return text
    
    def _calculate_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calculate distance between two points using Haversine formula"""
        R = 6371000  # Earth's radius in meters
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lng = math.radians(lng2 - lng1)
        
        a = (math.sin(delta_lat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def _calculate_bbox(self, center: Dict[str, float], radius_m: float = 100) -> BoundingBox:
        """Calculate bounding box around a center point"""
        lat = center["lat"]
        lng = center["lng"]
        
        # Approximate degrees per meter
        lat_delta = radius_m / 111000  # ~111km per degree latitude
        lng_delta = radius_m / (111000 * math.cos(math.radians(lat)))
        
        return BoundingBox(
            minLat=lat - lat_delta,
            minLng=lng - lng_delta,
            maxLat=lat + lat_delta,
            maxLng=lng + lng_delta
        )
    
    def get_uptime(self) -> int:
        """Get service uptime in seconds"""
        return int(time.time() - self.start_time)
    
    def cleanup_expired_sessions(self):
        """Clean up expired session cache entries"""
        current_time = time.time()
        expired_keys = []
        
        for key, data in self._session_cache.items():
            if current_time - data["timestamp"] > 300:  # 5 minutes
                expired_keys.append(key)
        
        for key in expired_keys:
            del self._session_cache[key]


# Global service instance
places_service = PlacesService()
