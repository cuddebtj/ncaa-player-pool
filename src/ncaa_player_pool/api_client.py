"""HTTP API client with retry logic and error handling.

This module provides an async HTTP client built on httpx with automatic retry
logic using tenacity. It handles common API issues like rate limiting, timeouts,
and network errors.

Example:
    Basic usage with async context manager::

        from ncaa_player_pool.api_client import APIClient
        from ncaa_player_pool.config import get_config

        config = get_config()

        async with APIClient(config) as client:
            data = await client.get("https://api.example.com/data")
            print(data)

    Batch fetching multiple URLs::

        async with APIClient(config) as client:
            urls = ["https://api.example.com/1", "https://api.example.com/2"]
            results = await client.batch_get(urls, max_concurrent=3)

Attributes:
    logger: Module-level logger instance for API operations.

Classes:
    APIError: Base exception for all API-related errors.
    RateLimitError: Raised when API rate limit (429) is exceeded.
    NotFoundError: Raised when resource is not found (404).
    APIClient: Async HTTP client with retry logic.
"""

import asyncio
import json
from pathlib import Path
from typing import Any

import httpx
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from .config import Config
from .logger import get_logger

logger = get_logger(__name__)


class APIError(Exception):
    """Base exception for API-related errors.

    All API exceptions inherit from this class, making it easy to catch
    any API-related error with a single except clause.

    Example:
        Catching any API error::

            try:
                data = await client.get(url)
            except APIError as e:
                print(f"API request failed: {e}")
    """

    pass


class RateLimitError(APIError):
    """Raised when API rate limit (HTTP 429) is exceeded.

    This exception triggers automatic retry with exponential backoff
    when caught by the retry decorator.

    Attributes:
        Inherits all attributes from APIError.
    """

    pass


class NotFoundError(APIError):
    """Raised when the requested resource is not found (HTTP 404).

    Unlike other API errors, 404 errors are not retried since the
    resource genuinely does not exist.

    Attributes:
        Inherits all attributes from APIError.
    """

    pass


