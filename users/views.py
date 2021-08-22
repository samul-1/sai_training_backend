from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from .models import User
from .serializers import UserSerializer


class TeacherList(generics.ListAPIView):
    """
    API view to retrieve a list of all teachers
    """

    queryset = User.objects.filter(is_teacher=True)
    serializer_class = UserSerializer


# permission_classes = [IsAuthenticated, TeachersOnly]
