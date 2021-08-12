from django.db.models.signals import post_save
from django.dispatch import receiver


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
            # print(f"{source} changed")
            rendered_content = render_tex(getattr(instance, source))
            re_rendered_field_values[target] = rendered_content
        else:
            pass
            # print(f"{source} stayed the same")

    # use `update` to prevent calling `save` again and entering a loop
    sender.objects.filter(pk=instance.pk).update(**re_rendered_field_values)
