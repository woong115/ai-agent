"""Gunicorn 설정 파일."""

import os

bind = "0.0.0.0:5000"
workers = os.environ.get('GUNICORN_WORKER_COUNT', 3)
timeout = 60
worker_class = "uvicorn.workers.UvicornWorker"
keepalive = 5
