#!/bin/sh

gunicorn=/usr/local/bin/gunicorn

manage_py() {
    python storagl/app.py $@
}

start_gunicorn() {
    manage_py migrate
    gunicorn storagl.app --bind 0.0.0.0:8000
}

if [ "$1" = "" ]; then
    start_gunicorn
else
    manage_py $@
fi
