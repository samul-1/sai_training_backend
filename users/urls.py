from django.urls import include, path, re_path

from . import views

urlpatterns = [
    path("teachers/", views.TeacherList.as_view(), name="teacher-list"),
]
