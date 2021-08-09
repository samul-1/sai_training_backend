from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Course, Question, Topic, TrainingSession
from .serializers import (
    CourseSerializer,
    QuestionSerializer,
    TopicSerializer,
    TrainingSessionSerializer,
)


class TrainingSessionEndPoint(viewsets.ModelViewSet):
    queryset = TrainingSession.objects.all()
    serializer_class = TrainingSessionSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(course=self.kwargs["course_pk"], user=self.request.user)

    def list(self, request, *args, **kwargs):
        return Response(data="get'd")

    def post(self, request, *args, **kwargs):
        return Response("post'd")


class CourseViewSet(viewsets.ModelViewSet):
    serializer_class = CourseSerializer
    queryset = Course.objects.all()


class TopicViewSet(viewsets.ModelViewSet):
    serializer_class = TopicSerializer
    queryset = Topic.objects.all()

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(course=self.kwargs["course_pk"])

    def perform_create(self, serializer):
        serializer.save(course_id=self.kwargs["course_pk"])


class QuestionViewSet(viewsets.ModelViewSet):
    serializer_class = QuestionSerializer
    queryset = Question.objects.all().prefetch_related("choices")

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(topic=self.kwargs["topic_pk"])

    def perform_create(self, serializer):
        serializer.save(
            creator=self.request.user,
            course_id=self.kwargs["course_pk"],
            topic_id=self.kwargs["topic_pk"],
        )
