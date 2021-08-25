from rest_framework.pagination import PageNumberPagination


class CourseItemPagination(PageNumberPagination):
    page_size = 10
