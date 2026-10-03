import asyncio
import logging
from functools import wraps
from typing import Callable, Any, TypeVar, cast
from tenacity import retry, wait_exponential, stop_after_attempt, before_sleep_log

T = TypeVar("T", bound=Callable[..., Any])

# Set up a logger for tenacity to print warnings when it retries
logger = logging.getLogger("RateLimiter")
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(ch)

def is_rate_limit_error(exception: BaseException) -> bool:
    """Check if the exception is a rate limit error (429)"""
    # Langchain wraps Groq errors. We check string representation just to be safe.
    err_str = str(exception).lower()
    return "429" in err_str or "too many requests" in err_str or "rate limit" in err_str

def custom_retry_if(retry_state):
    if retry_state.outcome.failed:
        exc = retry_state.outcome.exception()
        if is_rate_limit_error(exc):
            return True
    return False

# Base retry decorator configuration
base_retry_decorator = retry(
    wait=wait_exponential(multiplier=2, min=5, max=60), # Wait 5s, 10s, 20s, 40s, 60s...
    stop=stop_after_attempt(10), # Max 10 attempts
    before_sleep=before_sleep_log(logger, logging.WARNING)
)
base_retry_decorator.retry = custom_retry_if

def with_rate_limit_retry(func: T) -> T:
    """
    A decorator that applies exponential backoff if a Groq rate limit error occurs.
    """
    if asyncio.iscoroutinefunction(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await base_retry_decorator(func)(*args, **kwargs)
        return cast(T, async_wrapper)
    else:
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            return base_retry_decorator(func)(*args, **kwargs)
        return cast(T, sync_wrapper)

def with_rate_limit_retry_async_gen(func: T) -> T:
    """
    Specific decorator for async generators (astream).
    """
    @wraps(func)
    async def async_gen_wrapper(*args, **kwargs):
        # We wrap the creation and the FIRST yield of the generator, 
        # as rate limits happen upon initiating the request.
        
        @base_retry_decorator
        async def get_first_chunk():
            gen = func(*args, **kwargs)
            try:
                first = await gen.__anext__()
                return gen, first, False
            except StopAsyncIteration:
                return gen, None, True

        gen, first_chunk, is_empty = await get_first_chunk()
        
        if is_empty:
            return
            
        yield first_chunk
        
        # Stream the rest normally
        async for chunk in gen:
            yield chunk

    return cast(T, async_gen_wrapper)
