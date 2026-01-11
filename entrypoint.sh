#!/bin/bash
set -e

mkdir -p /config

if [ ! -f /config/config.yaml ]; then
  cp /app/config.yaml /config/config.yaml
fi

if [ ! -d /config/html-template ]; then
  cp -r /app/html-template /config/html-template
fi

exec uv run ha-ipaper -config /config/config.yaml
