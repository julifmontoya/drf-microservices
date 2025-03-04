import pika
import json
from decouple import config
from django.core.cache import cache
import os
import django



RABBITMQ_URL = config("CLOUDAMQP_URL")

def callback(ch, method, properties, body):
    message = json.loads(body)
    print(f"Received authentication event: {message}")

    # Process the received event by performing any necessary action.
    # In this case, we store the user authentication event in cache (e.g., for 5 minutes).
    user_id = message.get("user_id")
    if user_id:
        # Store user authentication event in cache (e.g., for 5 minutes)
        cache.set(f"user_auth_{user_id}", True, timeout=300)

    ch.basic_ack(delivery_tag=method.delivery_tag)  # Acknowledge message

def consume_auth_events():
    params = pika.URLParameters(RABBITMQ_URL)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    
    channel.queue_declare(queue="auth_events", durable=True)
    channel.basic_consume(queue="auth_events", on_message_callback=callback)

    print("Waiting for messages...")
    channel.start_consuming()

consume_auth_events()
