FROM python:3

RUN pip install kubernetes
ENV PYTHONUNBUFFERED=0
COPY . /app
WORKDIR /app
