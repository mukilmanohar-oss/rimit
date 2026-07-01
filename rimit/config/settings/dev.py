"""Development settings - SQLite, debug enabled, relaxed CORS."""
from .base import *  # noqa

DEBUG = True
ALLOWED_HOSTS = ['*', 'localhost', '127.0.0.1']

# Use eager Celery (sync) for tests
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_BROKER_URL = 'memory://'
CELERY_RESULT_BACKEND = 'cache+memory://'
CELERY_TASK_ACKS_LATE = False  # eager mode doesn't need acks
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = False

# CORS wide open for local dev
CORS_ALLOW_ALL_ORIGINS = True

# Speed up password hashing in tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Disable rate limiting in dev/test
REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {'user': None, 'anon': None}
