from prometheus_client import Counter, Histogram, Gauge, start_http_server
import time

# Define metrics
ideas_processed = Counter('ideas_processed_total', 'Total ideas processed')
ideas_failed = Counter('ideas_failed_total', 'Total ideas failed')
processing_time = Histogram('processing_time_seconds', 'Time to process idea')
queue_depth = Gauge('queue_depth', 'Current queue depth')
active_pods = Gauge('active_pods', 'Number of active pods')

class MetricsCollector:
    @staticmethod
    def record_idea_processed(success: bool, duration: float):
        if success:
            ideas_processed.inc()
        else:
            ideas_failed.inc()
        processing_time.observe(duration)
    
    @staticmethod
    def update_queue_depth(depth: int):
        queue_depth.set(depth)
    
    @staticmethod
    def update_active_pods(count: int):
        active_pods.set(count)

# Start Prometheus metrics server
start_http_server(9090)