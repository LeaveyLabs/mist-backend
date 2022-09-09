web: gunicorn backend.wsgi
release: python3 manage.py migrate
celery: python3 -m celery -A backend worker -l info -B --concurrency=2