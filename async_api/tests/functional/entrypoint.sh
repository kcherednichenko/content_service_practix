#!/bin/sh

cd /home/app
python -m pytest

exec "$@"
