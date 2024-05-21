#!/bin/sh

cd /home/app
python /home/app/tests/functional/utils/wait_for_es.py && python /home/app/tests/functional/utils/wait_for_redis.py && python -m pytest

exec "$@"
