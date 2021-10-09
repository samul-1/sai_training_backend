import logging
import os
import time
from random import randint
from time import sleep

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

    print("RECEIVED")

    re_rendered_fields = {}
    for target, source in fields.items():
        re_rendered_fields[target] = tex_to_svg(source)

    # for some reason, sometimes the object to be updated isn't immediately
    # found using `filter` with its pk (!), so `update` is called and its return
    # value gets checked - if it's 1, the object was correctly updated, otherwise
    # celery should retry to fetch it. it *is* in the database, as this is called
    # post_save and explicitly passed the object's pk; it's just that sometimes the
    # first query returns an empty queryset (no clue why), so retrying shortly after
    # is necessary
    while True:
        # ! if you have problems again, try testing
        # ! `apps.get_model(...).filter(...)count()` against 0 instead of
        # ! the return value of `update`
        if (
            apps.get_model(app_label="training", model_name=model)
            .objects.filter(pk=pk)
            .update(**re_rendered_fields)
        ) == 1:  # object was correctly updated
            break
        # retry in a bit
        print("SLEEPING")
        sleep(randint(1, 5))

    print("OUT")
