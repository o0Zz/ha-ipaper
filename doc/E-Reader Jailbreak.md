# E-Reader Jailbreak & Kiosk Mode Compatibility

This document lists **Kindle** and **Kobo** e-readers that can be jailbroken or configured for fullscreen / kiosk-style usage, along with compatible firmware versions and useful tools.



## Kindle

### Overview
A jailbroken Kindle is **preferred** (but not always required) to:
- Disable the native screensaver
- Enable true fullscreen browser usage
- Prevent deep sleep
- Run the device in **full kiosk mode**

### Jailbreak / Kiosk Reference
- Kindle Kiosk / Fullscreen Hack  
  https://www.mobileread.com/forums/showthread.php?t=346037

> You **must** use the exploit payload that matches your **exact device + firmware combination**.


### List of devices/firmware that support jailbreak
**KT3, KT4, KOA1, KOA2, KOA3, PW3, PW4, PW5**
- 5.14.2
- 5.14.1 (5.14.1.1 on PW5)
- 5.13.7
- 5.13.6
- 5.13.5
- 5.13.4

**KV**
- 5.13.6
- 5.13.5
- 5.13.4

**KT2, PW2**
- 5.12.2.2


### Fullscreen Browser / Web Launch
- WebLaunch (Fullscreen Browser)  
  https://github.com/PaulFreund/WebLaunch

- Disable deep sleep:
```
~ds
```

### Useful References & Projects
- Home Assistant + E-Ink dashboards  
  https://community.home-assistant.io/t/use-esphome-with-e-ink-displays-to-blend-in-with-your-home-decor/435428

- Hatki  
  https://github.com/tombo1337/hatki

- KFloorP  
  https://github.com/viny182/KFloorP/tree/main

### Kindle Hardware Comparison

- https://en.wikipedia.org/wiki/Amazon_Kindle

| Model | RAM | Screen |
|------|-----|--------|
| Kindle 4 / PW1 / PW2 | 256 MB | 6\" |
| PW3 | 512 MB | 6\" |




## Kobo

### Device Comparison
- https://comparisontabl.es/kobo-e-readers/

#### Notable Models
- **Kobo Clara HD** — 6\", 2018  
- **Kobo Aura H2O** — 6.8\", 2014 (Edition 2: 2017)


### Kobo Browser & Developer Configuration

- https://www.mobileread.com/forums/showthread.php?t=256343

### Enable Developer Mode & Fullscreen

Edit `Kobo eReader.conf`:

```
[PowerOptions]
AutoOffMinutes=0
AutoSleepMinutes=0
FrontLightLevel=10
FullscreenCoverInfoPanel=true
FullscreenCoverStretch=true
ShowBookCover=true
SleepAccessoryEnabled=true
```

```
[FeatureSettings]
FullScreenReading=true
```

## Notes

- Kindle firmware auto-updates can break jailbreaks.
- Kobo devices are generally more permissive.
- E-ink browsers have limited CSS/JS support.
