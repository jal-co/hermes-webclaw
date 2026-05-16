## ✓ WebClaw plugin installed

**Set WebClaw as your web backend:**

```bash
hermes config set web.backend webclaw
```

Or run `hermes tools` → select **WebClaw** under Web Search & Extract.

Then restart the gateway:

```bash
sudo systemctl restart hermes-gateway
```

**9 tools available:** `webclaw_scrape`, `webclaw_search`, `webclaw_crawl`, `webclaw_extract`, `webclaw_summarize`, `webclaw_diff`, `webclaw_map`, `webclaw_batch`, `webclaw_brand`

Docs: https://webclaw.io/docs
