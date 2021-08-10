from django.core.exceptions import ValidationError
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
    TrainingSessionOutcomeSerializer,
    TrainingSessionSerializer,
)


class TrainingSessionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TrainingSessionSerializer
    queryset = TrainingSession.objects.all()

    serializer_action_classes = {"retrieve": TrainingSessionOutcomeSerializer}

    def get_serializer_class(self):
        try:
            return self.serializer_action_classes[self.action]
        except (KeyError, AttributeError):
            return super().get_serializer_class()

    def _get_serializer_context(self, request):
        return {
            "request": request,
        }

    @action(detail=False, methods=["post"])
    def current(self, request, **kwargs):
        course_id = kwargs.pop("course_pk")
        try:
            session = TrainingSession.objects.get(
                course__pk=course_id, trainee=request.user, in_progress=True
            )
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
                trainee=self.request.user,
                course_id=course_id,
                training_template=training_template,
            )
        context = self._get_serializer_context(request)
        serializer = TrainingSessionSerializer(instance=session, context=context)
        return Response(serializer.data)

    @action(detail=False, methods=["post"])
    def turn_in(self, request, **kwargs):
        course_id = kwargs.pop("course_pk")
        try:
            session = TrainingSession.objects.get(
                course__pk=course_id, user=request.user, in_progress=True
            )
        except TrainingSession.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        try:
            session.turn_in(request.data["answers"])
        except (KeyError, ValidationError):
            return Response(stats=status.HTTP_400_BAD_REQUEST)

        serializer = TrainingSessionOutcomeSerializer(instance=session)
        return Response(serializer.data)


class CourseViewSet(viewsets.ModelViewSet):
    serializer_class = CourseSerializer
    queryset = Course.objects.all()


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
