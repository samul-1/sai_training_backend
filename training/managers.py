import math as m

from django.apps import apps
from django.db import models

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
