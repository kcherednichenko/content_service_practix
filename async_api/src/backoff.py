import logging
from typing import Any, Awaitable, Tuple, Callable
from functools import wraps
import asyncio

logger = logging.getLogger(__name__)


def backoff(start_sleep_time: float = 0.1,
            factor: int = 2,
            border_sleep_time: int = 2,
            attempts_threshold: int = 3,
            exceptions: Tuple[Exception, ...] = ()) -> Callable[..., Any]:
    def func_wrapper(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        @wraps(func)
        async def inner(*args: Any, **kwargs: Any) -> Any:
            n = 1
            while True:
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    logger.error(f"Exception has occurred: {e}")
                    if n > attempts_threshold:
                        raise
                    time_to_sleep = start_sleep_time * (factor ** n)
                    await asyncio.sleep(time_to_sleep if time_to_sleep < border_sleep_time else border_sleep_time)
                    n += 1
        return inner
    return func_wrapper
