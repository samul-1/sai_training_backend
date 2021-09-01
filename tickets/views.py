from rest_framework import viewsets

from .models import Ticket
from .permissions import TeacherOrWriteOnly
from .serializers import TicketSerializer


class TicketViewSet(viewsets.ModelViewSet):
    serializer_class = TicketSerializer
    queryset = Ticket.objects.all()
    permission_classes = [TeacherOrWriteOnly]
