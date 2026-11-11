# Changelog

## 1.0.2

- Fix `message too big` error with a large number of entities: accept WebSocket messages up to 64 MiB instead of 1 MiB.

## 1.0.1

- Add optional `homeassistant_url` and `homeassistant_token` options to connect directly to Home Assistant instead of through the Supervisor.
- Show a clear error page when Home Assistant refuses the connection (for example HTTP 502 from the Supervisor).

## 1.0.0

- First release as a Home Assistant add-on.
