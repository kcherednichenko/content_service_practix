from redis import Redis, RedisError

from tests.functional.settings import test_settings
from tests.functional.utils.backoff import backoff


@backoff()
def wait_for_redis(redis_client: Redis) -> bool:
    try:
        return redis_client.ping()
    except RedisError:
        return False


if __name__ == '__main__':
    redis_client = Redis(host=test_settings.redis_host, port=test_settings.redis_port)
    wait_for_redis(redis_client)
