#!/bin/bash
set -e

mkdir -p /config

if [ ! -f /config/config.yaml ]; then
  cp /app/config.yaml /config/config.yaml
fi

exec uv run ha-ipaper -config /config/config.yaml
