"""WebClaw tool schemas — what the LLM sees."""

WEBCLAW_SCRAPE = {
    "name": "webclaw_scrape",
    "description": (
        "Scrape a single page using WebClaw. Returns clean markdown, text, "
        "or LLM-optimized output. Supports CSS filtering, screenshots, "
        "mobile User-Agent, page Q&A, and multiple output formats. "
        "Fast HTTP extraction with browser-grade TLS impersonation — no "
        "headless browser. Use for fetching any single URL's content."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "HTTP or HTTPS URL to scrape.",
            },
            "formats": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    'Output formats: "markdown", "llm", "text", "json", '
                    '"links", "rawHtml", "screenshot", "query". '
                    'Default: ["markdown"].'
                ),
            },
            "only_main_content": {
                "type": "boolean",
                "description": "Extract only main content, skip nav/sidebar/footer. Default: true.",
            },
            "include_selectors": {
                "type": "array",
                "items": {"type": "string"},
                "description": "CSS selectors to extract exclusively.",
            },
            "exclude_selectors": {
                "type": "array",
                "items": {"type": "string"},
                "description": "CSS selectors to exclude.",
            },
            "screenshot": {
                "type": "boolean",
                "description": "Take a screenshot. Returns base64 PNG.",
            },
            "mobile": {
                "type": "boolean",
                "description": "Use mobile User-Agent.",
            },
            "query": {
                "type": "string",
                "description": 'Natural language question about the page. Use with format "query".',
            },
        },
        "required": ["url"],
    },
}

WEBCLAW_SEARCH = {
    "name": "webclaw_search",
    "description": (
        "Web search using WebClaw. Returns structured results with titles, "
        "URLs, and snippets. Optionally scrapes content from each result "
        "URL in parallel. Use for any web search query."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query.",
            },
            "count": {
                "type": "number",
                "description": "Number of results (1-10). Default: 5.",
            },
            "scrape": {
                "type": "boolean",
                "description": "Scrape content from each result URL. Default: true.",
            },
            "country": {
                "type": "string",
                "description": 'Country code for localized results (e.g. "us").',
            },
            "lang": {
                "type": "string",
                "description": 'Language code (e.g. "en").',
            },
        },
        "required": ["query"],
    },
}

WEBCLAW_CRAWL = {
    "name": "webclaw_crawl",
    "description": (
        "BFS crawl a website starting from a URL. Discovers and scrapes "
        "linked pages up to a depth/page limit. Supports sitemap seeding "
        "and path filtering. Use for scraping documentation sites or "
        "exploring a site's content structure."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "Starting URL to crawl.",
            },
            "max_depth": {
                "type": "number",
                "description": "Maximum crawl depth. Default: 2.",
            },
            "max_pages": {
                "type": "number",
                "description": "Maximum pages to crawl. Default: 50.",
            },
            "use_sitemap": {
                "type": "boolean",
                "description": "Seed crawl from sitemap.xml.",
            },
            "include_paths": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Glob patterns for paths to include.",
            },
            "exclude_paths": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Glob patterns for paths to exclude.",
            },
        },
        "required": ["url"],
    },
}

WEBCLAW_EXTRACT = {
    "name": "webclaw_extract",
    "description": (
        "LLM-powered structured data extraction from a URL. Provide a "
        "JSON schema or a natural language prompt describing what to "
        "extract. Returns structured JSON matching your schema. Use when "
        "you need specific data points from a page (prices, contacts, "
        "specs, etc.)."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "URL to extract structured data from.",
            },
            "schema": {
                "type": "object",
                "description": "JSON schema describing the data to extract.",
            },
            "prompt": {
                "type": "string",
                "description": "Natural language description of what to extract.",
            },
        },
        "required": ["url"],
    },
}

WEBCLAW_SUMMARIZE = {
    "name": "webclaw_summarize",
    "description": (
        "LLM-powered summarization of a web page. Returns a concise "
        "summary of the page content. Use when you need a quick overview "
        "of a URL without the full content."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "URL to summarize.",
            },
            "sentences": {
                "type": "number",
                "description": "Number of sentences in the summary. Default: 3.",
            },
        },
        "required": ["url"],
    },
}

WEBCLAW_DIFF = {
    "name": "webclaw_diff",
    "description": (
        "Content change tracking — compare current page content against "
        "a previous JSON snapshot. Returns what changed. Use to monitor "
        "pages for updates or detect content modifications."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "URL to compare against snapshot.",
            },
            "snapshot": {
                "type": "object",
                "description": "Previous JSON snapshot from a WebClaw scrape (json format).",
            },
        },
        "required": ["url", "snapshot"],
    },
}

WEBCLAW_MAP = {
    "name": "webclaw_map",
    "description": (
        "Sitemap discovery — find all URLs on a site via sitemap.xml "
        "and robots.txt. Returns the full URL list. Use to discover "
        "all pages on a site before deciding what to scrape."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "Base URL to discover sitemap URLs from.",
            },
        },
        "required": ["url"],
    },
}

WEBCLAW_BATCH = {
    "name": "webclaw_batch",
    "description": (
        "Extract content from multiple URLs concurrently in a single "
        "request. More efficient than calling webclaw_scrape in a loop. "
        "Use when you need content from several known URLs."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "urls": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Array of URLs to extract (1-100).",
            },
            "formats": {
                "type": "array",
                "items": {"type": "string"},
                "description": 'Output formats. Default: ["markdown"].',
            },
            "concurrency": {
                "type": "number",
                "description": "Max concurrent requests. Default: 5.",
            },
        },
        "required": ["urls"],
    },
}

WEBCLAW_BRAND = {
    "name": "webclaw_brand",
    "description": (
        "Extract brand identity from a website — colors, fonts, logo URL, "
        "and favicon. Use when you need to match a site's visual style, "
        "build a style guide, or analyze a brand's web presence."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "URL to extract brand identity from.",
            },
        },
        "required": ["url"],
    },
}
