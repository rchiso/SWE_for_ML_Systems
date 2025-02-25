import time
import functools
from prometheus_client import Counter, Histogram, Gauge, start_http_server

# Message processing metrics
MESSAGES_PROCESSED = Counter(
    "messages_processed_total", "Number of HL7 messages processed", ["message_type"]
)

PROCESSING_TIME = Histogram(
    "message_processing_seconds", "Time spent processing messages", ["message_type"]
)

# ML metrics
PREDICTIONS_MADE = Counter(
    "predictions_made_total", "Number of AKI predictions made", ["result"]
)

# Database metrics
DB_OPERATIONS = Counter(
    "database_operations_total", "Number of database operations", ["operation_type", "status"]
)

DB_OPERATION_TIME = Histogram(
    "database_operation_duration_seconds",
    "Time spent on database operations",
    ["operation_type"],
)

# Pager metrics
PAGER_REQUESTS = Counter(
    "pager_requests_total", "Number of pager requests sent", ["status"]
)

# Error monitoring metrics
ERROR_COUNTER = Counter(
    "application_errors_total",
    "Total number of application errors",
    ["error_type", "component"],
)

SOCKET_TIMEOUTS = Counter(
    "socket_timeouts", "Number of times the socket has timed out"
)

SIGTERM_COUNTER = Counter(
    "sigterm_counter", "Number of times the pod has received SIGTERM"
)

# System health metrics
SYSTEM_HEALTH = Gauge(
    "system_health_status", "Current health status of system components", ["component"]
)


def init_metrics(port=9090):
    """Initialize the Prometheus metrics server"""
    start_http_server(port)


def record_error(error_type: str, component: str):
    """Record an error occurrence"""
    ERROR_COUNTER.labels(error_type=error_type, component=component).inc()
    SYSTEM_HEALTH.labels(component=component).set(0)  # Mark component as unhealthy


def monitor_db_operation(operation_type):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                DB_OPERATIONS.labels(
                    operation_type=operation_type, status="success"
                ).inc()
                return result
            except Exception as e:
                DB_OPERATIONS.labels(
                    operation_type=operation_type, status="error"
                ).inc()
                record_error(error_type=str(e.__class__.__name__), component="database")
                raise
            finally:
                DB_OPERATION_TIME.labels(operation_type=operation_type).observe(
                    time.time() - start_time
                )

        return wrapper

    return decorator
