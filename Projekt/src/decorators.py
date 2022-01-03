from concurrent.futures import ThreadPoolExecutor
from functools import wraps


def thread_request(f, executor=None):
    """
    Unblocking function realized on thread
    Based on: https://stackoverflow.com/questions/6893968/how-to-get-the-return-value-from-a-thread-in-python
    """
    @wraps(f)
    def wrap(*args, **kwargs):
        return (executor or ThreadPoolExecutor()).submit(f, *args, **kwargs)

    return wrap
