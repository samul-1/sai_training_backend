from rest_framework.permissions import SAFE_METHODS, BasePermission

from training.models import Course, Topic


class TeacherOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_teacher:
            return True

        return request.method in SAFE_METHODS


class EnrolledOnly(BasePermission):
    def has_permission(self, request, view):
        try:
            course = Course.objects.get(pk=view.kwargs["course_pk"])
        except KeyError:
            topic = Topic.objects.get(pk=view.kwargs["topic_pk"])
            course = Course.objects.get(pk=topic.course.pk)

        return request.user in course.enrolled_students.all()


class AllowedTeacherOrEnrolledOnly(BasePermission):
    def has_permission(self, request, view):
        try:
            course = Course.objects.get(pk=view.kwargs["course_pk"])
        except KeyError:
            topic = Topic.objects.get(pk=view.kwargs["topic_pk"])
            course = Course.objects.get(pk=topic.course.pk)

        if request.user.is_teacher:
            return (
                request.user == course.creator
                or request.user in course.allowed_teachers.all()
            )

        return request.user in course.enrolled_students.all()


class TeachersOnly(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_teacher


class StudentsOnly(BasePermission):
    def has_permission(self, request, view):
        return not request.user.is_teacher
