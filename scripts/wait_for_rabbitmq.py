"""Wait for RabbitMQ to be ready, then exit."""
import sys
import time

from kombu import Connection

url = sys.argv[1] if len(sys.argv) > 1 else "amqp://shipping:shipping_secret@rabbitmq:5672//"

for i in range(30):
    try:
        with Connection(url) as conn:
            conn.ensure_connection(max_retries=1)
            print("rabbitmq ready")
            sys.exit(0)
    except Exception as e:
        print(f"waiting for rabbitmq ({i+1}/30): {e}")
        time.sleep(1)

print("rabbitmq not ready after 30s")
sys.exit(1)
