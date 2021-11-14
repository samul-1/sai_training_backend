from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers
from users.views import EnrolledStudentsViewSet

from . import views

router = routers.SimpleRouter()
router.register(r"courses", views.CourseViewSet, basename="courses")

# achieves `/courses/{pk}/topics/{pk}/questions` and
# `/courses/{pk}/topics/{pk}/programming_exercises`
course_router = routers.NestedSimpleRouter(router, r"courses", lookup="course")
course_router.register(r"topics", views.TopicViewSet, basename="course-topics")
topic_router = routers.NestedSimpleRouter(course_router, r"topics", lookup="topic")
topic_router.register(r"questions", views.QuestionViewSet, basename="topic-questions")
topic_router.register(
    r"programming_exercises",
    views.ProgrammingExerciseViewSet,
    basename="topic-exercises",
)

# achieves `/courses/{pk}/questions`, `/courses/{pk}/programming_exercises`,
# `/courses/{pk}/templates`, `/courses/{pk}/sessions`, and `/courses/{pk}/students`
course_router.register(
    r"templates",
    views.TrainingTemplateViewSet,
    basename="course-training-template",
)
course_router.register(r"questions", views.QuestionViewSet, basename="course-questions")
course_router.register(
    r"programming_exercises",
    views.ProgrammingExerciseViewSet,
    basename="course-questions",
)
course_router.register(
    r"students",
    EnrolledStudentsViewSet,
    basename="course-students",
)

course_router.register(
    r"sessions",
    views.TrainingSessionViewSet,
    basename="course-training-session",
)
urlpatterns = [
    path("", include(router.urls)),
    path("", include(course_router.urls)),
    path("", include(topic_router.urls)),
]
