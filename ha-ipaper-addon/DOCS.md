# HA-IPaper

Interactive e-Paper dashboard for Home Assistant, designed for the built-in browser of Kobo, Kindle and other e-readers.

## Usage

1. Start the add-on.
2. On your e-reader, open `http://<home-assistant-ip>:8081/`.

No access token is needed: the add-on talks to Home Assistant through the Supervisor.

## Configuration

On first start, the add-on creates `config.yaml` in `/addon_configs/<id>_ha_ipaper/`
(reachable with the File editor, Studio Code Server or Samba add-ons).

Edit this file to change the menu, the pages and the graphs, then restart the add-on.
The `homeassistant_url`, `homeassistant_token` and `timezone` values in this file are ignored:
the add-on always uses the Supervisor connection and the Home Assistant timezone.

### Template override

Create `html-template/` next to `config.yaml` and put in it only the files you want to override
(for example `components/lights.html` or `style.css`).
Copy the defaults from https://github.com/o0Zz/ha-ipaper/tree/main/src/ha_ipaper/html-template.

## Network

To use another port, change it in the add-on **Network** section.

## Security

The dashboard has no login, and anyone who can reach the port can control your Home Assistant entities.
Do not expose this port to the Internet.
