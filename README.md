# HA-IPaper

**Home Assistant Interactive e-Paper Dashboard (For Kobo, Kindle, etc.)**

HA-IPaper is a ready-to-use e-paper dashboard for Home Assistant that enables display and interaction with your smart home setup on e-paper devices with a browser.

![image](https://github.com/user-attachments/assets/8d98ff2e-f702-460a-b45b-4f50103aefc9)

## Key Differences from Other Home Assistant e-Paper Dashboards

1. **Compatible with Built-in eReader Browser:** This project is designed to work with the limited browsers on e-paper eReaders. Simply prevent your eReader from entering deep sleep mode, and enable fullscreen mode for an optimal experience. For Kobo devices, you can use NickelMenu to manage these settings directly. On Kindle, you may need to jailbreak the device to disable deep sleep and enable fullscreen mode in the browser.

2. **No Coding Required:** Unlike other projects where you need to write HTML or additional code, HA-IPaper is designed to work out of the box. Configure it simply through a YAML file or environment variables, without needing to handle complex customization.

3. **Interactive:** This project allows full interaction with Home Assistant directly from your e-reader.

4. **Automatic adaptation to new entities**: HA-IPaper automatically integrates new entities added to your Home Assistant setup without requiring manual updates to the dashboard. 

## Quick Start

### Home Assistant add-on (HA OS / Supervised)

[![Add repository](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fo0Zz%2Fha-ipaper)

1. In Home Assistant, go to **Settings → Add-ons → Add-on Store → ⋮ → Repositories**.
2. Add `https://github.com/o0Zz/ha-ipaper` and close the dialog.
3. Install **HA-IPaper** and start it.
4. On your e-reader, open `http://<home-assistant-ip>:8081/`.

No access token is needed. The configuration file is created in `/addon_configs/<id>_ha_ipaper/config.yaml`.

### Docker (any machine with Docker)

Use this when Home Assistant does not run on HA OS / Supervised, or when you want to run HA-IPaper on another machine.
You do not need to download the source code: the image is published on `ghcr.io`.

First, create a Home Assistant long-lived access token (see [Home Assistant Setup](#home-assistant-setup)).

#### Option A: `docker run`

```
docker run -d --name ha-ipaper --restart unless-stopped -p 8081:8081 -v /data/ha-ipaper:/config \
  -e HA_IPAPER_GENERAL__homeassistant_url=http://homeassistant.local:8123 \
  -e HA_IPAPER_GENERAL__homeassistant_token=YOUR_LONG_LIVED_ACCESS_TOKEN_HERE \
  ghcr.io/o0zz/ha-ipaper:latest
```

#### Option B: `docker compose`

1. Create a folder (for example `ha-ipaper/`) and, in it, a file `docker-compose.yml`:
   ```yaml
   services:
     ha-ipaper:
       image: ghcr.io/o0zz/ha-ipaper:latest
       container_name: ha-ipaper
       environment:
         - TZ=Europe/London
         - HA_IPAPER_GENERAL__homeassistant_url=http://homeassistant.local:8123
         - HA_IPAPER_GENERAL__homeassistant_token=YOUR_LONG_LIVED_ACCESS_TOKEN_HERE
       volumes:
         - /data/ha-ipaper:/config
       ports:
         - 8081:8081
       restart: unless-stopped
   ```
2. Replace the Home Assistant URL and token with your values.
3. In the same folder, start the container in the background: `docker compose up -d`.

#### Open the dashboard

On your e-reader, open `http://<ip-of-the-docker-machine>:8081/`.
This is the IP of the machine that runs Docker, not the IP of Home Assistant (unless both are the same machine).

#### Configuration file

- On first start, the container creates `config.yaml` in the folder mounted on `/config`.
  With the examples above, this is `/data/ha-ipaper/config.yaml` on the Docker machine.
- After you edit it, restart the container: `docker restart ha-ipaper`. You do not need to rebuild anything.
- The `HA_IPAPER_GENERAL__...` environment variables override the same values in `config.yaml`.

#### Change the port

Change only the left part of the port mapping, for example `-p 8122:8081` or `- 8122:8081`, then open `http://<ip>:8122/`.
Do not change `bind_port` in `config.yaml`: it is the port inside the container, and the mapping must point to it.

#### Troubleshooting

- `docker ps` must list `ha-ipaper` as `Up`. If not, the container stopped at start.
- `docker logs ha-ipaper` shows why: wrong `config.yaml`, Home Assistant URL not reachable, wrong token, ...
- If the page shows an error instead of the dashboard, check the Home Assistant URL and token.
  The URL must be reachable from the Docker machine. Use an IP (`http://192.168.x.y:8123`) if `homeassistant.local` does not resolve.

### Build from source with docker compose

```
git clone https://github.com/o0Zz/ha-ipaper.git
cd ha-ipaper
```

Edit the Home Assistant URL and token in `docker/docker-compose.yml`, then build and start:

```
docker compose -f docker/docker-compose.yml up -d --build
```

### Run with UV
```bash
uv sync
uv run python -m ha_ipaper -config config.yaml
```

Run the tests (they use a fake Home Assistant, no real instance needed):
```bash
uv run pytest
```

## Configuration

### Home Assistant Setup

#### Option 1: From environment variable

 - In your `docker run` command or `docker-compose.yml` (see [Docker](#docker-any-machine-with-docker)), set:
```
      - HA_IPAPER_GENERAL__homeassistant_url=http://homeassistant.local:8123
      - HA_IPAPER_GENERAL__homeassistant_token=YOUR_LONG_LIVED_ACCESS_TOKEN_HERE
```

#### Option 2: From config.yaml file

Edit config.yaml with your Home Assistant details:

```yaml
general:
 homeassistant_url: http://homeassistant.local:8123
 homeassistant_token: YOUR_LONG_LIVED_ACCESS_TOKEN
```

- **homeassistant_url:** The URL of your Home Assistant instance.
- **homeassistant_token:** A long-lived access token for Home Assistant access. To create a token:
  - Log into your Home Assistant.
  - Go to your profile.
  - Select the "Security" tab.
  - At the bottom, under "Long-lived access tokens," click "CREATE TOKEN."
  - Name the token (e.g., "HA-IPaper") and confirm.

### Menu Configuration (Optional)

Customize the pages you need by modifying the menu section in config.yaml to filter and arrange items for your dashboard.

```yaml
menu:
    - name: "Home"
      icon: "webfonts/regular.svg?id=house"
      components: ["components/forecast.html", "components/sensors.html"]
      
```

## Customization (Optional)
### Template Override

You can customize templates without modifying the original application files by using multiple template folders. The first folder in the list has the highest priority.

1. Create a custom template folder (e.g., `./html-templates`)
2. Add it to your `config.yaml`:
   ```yaml
   general:
     html_templates:
       - "./config/html-templates"
   ```
3. Create only the files you want to override, using the same folder structure:
   ```
   html-templates/
   ├── components/
   │   └── lights.html    # Overrides default lights component
   └── style.css          # Overrides default stylesheet
   ```

Instead of starting from scratch, it's advice to copy/paste the default html-templates provided here: https://github.com/o0Zz/ha-ipaper/tree/main/src/ha_ipaper/html-template

### User Interface

The interface includes a "ready-to-use" design. If customization is desired, you may modify HTML files in the html-template directory (Created above).

**html-template Structure:**

- `index.html`: The main entry point, loading CSS, menu, and pages.
- `components/*.html`: Contains reusable components for pages.

#### Architecture Overview

```plaintext
index.html
 ┌───────────────────────────────┐
 │ ┌───────────────────────────┐ │
 │ │                           │ │
 │ │      Menu (From YAML)     │ │
 │ │                           │ │
 │ └───────────────────────────┘ │
 │ ┌───────────────────────────┐ │
 │ │ ┌──────────────────────┐  │ │
 │ │ │   component/*.html   │  │ │
 │ │ └──────────────────────┘  │ │
 │ └───────────────────────────┘ │
 └───────────────────────────────┘
```

### Components

Add components as needed. 
Use the `entities` variable, which contains a snapshot of your Home Assistant’s state.

For interactions with your Home Assistant, create a POST form where inputs align with Home Assistant’s service API:

Example:
This example with set the climate `my_climate_xxx` to 10 degree.
```html
<form method="POST"> 
    <input type="hidden" name="service" value="climate.set_temperature"> 
    <input type="hidden" name="entity_id" value="climate.my_climate_xxx"> 
    <button type="submit" name="temperature" value="10"> 
</form> 
``` 

Consult Home Assistant documentation for available services: 
- [Climate](https://www.home-assistant.io/integrations/climate) 
- [Switch](https://www.home-assistant.io/integrations/switch) 
- [Light](https://www.home-assistant.io/integrations/light) 
- [Cover](https://www.home-assistant.io/integrations/cover)  

### Project inspired by: 
- [Tombo1337's hatki](https://github.com/tombo1337/hatki) 
- [Viny182's KFloorP](https://github.com/viny182/KFloorP)
