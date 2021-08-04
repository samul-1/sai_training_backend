from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from users.models import User


class Course(models.Model):
    name = models.TextField(unique=True)
    creator = models.ForeignKey(
        User, related_name="created_courses", on_delete=models.PROTECT
    )
    allowed_teachers = models.ManyToManyField(
        User,
        related_name="visible_courses",
        blank=True,
    )
    created = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Topic(models.Model):
    PROGRAMMING_EXERCISES = "e"
    QUESTIONS = "q"

    TOPIC_ITEM_TYPES = (
        (PROGRAMMING_EXERCISES, "Programming exercises"),
        (QUESTIONS, "Questions"),
    )

    name = models.TextField()
    description = models.TextField(blank=True)
    course = models.ForeignKey(
        Course,
        on_delete=models.PROTECT,
        related_name="topics",
    )
    items_type = models.CharField(
        max_length=1, choices=TOPIC_ITEM_TYPES, default=QUESTIONS
    )
    help_text = models.TextField(blank=True)
    error_percentage_for_help_text = models.DecimalField(
        null=True, blank=True, decimal_places=2, max_digits=5
    )

    def __str__(self):
        return str(self.course) + " - " + self.name


class TrainingTemplate(models.Model):
    name = models.TextField(blank=True)
    description = models.TextField(blank=True)
    creator = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    custom = models.BooleanField(default=False)
    rules = models.ManyToManyField(Topic, through="TrainingTemplateRule")


class TrainingTemplateRule(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
    training_template = models.ForeignKey(TrainingTemplate, on_delete=models.CASCADE)
    amount = models.PositiveIntegerField()
    difficulty = models.PositiveIntegerField()


class TrainingSession(models.Model):
    trainee = models.ForeignKey(
        User, related_name="training_sessions", on_delete=models.SET_NULL, null=True
    )
    course = models.ForeignKey(
        Course, related_name="training_sessions", on_delete=models.PROTECT
    )
    training_template = models.ForeignKey(
        TrainingTemplate,
        related_name="training_sessions",
        on_delete=models.SET_NULL,
        null=True,
    )
    timestamp = models.DateTimeField(auto_now_add=True)


class AbstractItem(models.Model):
    VERY_EASY = 0
    EASY = 1
    MEDIUM = 2
    HARD = 3
    VERY_HARD = 4

    DIFFICULTY_CHOICES = (
        (VERY_EASY, "Very easy"),
        (EASY, "Easy"),
        (MEDIUM, "Medium"),
        (HARD, "Hard"),
        (VERY_HARD, "Very hard"),
    )

    course = models.ForeignKey(
        Course,
        on_delete=models.PROTECT,
        related_name="%(class)s",
    )
    topic = models.ForeignKey(
        Topic,
        on_delete=models.PROTECT,
        related_name="%(class)s",
    )
    creator = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    difficulty = models.PositiveSmallIntegerField(choices=DIFFICULTY_CHOICES)
    imported_from_exam = models.BooleanField(default=False)

    class Meta:
        abstract = True

    def __str__(self):
        return self.text[:100]

    def clean(self, *args, **kwargs):
        if self.topic not in self.course.topics.all():
            raise ValidationError("Chosen topic doesn't belong to chosen course")
        if (
            self.topic.items_type == Topic.PROGRAMMING_EXERCISES
            and type(self) == Question
        ):
            raise ValidationError(
                "Cannot add a question to a category for programming exercises"
            )
        if (
            self.topic.items_type == Topic.QUESTIONS
            and type(self) == ProgrammingExercise
        ):
            raise ValidationError(
                "Cannot add a programming exercise to a category for questions"
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super(AbstractItem, self).save(*args, **kwargs)


class TrackRenderableFieldsMixin(models.Model):
    class Meta:
        abstract = True

    @classmethod
    def from_db(cls, db, field_names, values):
        instance = super().from_db(db, field_names, values)
        for (source, _) in cls.renderable_tex_fields:
            setattr(instance, f"_old_{source}", getattr(instance, source))

        return instance


class Question(TrackRenderableFieldsMixin, AbstractItem):
    text = models.TextField()
    rendered_text = models.TextField(blank=True)
    solution = models.TextField(blank=True)
    rendered_solution = models.TextField(blank=True)

    renderable_tex_fields = [
        ("text", "rendered_text"),
        ("solution", "rendered_solution"),
    ]


class ProgrammingExercise(TrackRenderableFieldsMixin, AbstractItem):
    text = models.TextField()
    rendered_text = models.TextField(blank=True)
    initial_code = models.TextField(blank=True)
    minimum_passing_testcases = models.PositiveSmallIntegerField(default=1)
    solution = models.TextField(blank=True)
    rendered_solution = models.TextField(blank=True)

    renderable_tex_fields = [
        ("text", "rendered_text"),
        ("solution", "rendered_solution"),
    ]


def render_tex(string):
    return f"rendered - {string}"


@receiver(post_save)
def render_tex_fields(sender, instance, created, **kwargs):
    if not hasattr(sender, "renderable_tex_fields"):
        return

    re_rendered_field_values = {}
    for (source, target) in sender.renderable_tex_fields:
        value_changed = created or (
            getattr(instance, source) != getattr(instance, f"_old_{source}")
        )
        if value_changed:
            print(f"{source} changed")
            rendered_content = render_tex(getattr(instance, source))
            re_rendered_field_values[target] = rendered_content
        else:
            print(f"{source} stayed the same")

    # use `update` to prevent calling `save` again and entering a loop
    sender.objects.filter(pk=instance.pk).update(**re_rendered_field_values)
