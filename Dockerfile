FROM python:slim

RUN mkdir -p /app
WORKDIR /app

COPY requirements.txt /app
RUN pip install -v -r requirements.txt
COPY . /app

RUN chmod +x /app/entrypoint.sh
ENTRYPOINT ["/app/entrypoint.sh"]
