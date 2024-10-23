from celery import Celery
from kombu.utils.url import maybe_sanitize_url

# Use separate Redis databases for broker and backend
redis_broker_url = 'redis://localhost:6379/0'
redis_backend_url = 'redis://localhost:6379/1'

celery_app = Celery(
    'tasks',
    broker=redis_broker_url,
    backend=redis_backend_url
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    broker_connection_retry_on_startup=True,
)

print(f"Celery is configured with broker: {maybe_sanitize_url(celery_app.conf.broker_url)}")
print(f"Celery is configured with backend: {maybe_sanitize_url(celery_app.conf.result_backend)}")
