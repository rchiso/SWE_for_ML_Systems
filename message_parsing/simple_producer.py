#!/usr/bin/env python3

import pika
import sys

RABBIT_HOST = "localhost"
QUEUE_NAME  = "main_queue"

def main():
    # 1. Connect to RabbitMQ
    connection_params = pika.ConnectionParameters(host=RABBIT_HOST)
    connection = pika.BlockingConnection(connection_params)
    channel = connection.channel()

    # 3. Build your message (either from sys.argv or hard-coded)
    message = " ".join(sys.argv[1:]) or "Hello RabbitMQ!"
    
    # 4. Publish the message to the queue
    channel.basic_publish(
        exchange="",
        routing_key=QUEUE_NAME,
        body=message.encode("utf-8"),
        properties=pika.BasicProperties(
            delivery_mode=2  # make message persistent
        )
    )
    print(f"[producer] Sent message: {message}")

    # 5. Close the connection
    connection.close()

if __name__ == "__main__":
    main()