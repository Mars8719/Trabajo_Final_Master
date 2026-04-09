"""
Kafka producer and consumer for SOC alert pipeline.
Topics: siem.alerts.raw, siem.alerts.anonymized, compliance.audit.pii, compliance.blocked.alerts
Falls back to no-op when confluent-kafka is not installed.
"""
import json
import structlog
from typing import Callable, Optional
from app.config import get_settings

logger = structlog.get_logger()
settings = get_settings()

try:
    from confluent_kafka import Producer, Consumer, KafkaError
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False
    logger.warning("confluent-kafka not installed — Kafka disabled (dev mode)")


class KafkaProducerClient:
    def __init__(self):
        self._producer = None
        if KAFKA_AVAILABLE:
            try:
                self._producer = Producer({
                    "bootstrap.servers": settings.KAFKA_BOOTSTRAP_SERVERS,
                    "client.id": "soc-llm-producer",
                    "acks": "all",
                })
            except Exception as e:
                logger.warning("Kafka producer init failed (will use no-op)", error=str(e))

    def _delivery_callback(self, err, msg):
        if err:
            logger.error("Kafka delivery failed", error=str(err), topic=msg.topic())
        else:
            logger.debug("Kafka message delivered", topic=msg.topic(), partition=msg.partition())

    async def produce(self, topic: str, value: dict, key: Optional[str] = None):
        if self._producer is None:
            logger.debug("Kafka no-op produce", topic=topic)
            return
        self._producer.produce(
            topic=topic,
            value=json.dumps(value).encode("utf-8"),
            key=key.encode("utf-8") if key else None,
            callback=self._delivery_callback,
        )
        self._producer.poll(0)

    def flush(self):
        if self._producer:
            self._producer.flush()


class KafkaConsumerClient:
    def __init__(self, topics: list[str], group_id: Optional[str] = None):
        self._consumer = None
        self._running = False
        if KAFKA_AVAILABLE:
            try:
                self._consumer = Consumer({
                    "bootstrap.servers": settings.KAFKA_BOOTSTRAP_SERVERS,
                    "group.id": group_id or settings.KAFKA_GROUP_ID,
                    "auto.offset.reset": "earliest",
                    "enable.auto.commit": False,
                })
                self._consumer.subscribe(topics)
            except Exception as e:
                logger.warning("Kafka consumer init failed", error=str(e))

    async def consume(self, callback: Callable, timeout: float = 1.0):
        if self._consumer is None:
            return
        self._running = True
        while self._running:
            msg = self._consumer.poll(timeout)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                logger.error("Kafka consumer error", error=msg.error())
                continue
            try:
                value = json.loads(msg.value().decode("utf-8"))
                await callback(value)
                self._consumer.commit(msg)
            except Exception as e:
                logger.error("Error processing Kafka message", error=str(e))

    def stop(self):
        self._running = False
        if self._consumer:
            self._consumer.close()


kafka_producer = KafkaProducerClient()
