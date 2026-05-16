"""WebClaw web search + content extraction + crawl — Hermes plugin.

Subclasses :class:`agent.web_search_provider.WebSearchProvider`. Three
capabilities advertised:

- ``supports_search()``  -> True  (WebClaw ``/v1/search``)
- ``supports_extract()`` -> True  (WebClaw ``/v1/scrape``)
- ``supports_crawl()``   -> True  (WebClaw ``/v1/crawl``)

All three are sync (httpx.post). The dispatcher in
:func:`tools.web_tools.web_crawl_tool` runs sync providers in a thread
when appropriate. ``extract()`` is async with per-URL threading for
timeout support.

Config keys this provider responds to::

    web:
      search_backend: "webclaw"
      extract_backend: "webclaw"
      crawl_backend: "webclaw"
      backend: "webclaw"            # shared fallback for all three

Env vars::

    WEBCLAW_API_KEY=wc_...          # required — https://webclaw.io
    WEBCLAW_BASE_URL=...            # optional — default: https://api.webclaw.io
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, Dict, List

from agent.web_search_provider import WebSearchProvider
from tools.website_policy import check_website_access

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "https://api.webclaw.io"
DEFAULT_TIMEOUT = 60


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def _get_api_key() -> str:
    """Return the WebClaw API key or raise ValueError."""
    key = os.getenv("WEBCLAW_API_KEY", "").strip()
    if not key:
        raise ValueError(
            "WEBCLAW_API_KEY environment variable not set. "
            "Get your API key at https://webclaw.io"
        )
    return key


def _get_base_url() -> str:
    """Return the WebClaw API base URL."""
    url = os.getenv("WEBCLAW_BASE_URL", "").strip().rstrip("/")
    return url or DEFAULT_BASE_URL


def _post(endpoint: str, payload: Dict[str, Any], timeout: int = DEFAULT_TIMEOUT) -> Dict[str, Any]:
    """POST JSON to the WebClaw v1 API and return parsed response.

    Raises on HTTP errors so callers can catch and wrap.
    """
    import httpx

    api_key = _get_api_key()
    base_url = _get_base_url()
    url = f"{base_url}{endpoint}"

    logger.info("WebClaw %s request to %s", endpoint, url)
    response = httpx.post(
        url,
        json=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        timeout=timeout,
    )
    response.raise_for_status()
    return response.json()


def _get(endpoint: str, timeout: int = DEFAULT_TIMEOUT) -> Dict[str, Any]:
    """GET from the WebClaw v1 API and return parsed response."""
    import httpx

    api_key = _get_api_key()
    base_url = _get_base_url()
    url = f"{base_url}{endpoint}"

    logger.info("WebClaw GET %s", url)
    response = httpx.get(
        url,
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=timeout,
    )
    response.raise_for_status()
    return response.json()


# ---------------------------------------------------------------------------
# Response normalization
# ---------------------------------------------------------------------------

def _normalize_search_results(response: Dict[str, Any]) -> Dict[str, Any]:
    """Map WebClaw /v1/search response to Hermes search shape."""
    web_results = []
    for i, result in enumerate(response.get("results", [])):
        entry: Dict[str, Any] = {
            "title": result.get("title", ""),
            "url": result.get("url", ""),
            "description": result.get("snippet", result.get("description", "")),
            "position": i + 1,
        }
        # Include scraped content if present
        if result.get("markdown"):
            entry["content"] = result["markdown"]
        web_results.append(entry)
    return {"success": True, "data": {"web": web_results}}


def _normalize_scrape_result(url: str, response: Dict[str, Any]) -> Dict[str, Any]:
    """Map WebClaw /v1/scrape response to Hermes extract shape."""
    metadata = response.get("metadata", {})
    if not isinstance(metadata, dict):
        metadata = {}

    title = metadata.get("title", "")
    final_url = metadata.get("sourceURL", metadata.get("url", url))

    # Prefer markdown > llm > text > html
    content = (
        response.get("markdown")
        or response.get("llm")
        or response.get("text")
        or response.get("html")
        or ""
    )

    return {
        "url": final_url,
        "title": title,
        "content": content,
        "raw_content": content,
        "metadata": metadata,
    }


def _normalize_crawl_results(response: Dict[str, Any], fallback_url: str) -> List[Dict[str, Any]]:
    """Map WebClaw /v1/crawl response to Hermes crawl shape."""
    pages: List[Dict[str, Any]] = []

    # WebClaw crawl returns data as a list of page objects
    data = response.get("data", response.get("results", []))
    if not isinstance(data, list):
        data = []

    for item in data:
        if not isinstance(item, dict):
            continue

        metadata = item.get("metadata", {})
        if not isinstance(metadata, dict):
            metadata = {}

        page_url = metadata.get("sourceURL", metadata.get("url", fallback_url))
        title = metadata.get("title", "")
        content = (
            item.get("markdown")
            or item.get("llm")
            or item.get("text")
            or item.get("html")
            or ""
        )

        pages.append({
            "url": page_url,
            "title": title,
            "content": content,
            "raw_content": content,
            "metadata": metadata,
        })

    return pages


# ---------------------------------------------------------------------------
# Provider class
# ---------------------------------------------------------------------------

class WebClawWebSearchProvider(WebSearchProvider):
    """WebClaw search + extract + crawl provider."""

    @property
    def name(self) -> str:
        return "webclaw"

    @property
    def display_name(self) -> str:
        return "WebClaw"

    def is_available(self) -> bool:
        """Return True when WEBCLAW_API_KEY is set."""
        return bool(os.getenv("WEBCLAW_API_KEY", "").strip())

    def supports_search(self) -> bool:
        return True

    def supports_extract(self) -> bool:
        return True

    def supports_crawl(self) -> bool:
        return True

    def search(self, query: str, limit: int = 5) -> Dict[str, Any]:
        """Execute a web search via WebClaw /v1/search."""
        try:
            from tools.interrupt import is_interrupted

            if is_interrupted():
                return {"success": False, "error": "Interrupted"}

            logger.info("WebClaw search: '%s' (limit=%d)", query, limit)
            raw = _post("/v1/search", {
                "query": query,
                "num_results": min(limit, 10),
                "scrape": True,
            })
            return _normalize_search_results(raw)
        except ValueError as exc:
            return {"success": False, "error": str(exc)}
        except Exception as exc:  # noqa: BLE001
            logger.warning("WebClaw search error: %s", exc)
            return {"success": False, "error": f"WebClaw search failed: {exc}"}

    async def extract(self, urls: List[str], **kwargs: Any) -> List[Dict[str, Any]]:
        """Extract content from URLs via WebClaw /v1/scrape.

        Async with per-URL threading and 60s timeout. Checks website
        access policy before and after redirects.
        """
        from tools.interrupt import is_interrupted

        if is_interrupted():
            return [{"url": u, "error": "Interrupted", "title": ""} for u in urls]

        fmt = kwargs.get("format")
        formats = ["markdown"]
        if fmt == "html":
            formats = ["html"]

        results: List[Dict[str, Any]] = []

        for url in urls:
            if is_interrupted():
                results.append({"url": url, "error": "Interrupted", "title": ""})
                continue

            # Pre-scrape website policy check
            blocked = check_website_access(url)
            if blocked:
                logger.info(
                    "Blocked web_extract for %s by rule %s",
                    blocked["host"], blocked["rule"],
                )
                results.append({
                    "url": url,
                    "title": "",
                    "content": "",
                    "error": blocked["message"],
                    "blocked_by_policy": {
                        "host": blocked["host"],
                        "rule": blocked["rule"],
                        "source": blocked["source"],
                    },
                })
                continue

            try:
                logger.info("WebClaw scraping: %s", url)
                try:
                    scrape_result = await asyncio.wait_for(
                        asyncio.to_thread(
                            _post,
                            "/v1/scrape",
                            {
                                "url": url,
                                "formats": formats,
                                "only_main_content": True,
                            },
                        ),
                        timeout=60,
                    )
                except asyncio.TimeoutError:
                    logger.warning("WebClaw scrape timed out for %s", url)
                    results.append({
                        "url": url,
                        "title": "",
                        "content": "",
                        "error": (
                            "Scrape timed out after 60s — page may be too large "
                            "or unresponsive. Try browser_navigate instead."
                        ),
                    })
                    continue

                normalized = _normalize_scrape_result(url, scrape_result)

                # Post-redirect website policy check
                final_url = normalized.get("url", url)
                final_blocked = check_website_access(final_url)
                if final_blocked:
                    logger.info(
                        "Blocked redirected web_extract for %s by rule %s",
                        final_blocked["host"], final_blocked["rule"],
                    )
                    results.append({
                        "url": final_url,
                        "title": normalized.get("title", ""),
                        "content": "",
                        "raw_content": "",
                        "error": final_blocked["message"],
                        "blocked_by_policy": {
                            "host": final_blocked["host"],
                            "rule": final_blocked["rule"],
                            "source": final_blocked["source"],
                        },
                    })
                    continue

                results.append(normalized)
            except Exception as exc:  # noqa: BLE001
                logger.debug("WebClaw scrape failed for %s: %s", url, exc)
                results.append({
                    "url": url,
                    "title": "",
                    "content": "",
                    "raw_content": "",
                    "error": str(exc),
                })

        return results

    async def crawl(self, url: str, **kwargs: Any) -> Dict[str, Any]:
        """Crawl a seed URL via WebClaw /v1/crawl.

        WebClaw crawl is async — start returns a crawl ID, then poll for
        results. This method starts the crawl and polls until complete or
        timeout.

        Accepted kwargs:
          - ``limit``: int — max pages (default 20)
          - ``instructions``: str — logged but not sent (WebClaw crawl
            does not accept instructions; that's an /extract feature)
          - ``depth``: ignored (API parity with Tavily)
        """
        try:
            from tools.interrupt import is_interrupted

            if is_interrupted():
                return {"results": [{"url": url, "title": "", "content": "", "error": "Interrupted"}]}

            instructions = kwargs.get("instructions")
            limit = kwargs.get("limit", 20)

            if instructions:
                logger.info(
                    "WebClaw crawl: 'instructions' parameter ignored "
                    "(not supported by WebClaw /crawl — use /extract)"
                )

            logger.info("WebClaw crawl: %s (limit=%d)", url, limit)

            # Start crawl
            start_result = await asyncio.to_thread(
                _post,
                "/v1/crawl",
                {
                    "url": url,
                    "max_pages": limit,
                },
            )

            # If result already contains data (sync response), use it directly
            if start_result.get("data") or start_result.get("results"):
                pages = _normalize_crawl_results(start_result, url)
                # Post-crawl policy check per page
                checked_pages = []
                for page in pages:
                    page_blocked = check_website_access(page.get("url", url))
                    if page_blocked:
                        logger.info(
                            "Blocked crawled page %s by rule %s",
                            page_blocked["host"], page_blocked["rule"],
                        )
                        checked_pages.append({
                            "url": page.get("url", url),
                            "title": page.get("title", ""),
                            "content": "",
                            "raw_content": "",
                            "error": page_blocked["message"],
                            "blocked_by_policy": {
                                "host": page_blocked["host"],
                                "rule": page_blocked["rule"],
                                "source": page_blocked["source"],
                            },
                        })
                    else:
                        checked_pages.append(page)
                return {"results": checked_pages}

            # Async crawl — poll for results
            crawl_id = start_result.get("id") or start_result.get("crawl_id")
            if not crawl_id:
                logger.warning("WebClaw crawl: no crawl ID in response")
                return {"results": [{"url": url, "title": "", "content": "", "error": "No crawl ID returned"}]}

            logger.info("WebClaw crawl started: id=%s, polling...", crawl_id)

            # Poll with backoff (max ~5 minutes)
            import time
            poll_interval = 2
            max_polls = 60
            for _ in range(max_polls):
                from tools.interrupt import is_interrupted as _check
                if _check():
                    return {"results": [{"url": url, "title": "", "content": "", "error": "Interrupted"}]}

                await asyncio.sleep(poll_interval)
                status = await asyncio.to_thread(
                    _get,
                    f"/v1/crawl/{crawl_id}",
                )

                state = status.get("status", "")
                if state in ("completed", "done", "finished"):
                    pages = _normalize_crawl_results(status, url)
                    checked_pages = []
                    for page in pages:
                        page_blocked = check_website_access(page.get("url", url))
                        if page_blocked:
                            checked_pages.append({
                                "url": page.get("url", url),
                                "title": page.get("title", ""),
                                "content": "",
                                "raw_content": "",
                                "error": page_blocked["message"],
                                "blocked_by_policy": {
                                    "host": page_blocked["host"],
                                    "rule": page_blocked["rule"],
                                    "source": page_blocked["source"],
                                },
                            })
                        else:
                            checked_pages.append(page)
                    return {"results": checked_pages}
                elif state in ("failed", "error"):
                    error_msg = status.get("error", "Crawl failed")
                    return {"results": [{"url": url, "title": "", "content": "", "error": error_msg}]}

                # Increase interval up to 10s
                poll_interval = min(poll_interval + 1, 10)

            return {"results": [{"url": url, "title": "", "content": "", "error": "Crawl timed out after polling"}]}

        except ValueError as exc:
            return {"results": [{"url": url, "title": "", "content": "", "error": str(exc)}]}
        except Exception as exc:  # noqa: BLE001
            logger.warning("WebClaw crawl error: %s", exc)
            return {
                "results": [{
                    "url": url,
                    "title": "",
                    "content": "",
                    "error": f"WebClaw crawl failed: {exc}",
                }]
            }

    def get_setup_schema(self) -> Dict[str, Any]:
        return {
            "name": "WebClaw",
            "badge": "paid · open-source",
            "tag": (
                "Fast web extraction with browser-grade TLS impersonation. "
                "Search + extract + crawl. Drop-in Firecrawl replacement."
            ),
            "env_vars": [
                {
                    "key": "WEBCLAW_API_KEY",
                    "prompt": "WebClaw API key (wc_...)",
                    "url": "https://webclaw.io",
                },
            ],
        }
