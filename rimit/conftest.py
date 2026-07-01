"""pytest configuration for RIMIT B2B Aggregator."""
import os
import django
from django.conf import settings

# Force test settings BEFORE pytest-django configures anything
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')


def pytest_configure(config):
    django.setup()
    # Disable migrations for speed (create tables directly from models)
    class DisableMigrations:
        def __contains__(self, item):
            return True

        def __getitem__(self, item):
            return None

    settings.MIGRATION_MODULES = DisableMigrations()

    # Force Celery into eager mode for tests (defensive — settings.dev already sets this)
    from config.celery import app as celery_app
    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = True
    celery_app.conf.broker_url = 'memory://'
    celery_app.conf.result_backend = 'cache+memory://'


import pytest
from django.test.utils import setup_test_environment, teardown_test_environment


@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker):
    """Use the default test database."""
    pass
