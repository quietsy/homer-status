FROM python:slim

RUN mkdir -p /config
WORKDIR /config

COPY requirements.txt /config
RUN pip install -v -r requirements.txt
COPY . /config

ENV FLASK_APP app.py

CMD flask run --host=0.0.0.0
