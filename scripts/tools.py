"""WebClaw tool handlers — the code that runs when the LLM calls each tool."""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "https://api.webclaw.io"
DEFAULT_TIMEOUT = 60


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def _get_api_key() -> str:
    key = os.getenv("WEBCLAW_API_KEY", "").strip()
    if not key:
        raise ValueError(
            "WEBCLAW_API_KEY environment variable not set. "
            "Get your API key at https://webclaw.io"
        )
    return key


def _get_base_url() -> str:
    url = os.getenv("WEBCLAW_BASE_URL", "").strip().rstrip("/")
    return url or DEFAULT_BASE_URL


def _post(endpoint: str, payload: Dict[str, Any], timeout: int = DEFAULT_TIMEOUT) -> Dict[str, Any]:
    import httpx
    api_key = _get_api_key()
    base_url = _get_base_url()
    url = f"{base_url}{endpoint}"
    logger.info("WebClaw %s request to %s", endpoint, url)
    response = httpx.post(
        url, json=payload,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        timeout=timeout,
    )
    response.raise_for_status()
    return response.json()


def _get(endpoint: str, timeout: int = DEFAULT_TIMEOUT) -> Dict[str, Any]:
    import httpx
    api_key = _get_api_key()
    base_url = _get_base_url()
    url = f"{base_url}{endpoint}"
    logger.info("WebClaw GET %s", url)
    response = httpx.get(
        url, headers={"Authorization": f"Bearer {api_key}"},
        timeout=timeout,
    )
    response.raise_for_status()
    return response.json()


def _check_webclaw_available() -> bool:
    return bool(os.getenv("WEBCLAW_API_KEY", "").strip())


def _tool_result(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False)


def _tool_error(message: str) -> str:
    return json.dumps({"error": str(message)}, ensure_ascii=False)


# ---------------------------------------------------------------------------
# webclaw_scrape
# ---------------------------------------------------------------------------

def handle_scrape(args: dict, **kwargs) -> str:
    try:
        url = args.get("url", "").strip()
        if not url:
            return _tool_error("url is required")

        body: Dict[str, Any] = {
            "url": url,
            "formats": args.get("formats", ["markdown"]),
            "only_main_content": args.get("only_main_content", True),
        }
        if args.get("include_selectors"):
            body["include_selectors"] = args["include_selectors"]
        if args.get("exclude_selectors"):
            body["exclude_selectors"] = args["exclude_selectors"]
        if args.get("screenshot"):
            body["screenshot"] = True
        if args.get("mobile"):
            body["mobile"] = True
        if args.get("query"):
            body["query"] = args["query"]

        result = _post("/v1/scrape", body)

        content = (
            result.get("markdown")
            or result.get("llm")
            or result.get("text")
            or result.get("html")
            or ""
        )
        metadata = result.get("metadata", {})

        output: Dict[str, Any] = {
            "success": True,
            "url": url,
            "title": metadata.get("title", ""),
            "content": content,
        }
        if result.get("query_answer"):
            output["query_answer"] = result["query_answer"]
        if result.get("screenshot"):
            output["screenshot"] = result["screenshot"]
        if result.get("links"):
            output["links"] = result["links"]

        return _tool_result(output)
    except Exception as e:
        return _tool_error(f"WebClaw scrape failed: {e}")


# ---------------------------------------------------------------------------
# webclaw_search
# ---------------------------------------------------------------------------

def handle_search(args: dict, **kwargs) -> str:
    try:
        query = args.get("query", "").strip()
        if not query:
            return _tool_error("query is required")

        count = min(max(int(args.get("count", 5)), 1), 10)
        body: Dict[str, Any] = {
            "query": query,
            "num_results": count,
            "scrape": args.get("scrape", True),
        }
        if args.get("country"):
            body["country"] = args["country"]
        if args.get("lang"):
            body["lang"] = args["lang"]

        result = _post("/v1/search", body)
        raw_results = result.get("results", [])

        return _tool_result({
            "success": True,
            "query": query,
            "count": len(raw_results),
            "results": [
                {
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "description": r.get("snippet", r.get("description", "")),
                    **({"content": r["markdown"]} if r.get("markdown") else {}),
                }
                for r in raw_results
            ],
        })
    except Exception as e:
        return _tool_error(f"WebClaw search failed: {e}")


# ---------------------------------------------------------------------------
# webclaw_crawl
# ---------------------------------------------------------------------------

