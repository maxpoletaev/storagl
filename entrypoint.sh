#!/bin/sh

manage() {
    python storage/app.py $@
}

run() {
    manage migrate
    /usr/local/bin/gunicorn storage.app --bind 0.0.0.0:8000
}

if [ "$1" = "" ]; then
    run
else
    manage $@
fi
