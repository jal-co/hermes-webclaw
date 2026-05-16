# hermes-webclaw

Hermes Agent plugin that replaces the bundled Firecrawl plugin with native [WebClaw](https://webclaw.io) v1 API support.

[![License](https://shieldcn.dev/github/license/jal-co/hermes-webclaw.svg?variant=branded)](https://github.com/jal-co/hermes-webclaw/blob/main/LICENSE)
[![Hermes](https://shieldcn.dev/badge/Hermes_Agent-Plugin.svg?variant=branded&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHBhdGggZD0iTTEyIDJDNi40OCAyIDIgNi40OCAyIDEyczQuNDggMTAgMTAgMTAgMTAtNC40OCAxMC0xMFMxNy41MiAyIDEyIDJ6IiBmaWxsPSIjZmY2YjZiIi8+PC9zdmc+)](https://github.com/NousResearch/hermes-agent)
[![WebClaw](https://shieldcn.dev/badge/Powered_by-WebClaw.svg?variant=branded&logo=safari)](https://webclaw.io)
[![Docs](https://shieldcn.dev/badge/Docs-webclaw.io.svg?variant=branded&logo=readthedocs)](https://webclaw.io/docs)

---

## What is WebClaw?

[WebClaw](https://github.com/0xMassi/webclaw) is a fast, open-source web extraction toolkit built in Rust by [@0xMassi](https://github.com/0xMassi). It turns any website into clean markdown, JSON, plain text, or LLM-optimized output — without a headless browser. All extraction happens over raw HTTP using browser-grade TLS impersonation, making it lightweight and deployable anywhere.

WebClaw ships as a CLI, REST API, and MCP server, and is a **drop-in replacement for Firecrawl v2** with a richer native v1 API surface.

- **Source:** [github.com/0xMassi/webclaw](https://github.com/0xMassi/webclaw)
- **Docs:** [webclaw.io/docs](https://webclaw.io/docs)
- **Cloud API:** [api.webclaw.io](https://api.webclaw.io)
- **License:** AGPL-3.0

## Why this plugin?

Hermes Agent ships with a bundled Firecrawl plugin for `web_search`, `web_extract`, and `web_crawl`. If you're already using a `wc_`-prefixed API key, you're hitting WebClaw's cloud through Firecrawl's v2 compatibility layer — but you're only getting a fraction of what WebClaw can do.

This plugin replaces Firecrawl entirely. It registers as a `WebSearchProvider` so Hermes's built-in web tools route through WebClaw's native v1 API — faster responses, better extraction quality, and the full feature set.

## Capabilities

This plugin registers three capabilities with Hermes's web tool dispatcher:

| Hermes tool    | WebClaw endpoint | What it does                              |
|----------------|------------------|-------------------------------------------|
| `web_search`   | `/v1/search`     | Web search with optional result scraping  |
| `web_extract`  | `/v1/scrape`     | Single-page content extraction            |
| `web_crawl`    | `/v1/crawl`      | Async BFS site crawl with polling         |

All three appear in the `hermes tools` picker under **Web Search & Extract** and work with the existing `web_search`, `web_extract`, and `web_crawl` tool calls your agent already uses.

## Install

### 1. Get a WebClaw API key

Sign up at [webclaw.io](https://webclaw.io) and create an API key from the dashboard. Keys are prefixed with `wc_`.

### 2. Install the plugin

**Option A: `hermes plugins install`** (recommended)

```bash
hermes plugins install jal-co/hermes-webclaw --enable
```

This clones the repo, prompts for `WEBCLAW_API_KEY`, and enables the plugin. It appears in the `hermes tools` picker under **Web Search & Extract**.

**Option B: Download a release tarball**

```bash
curl -fsSL https://github.com/jal-co/hermes-webclaw/releases/latest/download/hermes-webclaw-1.0.0.tar.gz | tar xz
cd hermes-webclaw-1.0.0
bash install.sh
```

Or download a specific version from the [releases page](https://github.com/jal-co/hermes-webclaw/releases).

**Option C: Clone and install manually**

```bash
git clone https://github.com/jal-co/hermes-webclaw.git
cd hermes-webclaw
bash scripts/install.sh
```

**Option D: Direct copy into bundled plugins**

```bash
PLUGIN_DIR=/usr/local/lib/hermes-agent/plugins/web/webclaw
mkdir -p "$PLUGIN_DIR"
cp plugin.yaml  "$PLUGIN_DIR/plugin.yaml"
cp __init__.py   "$PLUGIN_DIR/__init__.py"
cp provider.py   "$PLUGIN_DIR/provider.py"
```

### 3. Set the API key

Add `WEBCLAW_API_KEY` to your Hermes environment file:

```bash
echo 'WEBCLAW_API_KEY=wc_your_key_here' >> ~/.hermes/.env
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

Alternatively, run `hermes tools` — WebClaw will appear in the **Web Search & Extract** picker. Selecting it writes the config for you.

### 5. (Optional) Disable Firecrawl

If Firecrawl has credentials configured and you want to avoid conflicts:

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

Or run `hermes tools` and confirm WebClaw appears as the active web backend.

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `WEBCLAW_API_KEY` | Yes | Your WebClaw API key (`wc_...`). Get one at [webclaw.io](https://webclaw.io). |
| `WEBCLAW_BASE_URL` | No | Override the API base URL. Default: `https://api.webclaw.io`. Use for self-hosted instances. |

## Migrating from Firecrawl

If you're already using `FIRECRAWL_API_KEY` with a `wc_`-prefixed key, you're hitting WebClaw's cloud API via the Firecrawl v2 compatibility layer. This plugin switches to the native v1 endpoints for better performance.

1. Set `WEBCLAW_API_KEY` to your existing `wc_` key
2. Install the plugin (see above)
3. Set `web: backend: webclaw` in config
4. Optionally disable Firecrawl
5. Restart the gateway

Your existing `web_search`, `web_extract`, and `web_crawl` calls will now route through WebClaw natively.

## Self-Hosting WebClaw

If you're running [`webclaw-server`](https://github.com/0xMassi/webclaw) on your own infrastructure:

```bash
# Start the server
webclaw-server --port 3000 --api-key your_secret
```

Then set both environment variables:

```bash
WEBCLAW_API_KEY=your_secret
WEBCLAW_BASE_URL=http://your-server:3000
```

See the [WebClaw self-hosting docs](https://webclaw.io/docs/self-hosting) for full setup instructions.

## Uninstall

```bash
rm -rf /usr/local/lib/hermes-agent/plugins/web/webclaw

# If you renamed Firecrawl, restore it:
mv /usr/local/lib/hermes-agent/plugins/web/firecrawl.disabled \
   /usr/local/lib/hermes-agent/plugins/web/firecrawl

# Update config
# Edit ~/.hermes/config.yaml — change web.backend back to firecrawl (or remove)

sudo systemctl restart hermes-gateway
```

## Also available for OpenClaw

If you're running OpenClaw instead of Hermes Agent, see [openclaw-webclaw](https://github.com/jal-co/openclaw-webclaw) — the TypeScript plugin with 9 dedicated tools for the full v1 API surface.

## Credits

This plugin is powered by [WebClaw](https://github.com/0xMassi/webclaw) by [@0xMassi](https://github.com/0xMassi) — a fast, Rust-based web extraction toolkit for LLMs. WebClaw provides the extraction engine, cloud API, and Firecrawl v2 compatibility layer that this plugin builds on.

## License

[AGPL-3.0](./LICENSE) — same license as WebClaw.
