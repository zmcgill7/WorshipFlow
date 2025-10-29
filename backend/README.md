# Worship Flow — Backend

This is the backend which is to be used for managing user login and model inference. Exact details are still subject to change.

## Stack
- Django

## Getting started

1. Install dependencies:
   - cd backend
   - python -m venv .venv
   - Linux: source .venv/bin/activate   Windows: .venv\Scripts\activate
   - pip install -r ./requirements.txt

2. Run the dev server:
   - python manage.py runserver 0.0.0.0:8000

3. Build for production:
   - Make sure settings.py has been hardened before this step as dev configurations are the default
   - python manage.py collectstatic --noinput
   - python manage.py migrate
   - python -m gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3 --daemon

## Notes
- The production webserver is designed to be run behind a reserse proxy such as Nginx.
