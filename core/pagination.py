"""
Standard pagination classes for GovAlert REST API.
"""
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardResultsPagination(PageNumberPagination):
    """Default pagination: 20 items per page, max 100."""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'total_pages': self.page.paginator.num_pages,
            'current_page': self.page.number,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data,
        })


class LargeResultsPagination(PageNumberPagination):
    """For large result sets (e.g. notification history): 50 items per page."""
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 200


class SmallResultsPagination(PageNumberPagination):
    """For compact views (e.g. latest alerts): 10 items per page."""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 20
