import os

from psycogreen.gevent import patch_psycopg

# Copied from data-hub-leeloo/config/gunicorn.py
# Worker class and gevent set-up

worker_class = os.environ.get('GUNICORN_WORKER_CLASS', 'gevent')
worker_connections = os.environ.get('GUNICORN_WORKER_CONNECTIONS', '10')

_enable_async_psycopg2 = (
    os.environ.get('GUNICORN_ENABLE_ASYNC_PSYCOPG2', 'true').lower() in ('true', '1')
)


def post_fork(server, worker):
    """
    Called just after a worker has been forked.

    Enables async processing in Psycopg2 if GUNICORN_ENABLE_ASYNC_PSYCOPG2 is set.
    """
    if worker_class == 'gevent' and _enable_async_psycopg2:
        patch_psycopg()
        worker.log.info('Enabled async Psycopg2')
