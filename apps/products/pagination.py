"""
Custom pagination classes for Affiliate Products API.
"""

from rest_framework.pagination import PageNumberPagination, CursorPagination
from rest_framework.response import Response


class StandardResultsPagination(PageNumberPagination):
    """
    Standard pagination with configurable page size.
    
    Default: 20 items per page
    Max: 100 items per page
    
    Usage:
        GET /api/v1/products/?page=1&page_size=20
    """
    
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    page_query_param = 'page'

    def get_paginated_response(self, data):
        """Return pagination metadata along with results."""
        return Response({
            'pagination': {
                'count': self.page.paginator.count,
                'total_pages': self.page.paginator.num_pages,
                'current_page': self.page.number,
                'page_size': self.get_page_size(self.request),
                'next': self.get_next_link(),
                'previous': self.get_previous_link(),
            },
            'results': data
        })


class LargeResultsPagination(PageNumberPagination):
    """
    Pagination for endpoints that return larger datasets.
    
    Default: 50 items per page
    Max: 200 items per page
    
    Usage:
        GET /api/v1/products/?page=1&page_size=50
    """
    
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 200

    def get_paginated_response(self, data):
        """Return pagination metadata along with results."""
        return Response({
            'pagination': {
                'count': self.page.paginator.count,
                'total_pages': self.page.paginator.num_pages,
                'current_page': self.page.number,
                'page_size': self.get_page_size(self.request),
                'next': self.get_next_link(),
                'previous': self.get_previous_link(),
            },
            'results': data
        })


class ProductCursorPagination(CursorPagination):
    """
    Cursor-based pagination for infinite scroll.
    
    More efficient for large datasets and real-time updates.
    Doesn't allow jumping to specific pages but handles
    real-time data changes gracefully.
    
    Usage:
        GET /api/v1/products/?cursor=cD0yMDI0LTAx...
    """
    
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 50
    ordering = '-created_at'
    cursor_query_param = 'cursor'

    def get_paginated_response(self, data):
        """Return cursor pagination response."""
        return Response({
            'pagination': {
                'next': self.get_next_link(),
                'previous': self.get_previous_link(),
                'page_size': self.get_page_size(self.request),
            },
            'results': data
        })