from django.db.models import Q
from rest_framework import filters

from training.models import Course


class StudentOrAllowedCoursesOnly(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        if not request.user.is_teacher:
            return queryset

        return queryset.filter(
            Q(creator=request.user) | Q(allowed_teachers__in=[request.user])
        ).distinct()  # ! keep an eye on this


class OwnedOnlyTrainingTemplates(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        if request.user.is_teacher:
            return queryset.filter(custom=False)

        return queryset.recently_used_by(request.user, view.kwargs["course_pk"])


class TeacherOrPersonalTrainingSessionsOnly(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        if request.user.is_teacher:
            return queryset

        return queryset.filter(trainee=request.user, in_progress=False)
