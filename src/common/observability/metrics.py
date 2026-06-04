from prometheus_client import Counter, Histogram, Gauge, generate_latest

email_received = Counter("emails_received_total", "Total emails received", ["source"])
email_processed = Counter("emails_processed_total", "Total emails processed", ["status"])
email_bytes = Histogram("email_bytes", "Email size bytes", buckets=[1024, 10240, 102400, 1048576, 10485760])
processing_duration = Histogram(
    "processing_duration_seconds",
    "Processing duration by step",
    ["step"],
    buckets=[0.01, 0.1, 0.5, 1.0, 5.0, 30.0, 120.0],
)
active_tasks = Gauge("active_tasks", "Currently active tasks", ["queue"])
db_pool_size = Gauge("db_pool_size", "Database pool size")
queue_depth = Gauge("queue_depth", "Queue depth", ["queue"])


def get_metrics() -> bytes:
    return generate_latest()
