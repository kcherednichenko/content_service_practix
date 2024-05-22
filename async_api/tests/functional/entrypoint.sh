#!/bin/sh

python ./utils/wait_for_es.py
python ./utils/wait_for_redis.py
pytest

exec "$@"
