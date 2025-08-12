"""
Shared HTTP client with in-memory caching, exponential backoff, and centralized
rate limiting for external data providers (Alpha Vantage, FRED, etc.).

Design goals (Phase 0):
- Reduce duplicate request logic scattered across tools
- Handle provider rate limits gracefully with backoff and cache fallbacks
- Provide a small API that tools can call for JSON GET requests
"""

from __future__ import annotations

import json
import logging
import random
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from threading import Lock
from typing import Any, Callable, Dict, Optional, Tuple

import requests

from backend.config.settings import get_settings


logger = logging.getLogger(__name__)


# -----------------------------
# Simple in-memory TTL cache
# -----------------------------

class _TTLCache:
    def __init__(self) -> None:
        self._store: Dict[Tuple[str, Tuple[Tuple[str, Any], ...]], Tuple[float, Any]] = {}
        self._lock = Lock()

    @staticmethod
    def _make_key(url: str, params: Optional[Dict[str, Any]]) -> Tuple[str, Tuple[Tuple[str, Any], ...]]:
        normalized = tuple(sorted((params or {}).items()))
        return (url, normalized)

    def get(self, url: str, params: Optional[Dict[str, Any]]) -> Optional[Any]:
        key = self._make_key(url, params)
        now = time.time()
        with self._lock:
            item = self._store.get(key)
            if not item:
                return None
            expires_at, value = item
            if now <= expires_at:
                return value
            # Expired: keep for potential stale return but do not remove yet
            return None

    def get_stale(self, url: str, params: Optional[Dict[str, Any]]) -> Optional[Any]:
        key = self._make_key(url, params)
        with self._lock:
            item = self._store.get(key)
            if not item:
                return None
            return item[1]

    def set(self, url: str, params: Optional[Dict[str, Any]], value: Any, ttl_seconds: int) -> None:
        key = self._make_key(url, params)
        expires_at = time.time() + max(1, int(ttl_seconds))
        with self._lock:
            self._store[key] = (expires_at, value)


_cache = _TTLCache()


# -----------------------------
# Simple token-bucket rate limiter per key
# -----------------------------

@dataclass
class _RateLimitConfig:
    limit_per_window: int
    window_seconds: int = 60


class _RateLimiter:
    def __init__(self) -> None:
        self._buckets: Dict[str, deque] = {}
        self._configs: Dict[str, _RateLimitConfig] = {}
        self._lock = Lock()

    def configure(self, key: str, limit_per_minute: int) -> None:
        with self._lock:
            self._configs[key] = _RateLimitConfig(limit_per_minute, 60)
            if key not in self._buckets:
                self._buckets[key] = deque()

    def _purge_old(self, key: str, now: float) -> None:
        bucket = self._buckets.setdefault(key, deque())
        window = self._configs.get(key, _RateLimitConfig(60, 60)).window_seconds
        while bucket and now - bucket[0] > window:
            bucket.popleft()

    def predicted_delay(self, key: str) -> float:
        """Return seconds to wait before next allowed call, or 0 if allowed now."""
        now = time.time()
        with self._lock:
            config = self._configs.get(key)
            if not config:
                # default to generous if unconfigured
                self._configs[key] = _RateLimitConfig(60, 60)
                config = self._configs[key]
            bucket = self._buckets.setdefault(key, deque())
            self._purge_old(key, now)
            if len(bucket) < config.limit_per_window:
                return 0.0
            # next available time is when the oldest drops out of window
            oldest = bucket[0]
            return max(0.0, (oldest + config.window_seconds) - now)

    def record(self, key: str) -> None:
        now = time.time()
        with self._lock:
            bucket = self._buckets.setdefault(key, deque())
            bucket.append(now)
            self._purge_old(key, now)


_rate_limiter = _RateLimiter()


# -----------------------------
# Provider-specific helpers
# -----------------------------

def _is_alphavantage_rate_limited(data: Any, status_code: int) -> bool:
    if status_code == 429:
        return True
    if isinstance(data, dict):
        if data.get("Note"):
            return True
        if data.get("Information"):
            # Often indicates limits or endpoint policy info
            return True
        if data.get("Error Message"):
            return True
    return False


def _is_fred_rate_limited(data: Any, status_code: int) -> bool:
    if status_code == 429:
        return True
    if isinstance(data, dict) and ("error_code" in data):
        return True
    return False


