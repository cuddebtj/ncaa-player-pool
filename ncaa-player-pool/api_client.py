"""
HTTP API client using httpx with retry logic and comprehensive error handling.
"""

import asyncio
from typing import Any, Dict, Optional
from pathlib import Path
import json

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

from config import Config
from logger import get_logger

logger = get_logger(__name__)


class APIError(Exception):
    """Base exception for API errors."""

    pass


class RateLimitError(APIError):
    """Raised when API rate limit is exceeded."""

    pass


class NotFoundError(APIError):
    """Raised when resource is not found (404)."""

    pass


class APIClient:
    """
    HTTP client for making API requests with retry logic and error handling.
    """

    def __init__(self, config: Config):
        """
        Initialize the API client.

        Args:
            config: Application configuration
        """
        self.config = config
        self.client: Optional[httpx.AsyncClient] = None
        self._rate_limit_delay = config.rate_limit_delay

    async def __aenter__(self):
        """Async context manager entry."""
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.config.request_timeout),
            headers={"accept": "application/json"},
            follow_redirects=True,
        )
        logger.info("API client initialized")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
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
        params: Optional[Dict[str, Any]] = None,
        save_to: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """
        Make a GET request with retry logic.

        Args:
            url: URL to request
            params: Optional query parameters
            save_to: Optional path to save response JSON

        Returns:
            Response JSON as dictionary

        Raises:
            APIError: If request fails after retries
            NotFoundError: If resource not found (404)
            RateLimitError: If rate limited (429)
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
                raise RateLimitError(f"Rate limited. Retry after delay.")

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

        except httpx.TimeoutException as e:
            logger.warning(f"Request timeout: {url}")
            raise

        except httpx.NetworkError as e:
            logger.warning(f"Network error: {url}")
            raise

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response from {url}: {e}")
            raise APIError(f"Invalid JSON response from {url}") from e

        except Exception as e:
            logger.exception(f"Unexpected error fetching {url}: {e}")
            raise APIError(f"Unexpected error: {e}") from e

    async def get_json_file(self, url: str, file_path: Path) -> Dict[str, Any]:
        """
        Fetch JSON from URL and save to file, or load from file if it exists.

        Args:
            url: URL to fetch
            file_path: Path to save/load JSON file

        Returns:
            JSON data as dictionary
        """
        if file_path.exists():
            logger.info(f"Loading cached data from {file_path}")
            with open(file_path, "r") as f:
                return json.load(f)

        logger.info(f"Fetching fresh data from {url}")
        return await self.get(url, save_to=file_path)

    async def batch_get(
        self,
        urls: list[str],
        save_dir: Optional[Path] = None,
        max_concurrent: int = 5,
    ) -> list[Dict[str, Any]]:
        """
        Fetch multiple URLs concurrently with rate limiting.

        Args:
            urls: List of URLs to fetch
            save_dir: Optional directory to save responses (uses URL hash as filename)
            max_concurrent: Maximum concurrent requests

        Returns:
            List of response JSONs
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def fetch_with_semaphore(url: str, index: int) -> Dict[str, Any]:
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
