"""Initialize RabbitMQ queues and bindings for Celery tasks."""
from src.common.messaging.celery_app import celery_app

if __name__ == "__main__":
    with celery_app.connection_for_write() as conn:
        celery_app.amqp.create_task_consumer(conn).consume()
        print("queues declared and bound")
