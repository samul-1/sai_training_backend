from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    COURSES = (
        ("a", "Corso A"),
        ("b", "Corso B"),
        ("c", "Corso C"),
    )
    is_teacher = models.BooleanField(default=False)
    course = models.CharField(max_length=1, blank=True, null=True, choices=COURSES)

    def save(self, *args, **kwargs):
        creating = not self.pk  # see if the objects exists already or is being created
        super(User, self).save(*args, **kwargs)  # create the object
        if creating and self.email.split("@")[1] == "unipi.it":
            self.is_teacher = True
            self.save()

    @property
    def full_name(self):
        return self.first_name.capitalize() + " " + self.last_name.capitalize()
