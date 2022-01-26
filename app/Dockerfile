# BUILDER

FROM python:3.9.6-alpine as builder

WORKDIR /usr/src/app

RUN apk --update --upgrade add build-base
RUN pip install --upgrade pip
COPY ./requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /usr/src/app/wheels -r requirements.txt


# FINAL

FROM python:3.9.6-alpine

RUN apk --update --upgrade add build-base libffi-dev
COPY --from=builder /usr/src/app/wheels /wheels
RUN pip install --no-cache /wheels/*

ENV HOME=/home/app
ENV APP_HOME=/home/app/app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN mkdir -p /home/app
RUN addgroup -S app && adduser -S app -G app
RUN mkdir $APP_HOME

WORKDIR $APP_HOME
COPY . $APP_HOME

RUN chown -R app:app $APP_HOME
RUN mkdir $HOME/auth && chown app:app $HOME/auth

USER app
