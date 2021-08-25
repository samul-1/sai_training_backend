from core.celery import render_tex_task
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save)
def render_tex_fields(sender, instance, created, **kwargs):
    if not hasattr(sender, "renderable_tex_fields"):
        return

    re_render_fields = {}
    for (source, target) in sender.renderable_tex_fields:
        value_changed = created or (
            getattr(instance, source) != getattr(instance, f"_old_{source}")
        )
        if value_changed:
            re_render_fields[target] = getattr(instance, source)

    render_tex_task.delay(
        model=sender.__name__, pk=instance.pk, fields=re_render_fields
    )
