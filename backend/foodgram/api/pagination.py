from rest_framework.pagination import PageNumberPagination


class CustomPaginator(PageNumberPagination):
    limit= 2
    page_size_query_param = 'limit'
