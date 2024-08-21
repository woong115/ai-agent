#!/bin/sh
set -e

if [ "$1" = 'gunicorn' ]; then
    shift
    exec gunicorn app.main:app \
        --config=gunicorn.conf.py \
        "$@"
elif [ "$1" = 'load_vectorstore' ]; then
    shift
    exec python app/init_vectorstore.py
elif [ "$1" = 'demo' ]; then
    shift
    exec streamlit run app/demo.py
else
    exec "$@"
fi
