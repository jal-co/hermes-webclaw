#!/usr/bin/env bash
# Install the WebClaw plugin into Hermes Agent.
#
# Usage:
#   bash install.sh [HERMES_INSTALL_DIR]
#
# Defaults:
#   HERMES_INSTALL_DIR=/usr/local/lib/hermes-agent

set -euo pipefail

HERMES_DIR="${1:-/usr/local/lib/hermes-agent}"
PLUGIN_DIR="${HERMES_DIR}/plugins/web/webclaw"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if [ ! -d "${HERMES_DIR}/plugins/web" ]; then
  echo "ERROR: Hermes plugin directory not found at ${HERMES_DIR}/plugins/web"
  echo "Is Hermes Agent installed at ${HERMES_DIR}?"
  exit 1
fi

echo "Installing WebClaw plugin to ${PLUGIN_DIR}..."

mkdir -p "${PLUGIN_DIR}"
cp "${SCRIPT_DIR}/plugin.yaml"  "${PLUGIN_DIR}/plugin.yaml"
cp "${SCRIPT_DIR}/__init__.py"  "${PLUGIN_DIR}/__init__.py"
cp "${SCRIPT_DIR}/provider.py"  "${PLUGIN_DIR}/provider.py"
cp "${SCRIPT_DIR}/schemas.py"   "${PLUGIN_DIR}/schemas.py"
cp "${SCRIPT_DIR}/tools.py"     "${PLUGIN_DIR}/tools.py"

echo "✓ Plugin files installed"
echo ""
echo "Next steps:"
echo "  1. Set WEBCLAW_API_KEY in ~/.hermes/.env"
echo "  2. Set web backend in ~/.hermes/config.yaml:"
echo "       web:"
echo "         backend: webclaw"
echo "  3. Restart the gateway: sudo systemctl restart hermes-gateway"
echo ""
echo "To disable Firecrawl (optional — only needed if both are loaded):"
echo "  Remove or rename: ${HERMES_DIR}/plugins/web/firecrawl/"
