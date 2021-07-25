FROM python:3.8.5-alpine3.12

MAINTAINER Ondrej Tom <info@ondratom.cz>

RUN apk add --update bash gcc musl-dev libffi libffi-dev libxml2 libxml2-dev libxslt libxslt-dev curl openssh openssl openssl-dev

COPY ./requirements.txt /requirements.txt

RUN pip install --upgrade -r /requirements.txt

COPY . /app

WORKDIR /app

CMD ["python3", "-u", "run.py"]