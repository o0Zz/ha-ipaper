# ha-ipaper
Home Assitant interactive e-paper dashboard (For Kobo, Kindle, ...)

## Quick start

### Docker version
```
docker run 
```

### Python version

Edit config.yaml in order to setup you homeassistant token and homeassistant url

```
pipenv install
pipenv run python -m ha-ipaper -config config.yaml
```

### Customization

The interface come with a "ready-to-use" interface, however if you want to customize the interface for your need feel free to edit the html files.
It's strongly advice to not change other part of the projet. Most of time your html file should be compatible from one version to another

Everything is in html-template

 - menu.html is the top menu
 - home.html contains the list of element your want
 
If some pages do not meet your needs it's advice to create new pages and new components - Do not hesitate to share it with others :)

 components/ contains generic component that may be include in various pages
 page mainly contains compoenent
  
Here is the architecure
 
```
            index.html               
 ┌────────────────────────────────┐  
 │  ┌───────────────────────────┐ │  
 │  │                           │ │  
 │  │      menu(From yaml)      │ │  
 │  │                           │ │  
 │  └───────────────────────────┘ │  
 │  ┌───────────────────────────┐ │  
 │  │      pages/*.html         │ │  
 │  │                           │ │  
 │  │ ┌──────────────────────┐  │ │  
 │  │ │   component/*.html   │  │ │  
 │  │ │                      │  │ │  
 │  │ └──────────────────────┘  │ │  
 │  │ ┌──────────────────────┐  │ │  
 │  │ │   component/*.html   │  │ │  
 │  │ │                      │  │ │  
 │  │ └──────────────────────┘  │ │  
 │  │ ┌──────────────────────┐  │ │  
 │  │ │   component/*.html   │  │ │  
 │  │ │                      │  │ │  
 │  │ └──────────────────────┘  │ │  
 │  │                           │ │  
 │  │                           │ │  
 │  └───────────────────────────┘ │  
 └────────────────────────────────┘  
```

### References
This project has been inspried by:

https://github.com/tombo1337/hatki
https://github.com/viny182/KFloorP