import logging
import os
import time

from django.apps import apps

from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.base")

app = Celery("tex_rendering")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

logger = logging.getLogger(__name__)


@app.task(bind=True)
def render_tex_task(self, model, pk, fields):
    from training.tex import tex_to_svg

    re_rendered_fields = {}
    for target, source in fields.items():
        re_rendered_fields[target] = tex_to_svg(source)

    # use `update` to prevent calling `save` again and entering a loop
    apps.get_model(app_label="training", model_name=model).objects.filter(pk=pk).update(
        **re_rendered_fields
    )