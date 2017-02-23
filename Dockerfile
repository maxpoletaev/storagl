FROM python:3.5-alpine
WORKDIR /app

ADD entrypoint.sh requirements.txt ./
RUN pip install -r requirements.txt
ADD storagl/ storagl/

EXPOSE 8000
ENTRYPOINT ["/app/entrypoint.sh"]
