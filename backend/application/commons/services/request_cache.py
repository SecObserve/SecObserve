from collections import OrderedDict
from threading import Lock
from typing import Any, Callable, Optional, TypeVar

from django.core.cache.backends.base import BaseCache
from django.core.cache.backends.locmem import LocMemCache
from django.utils.deprecation import MiddlewareMixin
from rest_framework.request import Request

from application.commons.services.global_request import get_current_request

T = TypeVar("T")

# Attribution 1: This code has been taken from https://github.com/anexia-it/django-request-cache, which has
# been published under the MIT License. Since this project hasn't been updated for several years,
# the code has been copied to SecObserve, to be able to fix issues ourselves.

# Attribution 2: RequestCache and RequestCacheMiddleware are from a source code snippet on StackOverflow
# https://stackoverflow.com/questions/3151469/per-request-cache-in-django/37015573#37015573
# created by coredumperror https://stackoverflow.com/users/464318/coredumperror
# Original Question was posted by https://stackoverflow.com/users/7679/chase-seibert
# at https://stackoverflow.com/questions/3151469/per-request-cache-in-django
# copied on 2017-Dec-20


class RequestCache(LocMemCache):
    """
    RequestCache is a customized LocMemCache which stores its data cache as an instance attribute, rather than
    a global. It's designed to live only as long as the request object that RequestCacheMiddleware attaches it to.
    """

    def __init__(self) -> None:  # pylint: disable=super-init-not-called)
        # We explicitly do not call super() here, because while we want BaseCache.__init__() to run, we *don't*
        # want LocMemCache.__init__() to run, because that would store our caches in its globals.
        BaseCache.__init__(self, params={})  # pylint: disable=non-parent-init-called

        self._cache: dict[Any, Any] = OrderedDict()
        self._expire_info: dict[Any, Any] = {}
        self._lock = Lock()


class RequestCacheMiddleware(MiddlewareMixin):
    """
    For every request, a fresh cache instance is stored in ``request.cache``.
    The cache instance lives only as long as request does.
    """

    def process_request(self, request: Request) -> None:
        setattr(request, "cache", RequestCache())
        # request.cache = RequestCache()


def cache_for_request(fn: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator that allows to cache a function call with parameters and its result only for the current request
    The result is stored in the memory of the current process
    As soon as the request is destroyed, the cache is destroyed
    :param fn:
    :return:
    """

    def wrapper(*args: Any, **kwargs: Any) -> Any:
        cache = _get_request_cache()

        if not cache:
            # no cache found -> directly execute function without caching
            return fn(*args, **kwargs)

        # cache found -> check if a result is already available for this function call
        key = _cache_calculate_key(fn.__name__, *args, **kwargs)

        try:
            result = getattr(cache, key)
        except AttributeError:
            # no result available -> execute function
            result = fn(*args, **kwargs)
            setattr(cache, key, result)

        return result

    return wrapper


def _get_request_cache() -> Optional[RequestCache]:
    """
    Return the current requests cache
    :return:
    """
    return getattr(get_current_request(), "cache", None)


cache_args_kwargs_marker = object()  # marker for separating args from kwargs (needs to be global)


def _cache_calculate_key(*args: Any, **kwargs: Any) -> str:
    """
    Calculate the cache key of a function call with args and kwargs
    Taken from lru_cache
    :param args:
    :param kwargs:
    :return: the calculated key for the function call
    :rtype: basestring
    """
    # combine args with kwargs, separated by the cache_args_kwargs_marker
    key = (*args, cache_args_kwargs_marker, *tuple(sorted(kwargs.items())))
    # return as a string
    return str(key)
