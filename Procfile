release: python manage.py migrate
web: gunicorn core.wsgi
worker: python manage.py runworker --settings=core.settings.base -v2
celery: celery -A core worker -l INFO
