from django.db import models
from users.models import User


class Ticket(models.Model):
    user = models.ForeignKey(
        User,
        related_name="tickets",
        null=True,
        on_delete=models.SET_NULL,
    )
    created = models.DateTimeField(auto_now_add=True)
    message = models.TextField()
    additional_data = models.JSONField(blank=True, null=True)

    def __str__(self):
        return (
            (self.user.full_name if self.user is not None else "Anonyumous")
            + " - "
            + self.message[:100]
        )
