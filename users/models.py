from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    is_teacher = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        creating = self.pk is None
        super(User, self).save(*args, **kwargs)
        if creating and self.email.split("@")[1] == "unipi.it":
            self.is_teacher = True
            self.save()

    @property
    def full_name(self):
        return self.first_name.capitalize() + " " + self.last_name.capitalize()
