from importlib.resources import path

from django.urls import include, path
from rest_framework import routers

from tickets import views

router = routers.SimpleRouter()
router.register(r"", views.TicketViewSet, basename="tickets")

urlpatterns = [
    path("", include(router.urls)),
]
