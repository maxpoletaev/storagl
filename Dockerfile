FROM python:3.5-alpine

ADD storage /storage
ADD entrypoint.sh requirements.txt /

RUN pip install -r /requirements.txt

EXPOSE 8000
ENTRYPOINT ["/entrypoint.sh"]
