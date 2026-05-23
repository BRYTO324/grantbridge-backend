#!/usr/bin/env bash
# Render build script — runs before the web service starts
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate
