from rest_framework.permissions import BasePermission


class TeacherOrWriteOnly(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_anonymous and request.user.is_teacher:
            return True

        return request.method == "POST"
