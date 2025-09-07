"""
Enhanced pagination schemas with navigation links
"""
from typing import Optional, List, Generic, TypeVar, Dict, Any
from pydantic import BaseModel, Field, computed_field
from urllib.parse import urlencode

T = TypeVar('T')

class PaginationLinks(BaseModel):
    """Navigation links for pagination"""
    self: str = Field(..., description="Current page URL")
    first: str = Field(..., description="First page URL")
    last: Optional[str] = Field(None, description="Last page URL")
    next: Optional[str] = Field(None, description="Next page URL")
    prev: Optional[str] = Field(None, description="Previous page URL")

class PaginationMeta(BaseModel):
    """Pagination metadata"""
    current_page: int = Field(..., description="Current page number (1-based)")
    per_page: int = Field(..., description="Items per page")
    total_items: int = Field(..., description="Total number of items")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_prev: bool = Field(..., description="Whether there is a previous page")
    
    @computed_field
    @property
    def from_item(self) -> int:
        """First item number on current page"""
        return (self.current_page - 1) * self.per_page + 1
    
    @computed_field
    @property
    def to_item(self) -> int:
        """Last item number on current page"""
        return min(self.current_page * self.per_page, self.total_items)

class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response with navigation links"""
    data: List[T] = Field(..., description="List of items for current page")
    meta: PaginationMeta = Field(..., description="Pagination metadata")
    links: PaginationLinks = Field(..., description="Navigation links")

def build_pagination_links(
    base_url: str,
    current_page: int,
    total_pages: int,
    per_page: int,
    query_params: Optional[Dict[str, Any]] = None
) -> PaginationLinks:
    """
    Build pagination navigation links
    
    Args:
        base_url: Base URL without query parameters
        current_page: Current page number (1-based)
        total_pages: Total number of pages
        per_page: Items per page
        query_params: Additional query parameters to preserve
    
    Returns:
        PaginationLinks object with navigation URLs
    """
    if query_params is None:
        query_params = {}
    
    def build_url(page: int) -> str:
        """Build URL for specific page"""
        params = {**query_params, 'page': page, 'size': per_page}
        # Remove None values
        params = {k: v for k, v in params.items() if v is not None}
        query_string = urlencode(params)
        return f"{base_url}?{query_string}"
    
    # Build navigation links
    links = PaginationLinks(
        self=build_url(current_page),
        first=build_url(1),
        last=build_url(total_pages) if total_pages > 0 else build_url(1),
        next=build_url(current_page + 1) if current_page < total_pages else None,
        prev=build_url(current_page - 1) if current_page > 1 else None
    )
    
    return links

def create_paginated_response(
    items: List[T],
    total_items: int,
    current_page: int,
    per_page: int,
    base_url: str,
    query_params: Optional[Dict[str, Any]] = None
) -> PaginatedResponse[T]:
    """
    Create a standardized paginated response
    
    Args:
        items: List of items for current page
        total_items: Total number of items across all pages
        current_page: Current page number (1-based)
        per_page: Items per page
        base_url: Base URL for building navigation links
        query_params: Additional query parameters to preserve in links
    
    Returns:
        PaginatedResponse with data, metadata, and navigation links
    """
    total_pages = (total_items + per_page - 1) // per_page if total_items > 0 else 1
    
    meta = PaginationMeta(
        current_page=current_page,
        per_page=per_page,
        total_items=total_items,
        total_pages=total_pages,
        has_next=current_page < total_pages,
        has_prev=current_page > 1
    )
    
    links = build_pagination_links(
        base_url=base_url,
        current_page=current_page,
        total_pages=total_pages,
        per_page=per_page,
        query_params=query_params
    )
    
    return PaginatedResponse(
        data=items,
        meta=meta,
        links=links
    )

# Utility function to get base URL from request
def get_base_url(request, path: str) -> str:
    """
    Extract base URL from FastAPI request
    
    Args:
        request: FastAPI Request object
        path: API endpoint path
    
    Returns:
        Base URL string
    """
    return f"{request.url.scheme}://{request.url.netloc}{path}"

# Legacy pagination response for backward compatibility
class LegacyPaginatedResponse(BaseModel, Generic[T]):
    """Legacy pagination format for backward compatibility"""
    items: List[T] = Field(..., description="List of items (legacy field name)")
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Items per page")
    pages: int = Field(..., description="Total number of pages")
