# Changelog

## 1.0.3

- Upgrade homeassistant_api to 6.1: no WebSocket message size limit, so the 64 MiB workaround is removed.
- Fix the graph page when a sensor has no history, or when there are no light or climate entities.

## 1.0.2

- Fix `message too big` error with a large number of entities: accept WebSocket messages up to 64 MiB instead of 1 MiB.

## 1.0.1

- Add optional `homeassistant_url` and `homeassistant_token` options to connect directly to Home Assistant instead of through the Supervisor.
- Show a clear error page when Home Assistant refuses the connection (for example HTTP 502 from the Supervisor).

## 1.0.0

- First release as a Home Assistant add-on.
