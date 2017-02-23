FROM python:3.5-alpine
WORKDIR /app

ADD storagl entrypoint.sh requirements.txt ./
RUN pip install -r requirements.txt

EXPOSE 8000
ENTRYPOINT ["/app/entrypoint.sh"]
