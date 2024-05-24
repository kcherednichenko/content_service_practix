from functools import wraps
import time
from typing import Any, Callable


class ServiceUnavailable(Exception):
    pass


def backoff(start_sleep_time: float = 0.1,
            factor: int = 2,
            border_sleep_time: int = 10,
            attempts_threshold: int = 50) -> Callable[..., Any]:
    def func_wrapper(ready: Callable[..., bool]) -> Callable[..., Any]:
        @wraps(ready)
        def inner(*args: Any, **kwargs: Any) -> Any:
            n = 1
            while True:
                if ready(*args, **kwargs):
                    break
                if n > attempts_threshold:
                    raise ServiceUnavailable
                time_to_sleep = start_sleep_time * (factor ** n)
                time.sleep(time_to_sleep if time_to_sleep < border_sleep_time else border_sleep_time)
                n += 1
        return inner
    return func_wrapper
