#!/bin/sh
GUNICORN_WORKERS=${GUNICORN_WORKERS:-1}
GUNICORN_THREADS=${GUNICORN_THREADS:-10}
gunicorn=/usr/local/bin/gunicorn

manage_py() {
    python storagl/app.py $@
}

start_gunicorn() {
    manage_py migrate
    gunicorn storagl.app \
        --workers $GUNICORN_WORKERS \
        --threads $GUNICORN_THREADS \
        --bind 0.0.0.0:8000
}

if [ "$1" = "" ]; then
    start_gunicorn
else
    manage_py $@
fi
