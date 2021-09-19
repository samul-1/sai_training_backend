from rest_framework import viewsets
from rest_framework.exceptions import Throttled

from tickets import throttles

from .models import Ticket
from .permissions import TeacherOrWriteOnly
from .serializers import TicketSerializer


class TicketViewSet(viewsets.ModelViewSet):
    serializer_class = TicketSerializer
    queryset = Ticket.objects.all()
    permission_classes = [TeacherOrWriteOnly]
    throttle_classes = [
        throttles.AnonTicketSubmissionThrottle,
        throttles.UserTicketSubmissionThrottle,
    ]

    def perform_create(self, serializer):
        serializer.save(
            user=self.request.user if not self.request.user.is_anonymous else None,
        )

    def throttled(self, request, wait):
        raise Throttled(
            detail={
                "message": "Puoi inviare una segnalazione all'ora. Riprova più tardi.",
                "availableIn": f"{wait} seconds",
                "throttleType": "type",
            }
        )