class APIClient:
    """Async HTTP client with retry logic and comprehensive error handling.

    This client wraps httpx.AsyncClient and adds automatic retry logic
    for transient errors, rate limiting support, and response caching
    to files.

    Attributes:
        config: Application configuration instance.
        client: The underlying httpx.AsyncClient (None until context entered).

    Example:
        Using as an async context manager::

            async with APIClient(config) as client:
                # Make requests
                data = await client.get("https://api.example.com/resource")

                # Save response to file
                data = await client.get(url, save_to=Path("response.json"))

                # Batch fetch with concurrency control
                results = await client.batch_get(urls, max_concurrent=5)
    """

    def __init__(self, config: Config):
        """Initialize the API client.

        Args:
            config: Application configuration containing timeout settings,
                rate limit delay, and other HTTP client options.
        """
        self.config = config
        self.client: httpx.AsyncClient | None = None
        self._rate_limit_delay = config.rate_limit_delay

    async def __aenter__(self) -> "APIClient":
        """Enter async context manager and initialize HTTP client.

        Creates the underlying httpx.AsyncClient with configured timeout
        and default headers for JSON API requests.

        Returns:
            Self reference for use in async with statements.
        """
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.config.request_timeout),
            headers={"accept": "application/json"},
            follow_redirects=True,
        )
        logger.info("API client initialized")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context manager and close HTTP client.

        Properly closes the httpx.AsyncClient to release resources.

        Args:
            exc_type: Exception type if an error occurred, None otherwise.
            exc_val: Exception value if an error occurred, None otherwise.
            exc_tb: Exception traceback if an error occurred, None otherwise.
        """
        if self.client:
            await self.client.aclose()
            logger.info("API client closed")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError, RateLimitError)),
        before_sleep=before_sleep_log(logger, "WARNING"),
    )
    async def get(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        save_to: Path | None = None,
    ) -> dict[str, Any]:
        """Make a GET request with automatic retry on transient errors.

        Performs an HTTP GET request with automatic retry logic for timeouts,
        network errors, and rate limiting (HTTP 429). Uses exponential backoff
        between retries.

        Args:
            url: The URL to request. Must be a fully qualified URL.
            params: Optional dictionary of query parameters to append to the URL.
            save_to: Optional file path to save the JSON response. Parent
                directories are created automatically if they don't exist.

        Returns:
            The parsed JSON response as a Python dictionary.

        Raises:
            APIError: If the request fails after all retry attempts, or if
                the server returns an error status code (5xx).
            NotFoundError: If the resource is not found (HTTP 404). This error
                is not retried.
            RateLimitError: If rate limited (HTTP 429). This triggers retry
                with exponential backoff.

        Example:
            Basic GET request::

                data = await client.get("https://api.example.com/users")

            With query parameters::

                data = await client.get(
                    "https://api.example.com/search",
                    params={"q": "tournament", "year": 2026}
                )

            Save response to file::

                data = await client.get(
                    "https://api.example.com/data",
                    save_to=Path("data/response.json")
                )
        """
        if not self.client:
            raise APIError("Client not initialized. Use 'async with' context manager.")

        logger.info(f"GET {url}")
        if params:
            logger.debug(f"Query params: {params}")

        try:
            response = await self.client.get(url, params=params)

            # Handle specific status codes
            if response.status_code == 404:
                logger.error(f"Resource not found: {url}")
                raise NotFoundError(f"Resource not found: {url}")

            if response.status_code == 429:
                logger.warning(f"Rate limited: {url}")
                raise RateLimitError("Rate limited. Retry after delay.")

            if response.status_code >= 500:
                logger.error(f"Server error {response.status_code}: {url}")
                raise APIError(f"Server error {response.status_code}: {url}")

            response.raise_for_status()

            data = response.json()
            logger.info(f"Successfully fetched {url} (status: {response.status_code})")

            # Save to file if requested
            if save_to:
                save_to.parent.mkdir(parents=True, exist_ok=True)
                with open(save_to, "w") as f:
                    json.dump(data, f, indent=2)
                logger.info(f"Saved response to {save_to}")

            # Rate limiting - sleep between requests
            if self._rate_limit_delay > 0:
                logger.debug(f"Rate limit delay: {self._rate_limit_delay}s")
                await asyncio.sleep(self._rate_limit_delay)

            return data

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code}: {url}")
            raise APIError(f"HTTP error {e.response.status_code}: {url}") from e

        except httpx.TimeoutException:
            logger.warning(f"Request timeout: {url}")
            raise

        except httpx.NetworkError:
            logger.warning(f"Network error: {url}")
            raise

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response from {url}: {e}")
            raise APIError(f"Invalid JSON response from {url}") from e

        except Exception as e:
            logger.exception(f"Unexpected error fetching {url}: {e}")
            raise APIError(f"Unexpected error: {e}") from e

    async def get_json_file(self, url: str, file_path: Path) -> dict[str, Any]:
        """Fetch JSON from URL with local file caching.

        If the file already exists at the specified path, loads and returns
        the cached data. Otherwise, fetches from the URL and saves to the file.

        This is useful for avoiding redundant API calls when data doesn't
        change frequently.

        Args:
            url: The URL to fetch if the file doesn't exist.
            file_path: Path to the cache file. Will be created if it doesn't
                exist, loaded if it does.

        Returns:
            The JSON data as a Python dictionary, either from cache or
            freshly fetched.

        Example:
            Cache tournament data locally::

                data = await client.get_json_file(
                    "https://api.espn.com/tournament/123",
                    Path("cache/tournament_123.json")
                )
        """
        if file_path.exists():
            logger.info(f"Loading cached data from {file_path}")
            with open(file_path) as f:
                return json.load(f)

        logger.info(f"Fetching fresh data from {url}")
        return await self.get(url, save_to=file_path)

    async def batch_get(
        self,
        urls: list[str],
        save_dir: Path | None = None,
        max_concurrent: int = 5,
    ) -> list[dict[str, Any]]:
        """Fetch multiple URLs concurrently with controlled parallelism.

        Uses asyncio.Semaphore to limit concurrent requests, preventing
        overwhelming the target API. Failed requests are logged but don't
        stop other requests from completing.

        Args:
            urls: List of URLs to fetch. Each URL is fetched independently.
            save_dir: Optional directory to save responses. If provided,
                responses are saved as ``response_NNNN.json`` files.
            max_concurrent: Maximum number of concurrent requests. Lower
                values are gentler on the API but slower. Default is 5.

        Returns:
            List of successfully fetched JSON responses. Failed requests
            are excluded from the results but logged as errors.

        Example:
            Fetch multiple team rosters::

                team_urls = [
                    f"https://api.espn.com/teams/{tid}"
                    for tid in ["123", "456", "789"]
                ]
                results = await client.batch_get(
                    team_urls,
                    save_dir=Path("data/teams"),
                    max_concurrent=3
                )
                print(f"Successfully fetched {len(results)} teams")
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def fetch_with_semaphore(url: str, index: int) -> dict[str, Any]:
            async with semaphore:
                save_to = None
                if save_dir:
                    save_dir.mkdir(parents=True, exist_ok=True)
                    # Use index as filename for batch operations
                    save_to = save_dir / f"response_{index:04d}.json"
                return await self.get(url, save_to=save_to)

        logger.info(f"Batch fetching {len(urls)} URLs (max {max_concurrent} concurrent)")
        tasks = [fetch_with_semaphore(url, i) for i, url in enumerate(urls)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions and log them
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Failed to fetch URL {i}: {result}")
            else:
                valid_results.append(result)

        logger.info(f"Successfully fetched {len(valid_results)}/{len(urls)} URLs")
        return valid_results
