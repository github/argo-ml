FROM python:3

RUN pip install kubernetes Flask
ENV PYTHONUNBUFFERED=0
COPY . /app
WORKDIR /app