def http_get_json(
    *,
    url: str,
    params: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    cache_ttl_seconds: Optional[int] = None,
    rate_limit_key: Optional[str] = None,
    limit_per_minute: Optional[int] = None,
    timeout_seconds: int = 12,
    max_retries: int = 3,
    backoff_base_seconds: float = 1.0,
    backoff_max_seconds: float = 8.0,
    is_rate_limited_response: Optional[Callable[[Any, int], bool]] = None,
) -> Optional[Dict[str, Any]]:
    """GET JSON with TTL cache, token-bucket rate limiting, and exponential backoff.

    Returns parsed JSON dict on success, or None on failure/limit.
    """
    settings = get_settings()
    ttl = cache_ttl_seconds if cache_ttl_seconds is not None else settings.cache_ttl
    headers = headers or {}
    params = params or {}

    # Configure limiter if requested
    if rate_limit_key and limit_per_minute:
        _rate_limiter.configure(rate_limit_key, limit_per_minute)

    # Serve from fresh cache
    try:
        cached = _cache.get(url, params)
        if cached is not None:
            return cached
    except Exception:
        # Cache must never break data path
        pass

    # If limiter predicts delay, try stale cache
    if rate_limit_key and limit_per_minute:
        delay = _rate_limiter.predicted_delay(rate_limit_key)
        if delay > 0.0:
            stale = _cache.get_stale(url, params)
            if stale is not None:
                logger.debug(
                    f"Rate limited predicted for {rate_limit_key}, returning stale cache for {url}"
                )
                return stale
            # else fall through and attempt anyway; server may still accept

    # Attempt with retries and backoff
    attempt = 0
    while attempt <= max_retries:
        attempt += 1
        try:
            # Record pre-call for limiter (soft control; we want to avoid violating quotas)
            if rate_limit_key and limit_per_minute:
                predicted = _rate_limiter.predicted_delay(rate_limit_key)
                if predicted > 0:
                    # Sleep a bit but cap to avoid long blocking; prefer < 1.5s
                    time.sleep(min(1.5, predicted))

            resp = requests.get(url, params=params, headers=headers, timeout=timeout_seconds)
            status = resp.status_code
            data: Any
            try:
                data = resp.json()
            except Exception:
                data = None

            limited = False
            if is_rate_limited_response:
                limited = is_rate_limited_response(data, status)

            if status == 200 and data and not limited:
                # Success path
                if rate_limit_key and limit_per_minute:
                    _rate_limiter.record(rate_limit_key)
                try:
                    _cache.set(url, params, data, ttl)
                except Exception:
                    pass
                return data

            # Detect retryable conditions
            retryable = status in (408, 409, 425, 429, 500, 502, 503, 504) or limited
            if retryable and attempt <= max_retries:
                backoff = min(backoff_max_seconds, backoff_base_seconds * (2 ** (attempt - 1)))
                jitter = random.uniform(0, 0.3)
                sleep_s = backoff + jitter
                logger.warning(
                    f"Retryable error for {url} (status={status}, limited={limited}), attempt={attempt}/{max_retries}, sleeping {sleep_s:.2f}s"
                )
                time.sleep(sleep_s)
                continue

            # Non-retryable or out of retries
            break

        except requests.RequestException as e:
            if attempt <= max_retries:
                backoff = min(backoff_max_seconds, backoff_base_seconds * (2 ** (attempt - 1)))
                jitter = random.uniform(0, 0.3)
                sleep_s = backoff + jitter
                logger.warning(
                    f"Request exception for {url}: {e!s}; attempt={attempt}/{max_retries}; sleeping {sleep_s:.2f}s"
                )
                time.sleep(sleep_s)
                continue
            break

    # Fall back to stale cache if available
    stale = _cache.get_stale(url, params)
    if stale is not None:
        logger.debug(f"Returning stale cache for {url} after failures")
        return stale

    return None


def alpha_vantage_request(params: Dict[str, Any], cache_ttl_seconds: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """Alpha Vantage JSON GET with shared client and AV-specific limit detection.

    Automatically injects API key and rate limits using environment configuration.
    """
    settings = get_settings()
    api_key = settings.alpha_vantage_api_key
    if not api_key:
        return None
    url = "https://www.alphavantage.co/query"
    req_params = {**params, "apikey": api_key}
    limit_per_minute = getattr(settings, "alpha_vantage_per_minute", 5)
    return http_get_json(
        url=url,
        params=req_params,
        cache_ttl_seconds=cache_ttl_seconds,
        rate_limit_key="alpha_vantage",
        limit_per_minute=limit_per_minute,
        is_rate_limited_response=_is_alphavantage_rate_limited,
    )


def fred_request(params: Dict[str, Any], cache_ttl_seconds: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """FRED JSON GET with shared client and FRED-specific limit detection."""
    settings = get_settings()
    api_key = settings.fred_api_key
    if not api_key:
        return None
    url = "https://api.stlouisfed.org/fred/series/observations"
    req_params = {**params, "api_key": api_key, "file_type": "json"}
    limit_per_minute = getattr(settings, "fred_per_minute", 60)
    return http_get_json(
        url=url,
        params=req_params,
        cache_ttl_seconds=cache_ttl_seconds,
        rate_limit_key="fred",
        limit_per_minute=limit_per_minute,
        is_rate_limited_response=_is_fred_rate_limited,
    )


