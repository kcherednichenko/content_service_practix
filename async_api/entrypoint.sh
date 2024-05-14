#!/bin/sh

gunicorn main:app --chdir src --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

exec "$@"