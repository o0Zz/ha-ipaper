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

### Build & run from docker
```
docker build -f docker/Dockerfile -t ha-ipaper:latest .
```

Edit `docker/docker-compose.yml`

```
docker compose up
```

### Run with UV
```bash
uv sync
uv run python -m ha_ipaper -config config.yaml
```

## Configuration

### Home Assistant Setup

#### Option 1: From environment variable

 - Edit `docker/docker-compose.yaml`
 - Update environment variables:
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
