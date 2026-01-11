FROM python:3.11-slim-trixie

RUN apt-get update
RUN pip install uv

WORKDIR /ha-ipaper
COPY pyproject.toml uv.lock /ha-ipaper/
COPY ha-ipaper /ha-ipaper/ha-ipaper
COPY html-template /html-template

RUN uv sync --frozen

CMD [ "uv", "run", "ha-ipaper", "-config", "/config/config.yaml" ]
