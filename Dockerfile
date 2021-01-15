FROM python:3.5
ENV PYTHONUNBUFFERED 1

ADD requirements /requirements

WORKDIR /app
ADD . /app
RUN pip install -r requirements/dev.txt