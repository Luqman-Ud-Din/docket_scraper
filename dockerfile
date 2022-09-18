FROM python:3.10-slim

RUN apt-get update

RUN mkdir /app
WORKDIR /app

COPY ./requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt
RUN ls

COPY . /app
