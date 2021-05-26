import threading
from functools import wraps

from celery.utils.log import get_task_logger
logger = get_task_logger(__name__)

_kwd_mark = object()
_data_lock = threading.Lock()


def RDD_builder(f):
    """
    Decorator that caches the function's return value, so cached RDDs can be shared between subsequent tasks.
    """

    @wraps(f)
    def wrapper(self, *args, **kwargs):
        with _data_lock:
            try:
                self._cache
            except AttributeError:
                self._cache = {}

            # function call hash adapted from http://stackoverflow.com/a/10220908/1236542
            key = (f,) + args + (_kwd_mark,) + tuple(sorted(kwargs.items()))
            if key in self._cache:
                return self._cache[key]
            else:
                from pyspark.rdd import RDD

                result = f(self, *args, **kwargs)
                self._cache[key] = result

                if isinstance(result, RDD):
                    st = result.getStorageLevel()
                    if not st.useDisk and not st.useMemory and not st.useOffHeap:
                        raise ValueError('An RDD returned by RDD_builder should be persisted with .cache() or .persist().')

                return result

    return wrapper

