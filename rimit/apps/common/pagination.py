from __future__ import annotations

from typing import Optional

from rest_framework.pagination import PageNumberPagination
from rest_framework.request import Request


class ApiPageNumberPagination(PageNumberPagination):
    """Project-standard pagination.

    - Default page size is 25 (matches historical settings).
    - Supports client-controlled `?page_size=` up to `max_page_size`.
    - Back-compat: accepts legacy `?limit=` as an alias for `page_size`.
    """

    page_size = 25
    page_size_query_param = 'page_size'
    max_page_size = 200

    def get_page_size(self, request: Request) -> Optional[int]:
        # Prefer the new canonical query param.
        size = super().get_page_size(request)
        if size is not None:
            return size

        # Back-compat for older UIs: treat `limit` as `page_size`.
        limit = request.query_params.get('limit')
        if not limit:
            return None

        try:
            parsed = int(limit)
        except (TypeError, ValueError):
            return None

        if parsed <= 0:
            return None

        if self.max_page_size is not None:
            return min(parsed, self.max_page_size)
        return parsed
