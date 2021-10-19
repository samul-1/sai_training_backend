from django.shortcuts import get_object_or_404
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from training.filters import StudentOrAllowedCoursesOnly
from training.models import Course
from training.permissions import TeachersOnly
from training.serializers import TrainingSessionOutcomeSerializer

from .models import User
from .serializers import UserSerializer


class TeacherList(generics.ListAPIView):
    """
    API view to retrieve a list of all teachers
    """

    queryset = User.objects.filter(is_teacher=True)
    serializer_class = UserSerializer


# permission_classes = [IsAuthenticated, TeachersOnly]


class EnrolledStudentsViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    # queryset = User.objects.all()
    permission_classes = [
        IsAuthenticated,
        TeachersOnly,
    ]
    # filter_backends = [StudentOrAllowedCoursesOnly]

    def get_queryset(self):
        course = Course.objects.get(
            pk=self.kwargs["course_pk"]
        )  # TODO check filtering, permissions, 404
        return course.enrolled_students.all()

    @action(detail=True, methods=["get"])
    def history(self, request, **kwargs):
        user = (
            self.get_object()
        )  # get_object_or_404(self.get_queryset(), pk=self.kwargs["pk"])
        # print(user)
        sessions = user.training_sessions.filter(course_id=self.kwargs["course_pk"])

        serializer = TrainingSessionOutcomeSerializer(
            sessions,
            many=True,
            context={
                "request": request,
            },
        )
        return Response(serializer.data)
