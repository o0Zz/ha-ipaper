#!/bin/sh
set -e

# Running as a Home Assistant add-on: talk to Home Assistant through the Supervisor proxy
if [ -n "$SUPERVISOR_TOKEN" ]; then
  export HA_IPAPER_GENERAL__homeassistant_url=http://supervisor/core
  export HA_IPAPER_GENERAL__homeassistant_token="$SUPERVISOR_TOKEN"
  if [ -n "$TZ" ]; then
    export HA_IPAPER_GENERAL__timezone="$TZ"
  fi
fi

mkdir -p /config

if [ ! -f /config/config.yaml ]; then
  cp /app/config.yaml /config/config.yaml
fi

exec ha-ipaper -config /config/config.yaml
