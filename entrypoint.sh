#!/bin/sh

gunicorn=/usr/local/bin/gunicorn

manage_py() {
    python storage/app.py $@
}

run() {
    manage_py migrate
    gunicorn storage.app --bind 0.0.0.0:8000
}

if [ "$1" = "" ]; then
    run
else
    manage $@
fi
