"""WebClaw plugin for Hermes Agent.

Registers:
- WebClawWebSearchProvider — backs web_search, web_extract, web_crawl
- 9 dedicated tools for the full WebClaw v1 API surface
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path


def _import_from_here(module_name: str, filename: str):
    """Import a module from the same directory as this file.

    Works regardless of whether the plugin is installed as a bundled
    backend (plugins/web/webclaw/) or as a user plugin via
    ``hermes plugins install`` (~/.hermes/plugins/hermes-webclaw/).
    """
    plugin_dir = Path(__file__).resolve().parent
    filepath = plugin_dir / filename

    spec = importlib.util.spec_from_file_location(
        f"hermes_webclaw_{module_name}", str(filepath)
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def register(ctx) -> None:
    """Register WebClaw web provider + all 9 tools."""

    # Import provider, schemas, tools from the plugin directory
    provider_mod = _import_from_here("provider", "provider.py")
    schemas_mod = _import_from_here("schemas", "schemas.py")
    tools_mod = _import_from_here("tools", "tools.py")

    # 1. Register as the web search/extract/crawl provider
    ctx.register_web_search_provider(
        provider_mod.WebClawWebSearchProvider()
    )

    # 2. Register all 9 dedicated tools
    _TOOLS = (
        ("webclaw_scrape",    schemas_mod.WEBCLAW_SCRAPE,    tools_mod.handle_scrape,    "🌐"),
        ("webclaw_search",    schemas_mod.WEBCLAW_SEARCH,    tools_mod.handle_search,    "🔎"),
        ("webclaw_crawl",     schemas_mod.WEBCLAW_CRAWL,     tools_mod.handle_crawl,     "🕷️"),
        ("webclaw_extract",   schemas_mod.WEBCLAW_EXTRACT,   tools_mod.handle_extract,   "📊"),
        ("webclaw_summarize", schemas_mod.WEBCLAW_SUMMARIZE, tools_mod.handle_summarize, "📝"),
        ("webclaw_diff",      schemas_mod.WEBCLAW_DIFF,      tools_mod.handle_diff,      "📋"),
        ("webclaw_map",       schemas_mod.WEBCLAW_MAP,       tools_mod.handle_map,       "🗺️"),
        ("webclaw_batch",     schemas_mod.WEBCLAW_BATCH,     tools_mod.handle_batch,     "📦"),
        ("webclaw_brand",     schemas_mod.WEBCLAW_BRAND,     tools_mod.handle_brand,     "🎨"),
    )

    for name, schema, handler, emoji in _TOOLS:
        ctx.register_tool(
            name=name,
            toolset="webclaw",
            schema=schema,
            handler=handler,
            check_fn=tools_mod._check_webclaw_available,
            emoji=emoji,
        )
