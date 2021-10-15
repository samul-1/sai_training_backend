from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from training import difficulty_profiles, texts
from training.filters import (
    OwnedOnlyTrainingTemplates,
    StudentOrAllowedCoursesOnly,
    TeacherOrPersonalTrainingSessionsOnly,
)
from training.logic import get_concrete_difficulty_profile_amounts, get_items
from training.models import ExerciseSubmission, ProgrammingExercise, TrainingTemplate
from training.pagination import CourseItemPagination
from training.permissions import (
    AllowedTeacherOrEnrolledOnly,
    EnrolledOnly,
    StudentsOnly,
    TeacherOrReadOnly,
    TeachersOnly,
)
from training.serializers import (
    ProgrammingExerciseSerializer,
    SubmissionSerializer,
    TrainingTemplateSerializer,
)

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
            return Response(status=status.HTTP_400_BAD_REQUEST)

        serializer = TrainingSessionOutcomeSerializer(
            instance=session, context=self._get_serializer_context(request)
        )
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

    @action(
        detail=True,
        methods=["get"],
        # permission_classes=[IsAuthenticated, StudentsOnly],
    )
    @method_decorator(cache_page(60 * 60 * 12))
    def stats(self, request, **kwargs):
        course = self.get_object()

        data = {
            "number_enrolled": course.number_enrolled,
            "training_sessions": course.training_sessions.count(),
            "average_correct_percentage": course.average_correct_percentage,
        }

        return Response(data)


class TrainingTemplateViewSet(viewsets.ModelViewSet):
    serializer_class = TrainingTemplateSerializer
    queryset = TrainingTemplate.objects.all()
    permission_classes = [IsAuthenticated, AllowedTeacherOrEnrolledOnly]
    filter_backends = [OwnedOnlyTrainingTemplates]

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(course=self.kwargs["course_pk"])

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
        from django.db.models import Count

        queryset = super().get_queryset()
        queryset = queryset.filter(course=self.kwargs["course_pk"])
        if not self.request.user.is_teacher:
            # only return topics that contain at least one item
            queryset = queryset.annotate(
                questions_count=Count("questions"),
                exercises_count=Count("programmingexercises"),
            ).filter(Q(questions_count__gt=0) | Q(exercises_count__gt=0))

        return queryset

    def create(self, request, *args, **kwargs):
        try:
            return super().create(request, *args, **kwargs)
        except IntegrityError:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={"message": texts.TOPIC_NAME_ALREADY_EXISTS},
            )

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
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["difficulty"]
    pagination_class = CourseItemPagination

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
        many = isinstance(request.data, list)
        serializer = self.get_serializer(data=request.data, many=many)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, headers=headers)

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)


class ProgrammingExerciseViewSet(viewsets.ModelViewSet):
    serializer_class = ProgrammingExerciseSerializer
    queryset = ProgrammingExercise.objects.all().prefetch_related("testcases")
    permission_classes = [
        IsAuthenticated,
        AllowedTeacherOrEnrolledOnly,
        TeacherOrReadOnly,
    ]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["difficulty"]
    pagination_class = CourseItemPagination

    def _get_serializer_context(self, request):
        return {
            "request": request,
        }

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

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated, AllowedTeacherOrEnrolledOnly],
    )
    def submit(self, request, **kwargs):
        try:
            code = request.data["code"]
            submission = ExerciseSubmission.objects.create(
                exercise=self.get_object(), user=request.user, code=code
            )
        except KeyError:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        serializer = SubmissionSerializer(instance=submission)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def history(self, request, **kwargs):
        exercises = self.get_queryset().seen_by(request.user)

        serializer = ProgrammingExerciseSerializer(
            data=exercises,
            many=True,
            context=self._get_serializer_context(request),
        )
        serializer.is_valid()
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def bulk_get(self, request, **kwargs):
        try:
            ids = request.query_params["ids"]
            id_list = ids.split(",")
        except KeyError:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        exercises = []
        course = get_object_or_404(Course, pk=self.kwargs["course_pk"])

        for pk in id_list:
            exercise = get_object_or_404(course.programmingexercises.all(), pk=pk)
            exercises.append(exercise)

        serializer = ProgrammingExerciseSerializer(
            data=exercises,
            many=True,
            context=self._get_serializer_context(request),
        )
        serializer.is_valid()
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def get_matching_items(self, request, **kwargs):
        try:
            difficulty_profile = request.query_params["difficulty_profile"]
            amount = int(request.query_params["amount"])
            if difficulty_profile not in difficulty_profiles.profiles:
                raise KeyError
            topic_id = self.kwargs["topic_pk"]
        except (KeyError, ValueError):
            return Response(status=status.HTTP_400_BAD_REQUEST)

        course = get_object_or_404(Course, pk=self.kwargs["course_pk"])
        topic = get_object_or_404(course.topics.all(), pk=topic_id)

        exercises = get_items(
            ProgrammingExercise,
            topic,
            get_concrete_difficulty_profile_amounts(
                difficulty_profiles.profiles[difficulty_profile], amount
            ),
            difficulty_profiles.profiles[difficulty_profile],
            [],  # exclude exercises for which user has already submitted solution(s)
        )

        serializer = ProgrammingExerciseSerializer(
            data=exercises,
            many=True,
            context=self._get_serializer_context(request),
        )
        serializer.is_valid()
        return Response(serializer.data)

    def perform_create(self, serializer):
        topic_pk = self.kwargs.pop("topic_pk", None)
        kwargs = {}
        if topic_pk is not None:
            # if `topic_pk` is in kwargs, it means the viewset is being accessed
            # from `courses/<id>/topics/<id>/programming_exercises`,
            # therefore the exercise(s) will be created
            # under the topic specified in the url - otherwise, use
            # the topic id inside the request data for the exercise(s)
            kwargs["topic_id"] = topic_pk
        serializer.save(
            creator=self.request.user,
            course_id=self.kwargs["course_pk"],
            **kwargs,
        )

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        many = isinstance(request.data, list)
        serializer = self.get_serializer(data=request.data, many=many)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, headers=headers)

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)
