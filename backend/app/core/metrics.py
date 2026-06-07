"""
CloudWatch custom metrics publisher.

Publishes HTTP status-class counters and latency to the
TradingAgent/API namespace. Runs in a background thread so
metric API calls never block request handling.

On non-AWS environments (local dev) boto3 will raise
NoCredentialsError — we catch it and degrade gracefully.

CloudWatch console path:
  Metrics → Custom namespaces → TradingAgent/API
"""
from __future__ import annotations

import logging
import threading
from collections import defaultdict
from datetime import datetime, timezone
from queue import Empty, Queue

logger = logging.getLogger(__name__)

_NAMESPACE = "TradingAgent/API"
_FLUSH_INTERVAL_SEC = 60   # batch publish every minute


class MetricsPublisher:
    """
    Thread-safe CloudWatch metrics aggregator and publisher.

    Aggregates counts in-process, then flushes to CloudWatch
    every _FLUSH_INTERVAL_SEC seconds in a daemon thread.

    Usage:
        metrics_publisher.record_request(status_code=200, latency_ms=45.2, path="/api/v1/screener/ranked")
    """

    def __init__(self) -> None:
        self._queue: Queue[dict] = Queue(maxsize=10_000)
        self._lock  = threading.Lock()
        self._counts: defaultdict[str, int] = defaultdict(int)   # status_class → count
        self._latencies: defaultdict[str, list[float]] = defaultdict(list)
        self._started = False
        self._client = None

    def start(self) -> None:
        """Start the background flush thread. Call once at app startup."""
        if self._started:
            return
        self._started = True
        t = threading.Thread(target=self._flush_loop, daemon=True, name="cw-metrics-flusher")
        t.start()
        logger.info("CloudWatch metrics publisher started (namespace=%s)", _NAMESPACE)

    def record_request(self, status_code: int, latency_ms: float, path: str) -> None:
        """Non-blocking: enqueue a metric point. Drops silently if queue is full."""
        cls = self._status_class(status_code)
        try:
            self._queue.put_nowait({"class": cls, "latency": latency_ms, "path": path})
        except Exception:  # noqa: BLE001
            pass  # Queue full — drop metric, never block a request

    # ── private ───────────────────────────────────────────────────────────────

    def _flush_loop(self) -> None:
        import time
        while True:
            time.sleep(_FLUSH_INTERVAL_SEC)
            self._drain_queue()
            self._publish()

    def _drain_queue(self) -> None:
        """Move all queued events into in-memory aggregates."""
        while True:
            try:
                point = self._queue.get_nowait()
                with self._lock:
                    self._counts[point["class"]] += 1
                    self._latencies[point["class"]].append(point["latency"])
            except Empty:
                break

    def _publish(self) -> None:
        with self._lock:
            counts    = dict(self._counts)
            latencies = {k: list(v) for k, v in self._latencies.items()}
            self._counts.clear()
            self._latencies.clear()

        if not counts:
            return

        try:
            client = self._get_client()
            if client is None:
                return

            metric_data = []
            ts = datetime.now(timezone.utc)

            for cls, count in counts.items():
                metric_data.append({
                    "MetricName": "RequestCount",
                    "Dimensions": [{"Name": "StatusClass", "Value": cls}],
                    "Value": count,
                    "Unit": "Count",
                    "Timestamp": ts,
                })

            for cls, lats in latencies.items():
                metric_data.append({
                    "MetricName": "RequestLatency",
                    "Dimensions": [{"Name": "StatusClass", "Value": cls}],
                    "StatisticValues": {
                        "SampleCount": len(lats),
                        "Sum":         sum(lats),
                        "Minimum":     min(lats),
                        "Maximum":     max(lats),
                    },
                    "Unit": "Milliseconds",
                    "Timestamp": ts,
                })

            # CloudWatch accepts max 20 metric data points per call
            for i in range(0, len(metric_data), 20):
                client.put_metric_data(
                    Namespace=_NAMESPACE,
                    MetricData=metric_data[i: i + 20],
                )

            logger.debug("CloudWatch metrics flushed: %s", counts)

        except Exception as exc:  # noqa: BLE001
            # Silently degrade — metric failure must never affect the API
            logger.debug("CloudWatch publish skipped: %s", exc)

    def _get_client(self):
        """Lazily create boto3 client. Returns None outside AWS."""
        if self._client is not None:
            return self._client
        try:
            import boto3
            self._client = boto3.client("cloudwatch", region_name="us-east-1")
            return self._client
        except Exception:  # noqa: BLE001
            return None

    @staticmethod
    def _status_class(code: int) -> str:
        if code < 300:   return "2xx"
        if code < 400:   return "3xx"
        if code < 500:   return "4xx"
        return "5xx"


metrics_publisher = MetricsPublisher()
