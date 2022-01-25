FROM python:3.9.6-alpine

WORKDIR /usr/src/app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apk --update --upgrade add build-base libffi-dev
RUN pip install --upgrade pip
COPY . .
RUN pip install -r requirements.txt
