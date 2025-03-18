from rest_framework.pagination import PageNumberPagination

class CustomPageNumberPagination(PageNumberPagination):
    page_size = 10   # Default number of items per page
    page_size_query_param = 'page_size' # Allow clients to override page_size
    max_page_size = 100 # Maximum number of items per page