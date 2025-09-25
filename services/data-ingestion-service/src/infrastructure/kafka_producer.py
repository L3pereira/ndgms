"""Kafka producer for disaster events."""

import json
import logging
import os
from typing import Any

from aiokafka import AIOKafkaProducer
from prometheus_client import Counter, Histogram

from ..domain.disaster_event import DisasterType, ProcessedDisasterEvent, RawDisasterData

logger = logging.getLogger(__name__)

# Prometheus metrics
kafka_messages_sent = Counter(
    'kafka_messages_sent_total',
    'Total Kafka messages sent',
    ['topic', 'disaster_type', 'status']
)

kafka_send_duration = Histogram(
    'kafka_message_send_duration_seconds',
    'Time spent sending Kafka messages',
    ['topic']
)


class DisasterEventProducer:
    """Kafka producer for disaster events."""

    def __init__(self, bootstrap_servers: str | None = None):
        env_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
        self.bootstrap_servers = bootstrap_servers or env_servers or "localhost:9092"
        logger.info(f"Kafka bootstrap servers: env_var='{env_servers}', using='{self.bootstrap_servers}'")
        self.producer: AIOKafkaProducer | None = None

    async def start(self):
        """Start the Kafka producer."""
        try:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                enable_idempotence=True,  # Prevent duplicate messages
                acks='all'  # Wait for all replicas to acknowledge
            )
            await self.producer.start()
            logger.info(f"Kafka producer started, connected to {self.bootstrap_servers}")
        except Exception as e:
            logger.error(f"Failed to start Kafka producer: {e}")
            raise

    async def stop(self):
        """Stop the Kafka producer."""
        if self.producer:
            await self.producer.stop()
            logger.info("Kafka producer stopped")

    async def publish_raw_data(self, raw_data: RawDisasterData) -> None:
        """Publish raw disaster data to Kafka."""
        if not self.producer:
            raise RuntimeError("Producer not started")

        topic = f"disasters.raw.{raw_data.disaster_type.value}"

        message = {
            "data_id": raw_data.data_id,
            "disaster_type": raw_data.disaster_type.value,
            "external_id": raw_data.external_id,
            "source": raw_data.source,
            "ingested_at": raw_data.ingested_at.isoformat(),
            "raw_payload": raw_data.raw_payload
        }

        with kafka_send_duration.labels(topic=topic).time():
            try:
                await self.producer.send_and_wait(
                    topic=topic,
                    key=raw_data.external_id,
                    value=message
                )

                kafka_messages_sent.labels(
                    topic=topic,
                    disaster_type=raw_data.disaster_type.value,
                    status='success'
                ).inc()

                logger.debug(f"Published raw data to {topic}: {raw_data.external_id}")

            except Exception as e:
                kafka_messages_sent.labels(
                    topic=topic,
                    disaster_type=raw_data.disaster_type.value,
                    status='error'
                ).inc()
                logger.error(f"Failed to publish raw data to {topic}: {e}")
                raise

    async def publish_processed_event(self, event: ProcessedDisasterEvent) -> None:
        """Publish processed disaster event to Kafka."""
        if not self.producer:
            raise RuntimeError("Producer not started")

        topic = f"disasters.processed.{event.disaster_type.value}"

        message = {
            "event_id": event.event_id,
            "disaster_type": event.disaster_type.value,
            "location": {
                "latitude": event.location.latitude,
                "longitude": event.location.longitude,
                "depth": event.location.depth
            },
            "severity": {
                "value": event.severity.value,
                "scale": event.severity.scale,
                "level": event.severity.get_level().value,
                "is_significant": event.severity.is_significant()
            },
            "occurred_at": event.occurred_at.isoformat(),
            "processed_at": event.processed_at.isoformat(),
            "source": event.source,
            "external_id": event.external_id,
            "title": event.title,
            "metadata": event.metadata
        }

        with kafka_send_duration.labels(topic=topic).time():
            try:
                await self.producer.send_and_wait(
                    topic=topic,
                    key=event.external_id or event.event_id,
                    value=message
                )

                kafka_messages_sent.labels(
                    topic=topic,
                    disaster_type=event.disaster_type.value,
                    status='success'
                ).inc()

                logger.debug(f"Published processed event to {topic}: {event.event_id}")

            except Exception as e:
                kafka_messages_sent.labels(
                    topic=topic,
                    disaster_type=event.disaster_type.value,
                    status='error'
                ).inc()
                logger.error(f"Failed to publish processed event to {topic}: {e}")
                raise

    async def create_topics_if_needed(self, disaster_types: list[DisasterType]) -> None:
        """Create Kafka topics for disaster types if they don't exist."""
        # In production, topics should be pre-created by operations team
        # This is for development convenience
        topics_to_create = []

        for disaster_type in disaster_types:
            topics_to_create.extend([
                f"disasters.raw.{disaster_type.value}",
                f"disasters.processed.{disaster_type.value}"
            ])

        logger.info(f"Topics will be auto-created by Kafka: {topics_to_create}")
