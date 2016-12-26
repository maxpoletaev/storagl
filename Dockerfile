FROM python:3.5-alpine

ADD storage /storage
ADD entrypoint.sh /
ADD requirements.txt /

RUN pip install -r /requirements.txt
RUN pip install gunicorn

VOLUME /data

EXPOSE 8000
ENTRYPOINT ["/entrypoint.sh"]
