from prometheus_client import Counter, Histogram, Gauge, start_http_server
import time
import logging

logger = logging.getLogger(__name__)

ideas_processed = Counter(
    'ideas_processed_total',
    'Total number of ideas processed',
    ['status']
)

ideas_failed = Counter(
    'ideas_failed_total',
    'Total number of ideas that failed',
    ['phase']
)

processing_time = Histogram(
    'processing_time_seconds',
    'Time taken to process an idea',
    buckets=[60, 300, 900, 1800, 3600]
)

queue_depth = Gauge(
    'queue_depth',
    'Current number of ideas in queue'
)

active_workers = Gauge(
    'active_workers',
    'Number of active worker processes'
)

phase_duration = Histogram(
    'phase_duration_seconds',
    'Duration of each workflow phase',
    ['phase'],
    buckets=[10, 30, 60, 180, 300, 600]
)


class MetricsCollector:
    """Centralized metrics collection."""

    @staticmethod
    def record_idea_processed(success: bool, duration: float, status: str = "completed"):
        """Record that an idea was processed."""
        try:
            ideas_processed.labels(status=status).inc()
            processing_time.observe(duration)
            logger.debug(f"Recorded idea processed: {status}, duration: {duration}s")
        except Exception as e:
            logger.error(f"Failed to record metrics: {e}")

    @staticmethod
    def record_idea_failed(phase: str):
        """Record that an idea failed at a specific phase."""
        try:
            ideas_failed.labels(phase=phase).inc()
            logger.debug(f"Recorded idea failed at phase: {phase}")
        except Exception as e:
            logger.error(f"Failed to record failure metric: {e}")

    @staticmethod
    def update_queue_depth(depth: int):
        """Update the current queue depth."""
        try:
            queue_depth.set(depth)
        except Exception as e:
            logger.error(f"Failed to update queue depth: {e}")

    @staticmethod
    def update_active_workers(count: int):
        """Update the number of active workers."""
        try:
            active_workers.set(count)
        except Exception as e:
            logger.error(f"Failed to update active workers: {e}")

    @staticmethod
    def record_phase_duration(phase: str, duration: float):
        """Record the duration of a specific phase."""
        try:
            phase_duration.labels(phase=phase).observe(duration)
            logger.debug(f"Recorded phase {phase} duration: {duration}s")
        except Exception as e:
            logger.error(f"Failed to record phase duration: {e}")


def start_metrics_server(port: int = 9090):
    """Start Prometheus metrics server."""
    try:
        start_http_server(port)
        logger.info(f"Metrics server started on port {port}")
    except Exception as e:
        logger.error(f"Failed to start metrics server: {e}")
