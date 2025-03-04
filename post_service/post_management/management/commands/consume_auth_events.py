from django.core.management.base import BaseCommand
import pika
import json
from django.core.cache import cache
from decouple import config

RABBITMQ_URL = config("CLOUDAMQP_URL")

class Command(BaseCommand):
    help = "Starts RabbitMQ consumer for authentication events"

    def handle(self, *args, **kwargs):
        def callback(ch, method, properties, body):
            message = json.loads(body)
            print(f"Received authentication event: {message}")

            # Process the received event by performing any necessary action.
            # In this case, we store the user authentication event in cache (e.g., for 5 minutes).
            user_id = message.get("user_id")
            if user_id:
                cache.set(f"user_auth_{user_id}", True, timeout=300)

            ch.basic_ack(delivery_tag=method.delivery_tag)

        params = pika.URLParameters(RABBITMQ_URL)
        connection = pika.BlockingConnection(params)
        channel = connection.channel()

        channel.queue_declare(queue="auth_events", durable=True)
        channel.basic_consume(queue="auth_events", on_message_callback=callback)

        print("Waiting for messages...")
        channel.start_consuming()
