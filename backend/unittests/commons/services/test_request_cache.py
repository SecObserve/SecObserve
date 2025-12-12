from unittest import mock

# Import the module under test
import application.commons.services.request_cache as rc
from unittests.base_test_case import BaseTestCase


class DummyRequest:
    """A very small stand‑in for Django's HttpRequest object."""

    pass


class RequestCacheMiddlewareTest(BaseTestCase):
    def test_process_request_attaches_cache(self):
        """Middleware should add a RequestCache instance to the request."""
        request = DummyRequest()
        middleware = rc.RequestCacheMiddleware(get_response=lambda r: None)

        # process_request is called by Django during the request cycle
        middleware.process_request(request)

        self.assertTrue(hasattr(request, "cache"))
        self.assertIsInstance(request.cache, rc.RequestCache)


class CacheForRequestDecoratorTest(BaseTestCase):
    def setUp(self):
        super().setUp()
        # Reset any global state between tests
        rc.cache_args_kwargs_marker = object()

    def _mock_get_current_request(self, cache_instance):
        """Helper to patch get_current_request to return an object with a cache attribute."""
        mock_req = DummyRequest()
        mock_req.cache = cache_instance
        return mock.patch("application.commons.services.request_cache.get_current_request", return_value=mock_req)

    def test_decorator_caches_result_within_request(self):
        """The decorator should cache results only for the current request."""
        counter = {"calls": 0}

        @rc.cache_for_request
        def expensive(arg):
            counter["calls"] += 1
            return f"result-{arg}"

        # Use a RequestCache instance
        cache = rc.RequestCache()
        with self._mock_get_current_request(cache):
            # First call with arg=1 -> should compute
            self.assertEqual(expensive(1), "result-1")
            self.assertEqual(counter["calls"], 1)

            # Second call with same arg -> should hit cache
            self.assertEqual(expensive(1), "result-1")
            self.assertEqual(counter["calls"], 1)

            # Call with different arg -> compute again
            self.assertEqual(expensive(2), "result-2")
            self.assertEqual(counter["calls"], 2)

            # Ensure the cache stores attributes correctly
            # self.assertTrue(hasattr(cache, "_cache_calculate_key(1,)"))
            # self.assertTrue(hasattr(cache, "_cache_calculate_key(2,)"))

    def test_decorator_falls_back_when_no_cache(self):
        """If no request cache is available, the function should execute normally."""
        counter = {"calls": 0}

        @rc.cache_for_request
        def expensive(arg):
            counter["calls"] += 1
            return f"result-{arg}"

        # Patch get_current_request to return None
        with mock.patch("application.commons.services.request_cache.get_current_request", return_value=None):
            self.assertEqual(expensive(1), "result-1")
            self.assertEqual(counter["calls"], 1)
            self.assertEqual(expensive(1), "result-1")
            self.assertEqual(counter["calls"], 2)  # no caching

    def test_cache_key_generation_is_consistent(self):
        """Cache key calculation should be order‑insensitive for kwargs."""
        key1 = rc._cache_calculate_key(1, 2, foo="bar", baz=3)
        key2 = rc._cache_calculate_key(1, 2, baz=3, foo="bar")
        key3 = rc._cache_calculate_key(1, 2, foo="bar", baz=4)
        self.assertEqual(key1, key2)
        self.assertNotEqual(key1, key3)

    def test_cache_key_contains_args_and_kwargs(self):
        """The marker object should separate positional args from keyword args."""
        key_both = rc._cache_calculate_key(1, 2, foo="bar")

        # Args and kwargs should be present in the key string
        marker_repr = str(rc.cache_args_kwargs_marker)
        self.assertIn(marker_repr, key_both)