def handle_crawl(args: dict, **kwargs) -> str:
    try:
        url = args.get("url", "").strip()
        if not url:
            return _tool_error("url is required")

        body: Dict[str, Any] = {"url": url}
        if args.get("max_depth"):
            body["max_depth"] = int(args["max_depth"])
        if args.get("max_pages"):
            body["max_pages"] = int(args["max_pages"])
        if args.get("use_sitemap"):
            body["use_sitemap"] = True
        if args.get("include_paths"):
            body["include_paths"] = args["include_paths"]
        if args.get("exclude_paths"):
            body["exclude_paths"] = args["exclude_paths"]

        result = _post("/v1/crawl", body)

        # If sync response with data, return directly
        data = result.get("data", result.get("results", []))
        if isinstance(data, list) and data:
            pages = []
            for item in data:
                if not isinstance(item, dict):
                    continue
                meta = item.get("metadata", {})
                pages.append({
                    "url": meta.get("sourceURL", meta.get("url", url)),
                    "title": meta.get("title", ""),
                    "content": item.get("markdown") or item.get("text") or "",
                })
            return _tool_result({"success": True, "pages": len(pages), "results": pages})

        # Async crawl — return job ID for polling
        crawl_id = result.get("id") or result.get("crawl_id")
        if crawl_id:
            return _tool_result({
                "success": True,
                "status": "started",
                "crawl_id": crawl_id,
                "message": f"Crawl started. Poll status with webclaw_crawl_status (not yet implemented). ID: {crawl_id}",
            })

        return _tool_result({"success": True, "raw": result})
    except Exception as e:
        return _tool_error(f"WebClaw crawl failed: {e}")


# ---------------------------------------------------------------------------
# webclaw_extract
# ---------------------------------------------------------------------------

def handle_extract(args: dict, **kwargs) -> str:
    try:
        url = args.get("url", "").strip()
        if not url:
            return _tool_error("url is required")

        body: Dict[str, Any] = {"url": url}
        if args.get("schema"):
            body["schema"] = args["schema"]
        if args.get("prompt"):
            body["prompt"] = args["prompt"]

        result = _post("/v1/extract", body)
        return _tool_result({"success": True, "url": url, "data": result})
    except Exception as e:
        return _tool_error(f"WebClaw extract failed: {e}")


# ---------------------------------------------------------------------------
# webclaw_summarize
# ---------------------------------------------------------------------------

def handle_summarize(args: dict, **kwargs) -> str:
    try:
        url = args.get("url", "").strip()
        if not url:
            return _tool_error("url is required")

        body: Dict[str, Any] = {"url": url}
        if args.get("sentences"):
            body["sentences"] = int(args["sentences"])

        result = _post("/v1/summarize", body)
        return _tool_result({"success": True, "url": url, "summary": result})
    except Exception as e:
        return _tool_error(f"WebClaw summarize failed: {e}")


# ---------------------------------------------------------------------------
# webclaw_diff
# ---------------------------------------------------------------------------

def handle_diff(args: dict, **kwargs) -> str:
    try:
        url = args.get("url", "").strip()
        if not url:
            return _tool_error("url is required")
        snapshot = args.get("snapshot")
        if not snapshot:
            return _tool_error("snapshot is required (previous JSON from a webclaw scrape)")

        result = _post("/v1/diff", {"url": url, "snapshot": snapshot})
        return _tool_result({"success": True, "url": url, "diff": result})
    except Exception as e:
        return _tool_error(f"WebClaw diff failed: {e}")


# ---------------------------------------------------------------------------
# webclaw_map
# ---------------------------------------------------------------------------

def handle_map(args: dict, **kwargs) -> str:
    try:
        url = args.get("url", "").strip()
        if not url:
            return _tool_error("url is required")

        result = _post("/v1/map", {"url": url})
        return _tool_result({"success": True, "url": url, "map": result})
    except Exception as e:
        return _tool_error(f"WebClaw map failed: {e}")


# ---------------------------------------------------------------------------
# webclaw_batch
# ---------------------------------------------------------------------------

def handle_batch(args: dict, **kwargs) -> str:
    try:
        urls = args.get("urls", [])
        if not urls:
            return _tool_error("urls is required (array of URLs)")

        body: Dict[str, Any] = {"urls": urls}
        if args.get("formats"):
            body["formats"] = args["formats"]
        if args.get("concurrency"):
            body["concurrency"] = int(args["concurrency"])

        result = _post("/v1/batch", body)
        return _tool_result({"success": True, "count": len(urls), "results": result})
    except Exception as e:
        return _tool_error(f"WebClaw batch failed: {e}")


# ---------------------------------------------------------------------------
# webclaw_brand
# ---------------------------------------------------------------------------

def handle_brand(args: dict, **kwargs) -> str:
    try:
        url = args.get("url", "").strip()
        if not url:
            return _tool_error("url is required")

        result = _post("/v1/brand", {"url": url})
        return _tool_result({"success": True, "url": url, "brand": result})
    except Exception as e:
        return _tool_error(f"WebClaw brand failed: {e}")
