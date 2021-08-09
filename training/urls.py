from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers

from . import views

router = routers.SimpleRouter()
router.register(r"courses", views.CourseViewSet, basename="courses")

course_router = routers.NestedSimpleRouter(router, r"courses")
course_router.register(r"topics", views.TopicViewSet, basename="course-topics")
topic_router = routers.NestedSimpleRouter(course_router, r"topics")
topic_router.register(r"questions", views.QuestionViewSet, basename="topic-questions")


urlpatterns = [
    path("", include(router.urls)),
    path("", include(course_router.urls)),
    path("", include(topic_router.urls)),
]
