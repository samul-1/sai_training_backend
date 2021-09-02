from django.conf.urls import url
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("training.urls")),
    path("users/", include("users.urls")),
    path("", include("djoser.urls")),
    path("tickets/", include("tickets.urls")),
    url(r"^auth/", include("rest_framework_social_oauth2.urls")),
]
