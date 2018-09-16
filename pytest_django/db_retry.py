"""Functions to aid in retrying failed attempts to setup the database."""

import time
from functools import wraps


def wrap_creation_for_db_retry(setup_db_func, max_retries=5, timeout_sec=1):
    from django.db import OperationalError

    @wraps(setup_db_func)
    def retry_it(*args, **kwargs):
        for i in range(max_retries):
            try:
                return setup_db_func(*args, **kwargs)
            except OperationalError:
                if i == max_retries:
                    raise
                time.sleep(timeout_sec)

    return retry_it
