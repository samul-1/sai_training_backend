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
    enrolled_students = models.ManyToManyField(
        User,
        related_name="enrolled_courses",
        blank=True,
        through="Enrollment",
    )
    created = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Enrollment(models.Model):
    VIA_DIRECT_LINK = 0
    VIA_COURSE_SEARCH = 1

    ENROLLMENT_MODE_CHOICES = (
        (VIA_DIRECT_LINK, "Via direct link"),
        (VIA_COURSE_SEARCH, "Via course search"),
    )

    course = models.ForeignKey(Course, on_delete=models.PROTECT)
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    timestamp = models.DateTimeField(auto_now_add=True)
    mode = models.PositiveSmallIntegerField(
        null=True, blank=True, choices=ENROLLMENT_MODE_CHOICES
    )


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

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["course", "name"], name="same_course_topic_name_unique"
            )
        ]

    def __str__(self):
        return str(self.course) + " - " + self.name


class TrainingTemplate(models.Model):
    name = models.TextField(blank=True)
    course = models.ForeignKey(
        Course, related_name="training_templates", on_delete=models.CASCADE
    )
    description = models.TextField(blank=True)
    creator = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    custom = models.BooleanField(default=False)
    rules = models.ManyToManyField(Topic, through="TrainingTemplateRule")


class TrainingTemplateRuleManager(models.Manager):
    def create(self, total_amount, *args, **kwargs):
        from .difficulty_profiles import BOTTOM_UP, TOP_DOWN

        rule = super().create(*args, **kwargs)

        levels_range = range(AbstractItem.VERY_EASY, AbstractItem.VERY_HARD + 1)
        if rule.difficulty_profile["fall_through_direction"] == TOP_DOWN:
            # start from the highest difficulty level
            levels_range = reversed(levels_range)

        actual_total = 0
        first_level_hit = None
        for level in levels_range:
            try:
                actual_amount = round(total_amount * rule.difficulty_profile[level])
                actual_total += actual_amount

                # bookkeeping variables to choose which level to fill in later in case rounding
                # causes less items to be actually allocated than the requested amount
                if first_level_hit is None:
                    first_level_hit = level
                last_level_hit = level

                setattr(
                    rule,
                    f"amount_{AbstractItem.DIFFICULTY_CHOICES[level][1]}",  # difficulty level name as a string
                    actual_amount,
                )
            except KeyError:
                pass

        # this happens if rounding down percentages caused a lower total than the requested one
        # pick the first or last level visited according to the fall-through rule and fill in the
        # remainder of the items using that level
        if actual_total < total_amount:
            difference = total_amount - actual_total

            if rule.difficulty_profile["fall_through_direction"] == BOTTOM_UP:
                target_level = last_level_hit
            else:
                target_level = first_level_hit

            target_field = f"amount_{AbstractItem.DIFFICULTY_CHOICES[target_level][1]}"
            setattr(rule, target_field, getattr(rule, target_field) + difference)

        rule.save()


class TrainingTemplateRule(models.Model):
    EASY_ONLY = "easy_only"
    HARD_ONLY = "hard_only"
    MOSTLY_EASY = "mostly_easy"
    MOSTLY_HARD = "mostly_hard"
    BALANCED = "balanced"

    DIFFICULTY_PROFILE_CHOICES = (
        (EASY_ONLY, "Easy only"),
        (HARD_ONLY, "Hard only"),
        (MOSTLY_EASY, "Mostly easy"),
        (MOSTLY_HARD, "Mostly hard"),
        (BALANCED, "Balanced"),
    )

    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
    training_template = models.ForeignKey(TrainingTemplate, on_delete=models.CASCADE)
    difficulty_profile_code = models.CharField(
        max_length=11, choices=DIFFICULTY_PROFILE_CHOICES
    )
    amount_very_easy = models.PositiveIntegerField(default=0)
    amount_easy = models.PositiveIntegerField(default=0)
    amount_medium = models.PositiveIntegerField(default=0)
    amount_hard = models.PositiveIntegerField(default=0)
    amount_very_hard = models.PositiveIntegerField(default=0)

    objects = TrainingTemplateRuleManager()

    def clean(self, *args, **kwargs):
        if self.topic not in self.training_template.course.topics.all():
            raise ValidationError("Chosen topic does not belong to template's course.")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    @property
    def difficulty_profile(self):
        from .difficulty_profiles import profiles

        return profiles[self.difficulty_profile_code]

    @property
    def amount(self):
        return (
            self.amount_very_easy
            + self.amount_easy
            + self.amount_medium
            + self.amount_hard
            + self.amount_very_hard
        )


class AbstractItem(models.Model):
    VERY_EASY = 0
    EASY = 1
    MEDIUM = 2
    HARD = 3
    VERY_HARD = 4

    DIFFICULTY_CHOICES = (
        (VERY_EASY, "very_easy"),
        (EASY, "easy"),
        (MEDIUM, "medium"),
        (HARD, "hard"),
        (VERY_HARD, "very_hard"),
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
                "Cannot add a question to a topic for programming exercises"
            )
        if (
            self.topic.items_type == Topic.QUESTIONS
            and type(self) == ProgrammingExercise
        ):
            raise ValidationError(
                "Cannot add a programming exercise to a topic for questions"
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


class Choice(TrackRenderableFieldsMixin):
    question = models.ForeignKey(
        Question, related_name="choices", on_delete=models.CASCADE
    )
    text = models.TextField()
    rendered_text = models.TextField(blank=True)
    correct = models.BooleanField()

    renderable_tex_fields = [
        ("text", "rendered_text"),
    ]

    def __str__(self):
        return f"{self.text[:100]} ({str(self.question)})"


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


class ExerciseTestCase(models.Model):
    exercise = models.ForeignKey(
        ProgrammingExercise,
        related_name="testcases",
        on_delete=models.CASCADE,
    )
    code = models.TextField()
    public = models.BooleanField(default=True)


class ExerciseSubmission(models.Model):
    user = models.ForeignKey(
        User,
        related_name="submissions",
        on_delete=models.PROTECT,
    )
    exercise = models.ForeignKey(
        ProgrammingExercise,
        related_name="submissions",
        on_delete=models.PROTECT,
    )
    code = models.TextField()
    outcomes = models.ManyToManyField(
        ExerciseTestCase, through="TestCaseOutcomeThroughModel"
    )


class TestCaseOutcomeThroughModel(models.Model):
    testcase = models.ForeignKey(ExerciseTestCase, on_delete=models.CASCADE)
    submission = models.ForeignKey(ExerciseSubmission, on_delete=models.CASCADE)
    passed = models.BooleanField()
    details = models.JSONField()


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
    questions = models.ManyToManyField(
        Question,
        related_name="assigned_in_sessions",
        blank=True,
        through="QuestionTrainingSessionThroughModel",
    )


class QuestionTrainingSessionThroughModel(models.Model):
    question = models.ForeignKey(Question, on_delete=models.PROTECT)
    training_session = models.ForeignKey(TrainingSession, on_delete=models.PROTECT)
    selected_choice = models.ForeignKey(
        Choice, blank=True, null=True, on_delete=models.PROTECT
    )

    def clean(self, *args, **kwargs):
        if self.selected_choice not in self.question.choices.all():
            raise ValidationError("Selected choice isn't an option for this question.")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


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
