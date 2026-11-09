#!/bin/sh
set -e

# Print one value of the add-on options (/data/options.json), or nothing when it is not set
read_option() {
  python3 -c '
import json, sys
try:
    with open("/data/options.json") as f:
        print(json.load(f).get(sys.argv[1]) or "")
except (OSError, ValueError):
    pass
' "$1"
}

# Running as a Home Assistant add-on
if [ -n "$SUPERVISOR_TOKEN" ]; then
  ha_url=$(read_option homeassistant_url)
  ha_token=$(read_option homeassistant_token)
  if [ -n "$ha_url" ] && [ -n "$ha_token" ]; then
    # Direct connection configured in the add-on options
    export HA_IPAPER_GENERAL__homeassistant_url="$ha_url"
    export HA_IPAPER_GENERAL__homeassistant_token="$ha_token"
  else
    if [ -n "$ha_url" ] || [ -n "$ha_token" ]; then
      echo "Set both homeassistant_url and homeassistant_token to connect directly; using the Supervisor connection" >&2
    fi
    # Talk to Home Assistant through the Supervisor proxy
    export HA_IPAPER_GENERAL__homeassistant_url=http://supervisor/core
    export HA_IPAPER_GENERAL__homeassistant_token="$SUPERVISOR_TOKEN"
  fi
  if [ -n "$TZ" ]; then
    export HA_IPAPER_GENERAL__timezone="$TZ"
  fi
fi

mkdir -p /config

if [ ! -f /config/config.yaml ]; then
  cp /app/config.yaml /config/config.yaml
fi

exec ha-ipaper -config /config/config.yaml
