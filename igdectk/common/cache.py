# -*- coding: utf-8; -*-
#
# @file cache.py
# @brief Named cache for view, adding the possibility to invalidate them.
# @author Frédéric SCHERMA (INRA UMR1095)
# @date 2017-06-06
# @copyright Copyright (c) 2017 INRA
# @license MIT (see LICENSE file)
# @details

from django.core.cache import cache


def named_cache_page(cache_timeout):
    """
    Decorator for views that tries getting the page from the cache and
    populates the cache if the page isn't in the cache yet.

    The cache is keyed by view name and arguments.
    """
    def wrapper(func):
        def foo(*args, **kwargs):
            key = func.__name__
            if kwargs:
                key += ':' + ':'.join([kwargs[key] for key in kwargs])

            response = cache.get(key)
            if not response:
                response = func(*args, **kwargs)
                cache.set(key, response, cache_timeout)
            return response
        return foo
    return wrapper


def invalidate_cache(view_func_name):
    cache.set(view_func_name, None, 0)
