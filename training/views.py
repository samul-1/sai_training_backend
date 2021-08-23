from django.core.exceptions import ValidationError
from django.db import transaction
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from training.filters import (  # EnrolledOrAllowedCoursesOnly,
    StudentOrAllowedCoursesOnly,
    TeacherOrPersonalTrainingSessionsOnly,
)
from training.models import TrainingTemplate
from training.permissions import (
    AllowedTeacherOrEnrolledOnly,
    EnrolledOnly,
    StudentsOnly,
    TeacherOrReadOnly,
    TeachersOnly,
)
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

    permission_classes = [IsAuthenticated, EnrolledOnly]
    filter_backends = [TeacherOrPersonalTrainingSessionsOnly]

    serializer_action_classes = {
        "retrieve": TrainingSessionOutcomeSerializer,
        "list": TrainingSessionOutcomeSerializer,
    }

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(course=self.kwargs["course_pk"])

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
                return Response(
                    status=status.HTTP_204_NO_CONTENT,
                    # data={"message": "Please specify a template id."},
                )
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
                course__pk=course_id, trainee=request.user, in_progress=True
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
    permission_classes = [
        IsAuthenticated,
        TeacherOrReadOnly,
    ]
    filter_backends = [StudentOrAllowedCoursesOnly]

    def perform_create(self, serializer):
        serializer.save(
            creator=self.request.user,
        )

    def _get_serializer_context(self, request):
        return {
            "request": request,
        }

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated, StudentsOnly],
    )
    def enroll(self, request, **kwargs):
        course = self.get_object()
        course.enrolled_students.add(request.user)

        serializer = CourseSerializer(
            instance=course, context=self._get_serializer_context(request)
        )
        return Response(serializer.data)


class TrainingTemplateViewSet(viewsets.ModelViewSet):
    serializer_class = TrainingTemplateSerializer
    queryset = TrainingTemplate.objects.all()
    permission_classes = [IsAuthenticated, AllowedTeacherOrEnrolledOnly]
    # filter_backends = [EnrolledOrAllowedCoursesOnly]

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(course=self.kwargs["course_pk"], custom=False)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    def perform_create(self, serializer):
        is_custom = not self.request.user.is_teacher
        serializer.save(
            course_id=self.kwargs["course_pk"],
            custom=is_custom,
            creator=self.request.user,
        )


class TopicViewSet(viewsets.ModelViewSet):
    serializer_class = TopicSerializer
    queryset = Topic.objects.all()
    permission_classes = [
        IsAuthenticated,
        AllowedTeacherOrEnrolledOnly,
        TeacherOrReadOnly,
    ]
    # filter_backends = [EnrolledOrAllowedCoursesOnly]

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(course=self.kwargs["course_pk"])

    def perform_create(self, serializer):
        serializer.save(course_id=self.kwargs["course_pk"])


class QuestionViewSet(viewsets.ModelViewSet):
    serializer_class = QuestionSerializer
    queryset = Question.objects.all().prefetch_related("choices")
    permission_classes = [
        IsAuthenticated,
        AllowedTeacherOrEnrolledOnly,
        TeacherOrReadOnly,
    ]
    # filter_backends = [EnrolledOrAllowedCoursesOnly]

    def get_queryset(self):
        queryset = super().get_queryset()
        try:
            queryset = queryset.filter(course=self.kwargs["course_pk"])
        except KeyError:
            pass
        try:
            queryset = queryset.filter(topic=self.kwargs["topic_pk"])
        except KeyError:
            pass

        return queryset

    def perform_create(self, serializer):
        topic_pk = self.kwargs.pop("topic_pk", None)
        kwargs = {}
        if topic_pk is not None:
            # if `topic_pk` is in kwargs, it means the viewset is being accessed
            # from `courses/<id>/topics/<id>/questions`, therefore the question(s)
            # will be created under the topic specified in the url - otherwise, use
            # the topic id inside the request data for the question(s)
            kwargs["topic_id"] = topic_pk
        serializer.save(
            creator=self.request.user,
            course_id=self.kwargs["course_pk"],
            **kwargs,
        )

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        print(request.data)
        many = isinstance(request.data, list)
        print(many)
        serializer = self.get_serializer(data=request.data, many=many)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, headers=headers)

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)
