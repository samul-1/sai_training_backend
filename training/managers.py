import math as m

from django.apps import apps
from django.db import models
from django.db.models import Count, Exists, OuterRef, Q

from training.logic import get_concrete_difficulty_profile_amounts

from .logic import get_items


class TrainingSessionManager(models.Manager):
    def create(self, *args, **kwargs):
        session = super().create(*args, **kwargs)

        position = 0
        for rule in session.training_template.trainingtemplaterule_set.all():
            questions = get_items(
                apps.get_model(app_label="training", model_name="Question"),
                rule.topic,
                {
                    "amount_very_easy": rule.amount_very_easy,
                    "amount_easy": rule.amount_easy,
                    "amount_medium": rule.amount_medium,
                    "amount_hard": rule.amount_hard,
                    "amount_very_hard": rule.amount_very_hard,
                },
                rule.difficulty_profile,
                [],
            )
            for question in questions:
                session.questions.add(question, through_defaults={"position": position})
                position += 1
        return session


class TrainingTemplateRuleManager(models.Manager):
    def create(self, amount, *args, **kwargs):
        from training.models import TrainingTemplateRule

        rule = super().create(*args, **kwargs)
        concrete_amounts = get_concrete_difficulty_profile_amounts(
            rule.difficulty_profile, amount
        )
        for (
            field,
            value,
        ) in concrete_amounts.items():  # TODO find out why `update` isn't working
            setattr(rule, field, value)

        rule.save()

        # TrainingTemplateRule.objects.filter(pk=rule.pk).update(**concrete_amounts)

        return rule


class ProgrammingExerciseQuerySet(models.QuerySet):
    def seen_by(self, user):
        exists_submission = apps.get_model(
            "training.ExerciseSubmission"
        ).objects.filter(user=user, exercise=OuterRef("pk"))
        return self.annotate(
            submission_exists=Exists(exists_submission),
        ).filter(submission_exists=True)


class TrainingTemplatesQuerySet(models.QuerySet):
    def recently_used_by(self, user, course_id):
        recent_training_sessions_templates = (
            apps.get_model("training.TrainingSession")
            .objects.filter(
                trainee=user,
                course_id=course_id,
                training_template__custom=True,
            )
            .order_by("-begin_timestamp")[:4]
            .values_list("training_template_id")
        )  # get the templates of the three most recent training sessions from this user
        return (
            apps.get_model("training.TrainingTemplate")
            .objects.filter(
                Q(custom=False) | Q(pk__in=recent_training_sessions_templates)
            )
            .filter(course_id=course_id)
            .distinct()
        )


class TrainingTemplateManager(models.Manager):
    def get_queryset(self):
        return TrainingTemplatesQuerySet(self.model, using=self._db)

    def recently_used_by(self, user, course_id):
        return self.get_queryset().recently_used_by(user, course_id)


class ProgrammingExerciseManager(models.Manager):
    def get_queryset(self):
        return ProgrammingExerciseQuerySet(self.model, using=self._db)

    def seen_by(self, user):
        return self.get_queryset().seen_by(user)
