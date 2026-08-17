"""Pagination defaults.

Page size is client-adjustable up to a ceiling so the subject catalogue (39 rows
today) can be fetched in one request, while a future dataset cannot be pulled in
its entirety by a single call.
"""

from rest_framework.pagination import PageNumberPagination


class DefaultPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 200
