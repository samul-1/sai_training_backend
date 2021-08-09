from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from training.models import TrainingTemplate
from training.serializers import TrainingTemplateSerializer

from .models import Course, Question, Topic, TrainingSession
from .serializers import (
    CourseSerializer,
    QuestionSerializer,
    TopicSerializer,
    TrainingSessionSerializer,
)


class CourseViewSet(viewsets.ModelViewSet):
    serializer_class = CourseSerializer
    queryset = Course.objects.all()

    @action(detail=True, methods=["post"])
    def my_training_session(self, request, **kwargs):
        course_id = kwargs.pop("pk")
        try:
            session = TrainingSession.objects.get(course__pk=course_id)
        except TrainingSession.DoesNotExist:
            # a new session is being initiated: check that a training template
            # has been supplied in the request
            try:
                training_template = TrainingTemplate.objects.get(
                    pk=request.query_params["template_id"]
                )
            except KeyError:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            except TrainingTemplate.DoesNotExist:
                return Response(status=status.HTTP_404_NOT_FOUND)

            session = TrainingSession.objects.create(
                user=self.request.user,
                course_id=course_id,
                training_template=training_template,
            )

        serializer = TrainingSessionSerializer(instance=session)
        return Response(serializer.data)


class TrainingTemplateViewSet(viewsets.ModelViewSet):
    serializer_class = TrainingTemplateSerializer
    queryset = TrainingTemplate.objects.all()

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(course=self.kwargs["course_pk"])


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
