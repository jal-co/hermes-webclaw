"""WebClaw web search + extract + crawl plugin for Hermes Agent.

Replaces the bundled Firecrawl plugin with native WebClaw v1 API support.
Registers as a web search provider so Hermes's built-in web_search,
web_extract, and web_crawl tools route through WebClaw.

WebClaw is a fast, open-source web extraction toolkit built in Rust.
It turns any website into clean markdown, JSON, plain text, or
LLM-optimized output — without a headless browser.

- Source: https://github.com/0xMassi/webclaw
- Docs:   https://webclaw.io/docs
- Cloud:  https://api.webclaw.io
"""

from __future__ import annotations

from plugins.web.webclaw.provider import WebClawWebSearchProvider


def register(ctx) -> None:
    """Register the WebClaw provider with the plugin context."""
    ctx.register_web_search_provider(WebClawWebSearchProvider())
