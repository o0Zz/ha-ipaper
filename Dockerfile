FROM python:3.10-slim-buster

RUN echo "deb http://deb.debian.org/debian buster-backports main" >> /etc/apt/sources.list
RUN apt-get update
RUN pip install pipenv

ADD Pipfile /ha-ipaper/Pipfile
WORKDIR /ha-ipaper
RUN pipenv install

COPY ha-ipaper /ha-ipaper
COPY html-template /html-template

ENV PYTHONPATH="${PYTHONPATH}:/"
CMD [ "pipenv", "run", "python", "-m", "ha-ipaper", "-config", "/config/config.yaml" ]
