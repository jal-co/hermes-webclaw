---
name: hermes-webclaw
description: >-
  Hermes Agent plugin that replaces the bundled Firecrawl plugin with native
  WebClaw v1 API support — search, scrape/extract, and crawl. Install when the
  user wants to use WebClaw as their web backend in Hermes, set up WEBCLAW_API_KEY,
  or switch from Firecrawl to WebClaw.
license: AGPL-3.0
compatibility: "Hermes Agent ≥ 0.13.0, Python 3.11+, httpx"
metadata:
  author: jal-co
  version: 1.0.0
  webclaw-api: v1
  hermes-plugin-kind: backend
---

# hermes-webclaw

Hermes Agent plugin providing native [WebClaw](https://webclaw.io) v1 API
support as a drop-in replacement for the bundled Firecrawl plugin.

## What is WebClaw?

[WebClaw](https://github.com/0xMassi/webclaw) is a fast, open-source web
extraction toolkit built in Rust. It extracts clean markdown, JSON, or
LLM-optimized text from any website using HTTP with browser-grade TLS
impersonation — no headless browser required. 118ms average response time.

## What this plugin does

Registers a `WebSearchProvider` subclass (`webclaw`) that Hermes's built-in
`web_search`, `web_extract`, and `web_crawl` tools route through. Three
capabilities:

| Hermes tool    | WebClaw endpoint | What it does                              |
|----------------|------------------|-------------------------------------------|
| `web_search`   | `/v1/search`     | Web search with optional result scraping  |
| `web_extract`  | `/v1/scrape`     | Single-page content extraction            |
| `web_crawl`    | `/v1/crawl`      | Async BFS site crawl with polling         |

## Install

### 1. Get a WebClaw API key

Sign up at [webclaw.io](https://webclaw.io) and create an API key from the
dashboard. Keys are prefixed with `wc_`.

### 2. Copy plugin files to Hermes

Run the install script on the Hermes host:

```bash
bash scripts/install.sh
```

Or manually:

```bash
PLUGIN_DIR=/usr/local/lib/hermes-agent/plugins/web/webclaw
mkdir -p "$PLUGIN_DIR"
cp scripts/plugin.yaml  "$PLUGIN_DIR/plugin.yaml"
cp scripts/__init__.py   "$PLUGIN_DIR/__init__.py"
cp scripts/provider.py   "$PLUGIN_DIR/provider.py"
```

### 3. Set the API key

Add to `~/.hermes/.env`:

```
WEBCLAW_API_KEY=wc_your_key_here
```

### 4. Set WebClaw as the web backend

Edit `~/.hermes/config.yaml`:

```yaml
web:
  backend: webclaw
```

Or set per-capability:

```yaml
web:
  search_backend: webclaw
  extract_backend: webclaw
  crawl_backend: webclaw
```

### 5. (Optional) Disable Firecrawl

Both plugins register as web providers. If Firecrawl has credentials
configured, disable it to avoid conflicts:

```bash
mv /usr/local/lib/hermes-agent/plugins/web/firecrawl \
   /usr/local/lib/hermes-agent/plugins/web/firecrawl.disabled
```

### 6. Restart the gateway

```bash
sudo systemctl restart hermes-gateway
```

### 7. Verify

Check the gateway logs for WebClaw registration:

```bash
journalctl -u hermes-gateway --no-pager -n 20 | grep -i webclaw
```

Or run `hermes tools` and confirm WebClaw appears as the web backend.

## Environment variables

| Variable           | Required | Description                                              |
|--------------------|----------|----------------------------------------------------------|
| `WEBCLAW_API_KEY`  | Yes      | Your WebClaw API key (`wc_...`). Get one at webclaw.io.  |
| `WEBCLAW_BASE_URL` | No       | Override API base URL. Default: `https://api.webclaw.io`. |

## Self-hosting WebClaw

If running [`webclaw-server`](https://github.com/0xMassi/webclaw) locally:

```bash
WEBCLAW_API_KEY=your_secret
WEBCLAW_BASE_URL=http://your-server:3000
```

## Uninstall

```bash
rm -rf /usr/local/lib/hermes-agent/plugins/web/webclaw
# If you renamed Firecrawl, restore it:
mv /usr/local/lib/hermes-agent/plugins/web/firecrawl.disabled \
   /usr/local/lib/hermes-agent/plugins/web/firecrawl
sudo systemctl restart hermes-gateway
```

## Credits

Powered by [WebClaw](https://github.com/0xMassi/webclaw) by
[@0xMassi](https://github.com/0xMassi).
