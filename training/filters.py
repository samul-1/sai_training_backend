from django.db.models import Q
from rest_framework import filters

from training.models import Course


class StudentOrAllowedCoursesOnly(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        if not request.user.is_teacher:
            return queryset
        return queryset.filter(
            Q(creator=request.user) | Q(allowed_teachers__in=[request.user])
        )


class EnrolledOrAllowedCoursesOnly(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        if queryset.model is Course:
            if request.user.is_teacher:
                return queryset.filter(
                    Q(creator=request.user) | Q(allowed_teachers__in=[request.user])
                )
            else:
                return queryset.filter(enrolled_students__in=[request.user])

        if request.user.is_teacher:
            return queryset.filter(
                Q(course__creator=request.user)
                | Q(course__allowed_teachers__in=[request.user])
            )

        return queryset.filter(course__enrolled_students__in=[request.user])


class TeacherOrPersonalTrainingSessionsOnly(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        if request.user.is_teacher:
            return queryset

        return queryset.filter(trainee=request.user)
