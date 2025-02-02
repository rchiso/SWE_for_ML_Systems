#!/usr/bin/env python3

import pika

RABBIT_HOST = "localhost"
QUEUE_NAME = "main_queue"

# TODO: implement message processing here
def process_message(body):
    """Pretend to parse + write to DB. Raise an exception sometimes for testing."""
    msg_str = body.decode("utf-8", errors="replace")
    print(f"[consumer] Processing message: {msg_str}")
    # Simulate random failure. For a real scenario, replace with actual logic.
    if "FAIL" in msg_str:
        raise ValueError("Simulated processing error: 'FAIL' found")
    # Otherwise it "succeeds"
    print("[consumer] Done processing.")

def callback(ch, method, properties, body):
    # Extract or initialize retry count from headers
    headers = properties.headers or {}
    retry_count = headers.get("x-retry-count", 0)

    try:
        process_message(body)
        # If success, ACK the message
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        # Something went wrong
        print(f"[consumer] Error processing message: {e}")
        
        if retry_count < 1:
            # 1) We'll republish the message with retry_count+1
            new_retry_count = retry_count + 1
            print(f"[consumer] Requeue attempt #{new_retry_count} ...")

            # Build new properties with updated headers
            new_headers = dict(headers)
            new_headers["x-retry-count"] = new_retry_count

            ch.basic_publish(
                exchange="",
                routing_key=QUEUE_NAME,
                body=body,
                properties=pika.BasicProperties(
                    headers=new_headers,
                    delivery_mode=2  # persistent
                )
            )

            # 2) ACK the old message, so it won't get stuck in a re-delivery loop
            ch.basic_ack(delivery_tag=method.delivery_tag)
        else:
            # Exceeded retry limit => send to DLQ by NACK w/ requeue=False
            print("[consumer] Retry limit exceeded, sending to Dead Letter Queue...")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def main():
    connection_params = pika.ConnectionParameters(host=RABBIT_HOST)
    connection = pika.BlockingConnection(connection_params)
    channel = connection.channel()

    # -- Declare DLX and DLQ (for dead letters) --
    DLX_NAME = "dlx_main"
    channel.exchange_declare(exchange=DLX_NAME, exchange_type="direct", durable=True)

    DLQ_NAME = "main_queue_dlx"
    channel.queue_declare(queue=DLQ_NAME, durable=True)
    channel.queue_bind(exchange=DLX_NAME, queue=DLQ_NAME, routing_key="dlx_routing_key")

    # -- Declare main queue with reference to DLX --
    channel.queue_declare(
        queue=QUEUE_NAME,
        durable=True,
        arguments={
            'x-dead-letter-exchange': DLX_NAME,
            'x-dead-letter-routing-key': 'dlx_routing_key'
        }
    )

    # Prefetch 1 for fairness
    channel.basic_qos(prefetch_count=1)

    # Set up consumer
    channel.basic_consume(
        queue=QUEUE_NAME,
        on_message_callback=callback,
        auto_ack=False
    )

    print(f"[consumer] Waiting for messages in '{QUEUE_NAME}'. Press Ctrl+C to exit.")
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        print("Interrupted by user")
    finally:
        channel.stop_consuming()
        connection.close()

if __name__ == "__main__":
    main()