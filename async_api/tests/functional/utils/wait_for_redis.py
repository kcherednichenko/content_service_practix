import os
import time

from redis import Redis

from dotenv import load_dotenv


if __name__ == '__main__':
    load_dotenv()
    redis_client = Redis(host=os.environ.get('REDIS_HOST'), port=os.environ.get('REDIS_PORT'))
    while True:
        if redis_client.ping():
            break
        time.sleep(1)
