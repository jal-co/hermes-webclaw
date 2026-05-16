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

import importlib
import sys
from pathlib import Path


def _import_provider():
    """Import the provider module from the same directory as this file.

    Works regardless of whether the plugin is installed as a bundled
    backend (plugins/web/webclaw/) or as a user plugin via
    ``hermes plugins install`` (~/.hermes/plugins/hermes-webclaw/).
    """
    plugin_dir = Path(__file__).resolve().parent
    provider_path = plugin_dir / "provider.py"

    # If already importable via the bundled path, use that
    try:
        from plugins.web.webclaw.provider import WebClawWebSearchProvider
        return WebClawWebSearchProvider
    except ImportError:
        pass

    # Otherwise load from the file directly (user-installed plugin)
    spec = importlib.util.spec_from_file_location(
        "hermes_webclaw_provider", str(provider_path)
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod.WebClawWebSearchProvider


def register(ctx) -> None:
    """Register the WebClaw provider with the plugin context."""
    WebClawWebSearchProvider = _import_provider()
    ctx.register_web_search_provider(WebClawWebSearchProvider())
