FROM python:3.11-slim-trixie

RUN apt-get update
RUN pip install pipenv

ADD Pipfile /ha-ipaper/Pipfile
WORKDIR /ha-ipaper
RUN pipenv install

COPY ha-ipaper /ha-ipaper
COPY html-template /html-template

ENV PYTHONPATH="/"
CMD [ "pipenv", "run", "python", "-m", "ha-ipaper", "-config", "/config/config.yaml" ]
