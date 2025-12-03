#!/bin/bash

# Assuming venv is already activated in the terminal where this script is run

pkill -f "gunicorn config.wsgi" || true
pkill caddy || true
sleep 1

cd ../backend/

# Start Gunicorn in background (Django server)
python -m gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 1 --daemon

cd ../reverse_proxy/

caddy start --config ./Caddyfile

echo "Services started:"
echo "Gunicorn (Django) running on http://0.0.0.0:8000"
echo "Caddy running on http://localhost:80"
echo "Reach Caddy through worshipflow.zachmcgill.com"
