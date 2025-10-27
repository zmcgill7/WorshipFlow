#!/bin/bash

cd '/mnt/c/Users/zackm/OneDrive/Documents/University/PFW/Fall 2025/Applications of Deep Learning/WorshipFlow/'

# Start Gunicorn in background
cd backend/
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3 &
sleep 2

cd ../reverse_proxy/
# caddy run --config ./Caddyfile
sudo caddy run --config ./Caddyfile