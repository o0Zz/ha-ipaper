FROM python:3.10-slim-buster

RUN echo "deb http://deb.debian.org/debian buster-backports main" >> /etc/apt/sources.list
RUN apt-get update
RUN pip install pipenv

COPY ha-ipaper /ha-ipaper
ADD Pipfile /ha-ipaper

WORKDIR /ha-ipaper
RUN pipenv install

ENV PYTHONPATH="${PYTHONPATH}:/"
CMD [ "pipenv", "run", "python", "-m", "ha-ipaper", "-config", "/config/config.yaml" ]
