#!/usr/bin/env python3
import sys
import pika
import json
from parsing.hl7 import mssg_parser
from ml.consumer import QUEUE_NAME as ML_QUEUE_NAME
from ml.feature_construct import update
from database_functionality.db_operations import handle_adt_a01
from database_functionality.db_operations import handle_oru_a01
from database_functionality.db_operations import update_feature_store
from database_functionality import create_db
from database_functionality import populate_db

RABBIT_HOST = "localhost"
QUEUE_NAME = "message_parsing_queue"

# TODO: implement message processing here
def process_message(body):
    """Pretend to parse + write to DB. Raise an exception sometimes for testing."""
    msg_str = body.decode("utf-8", errors="replace")
    print(f"[consumer] Processing message: {msg_str}", file=sys.stdout)
    # Simulate random failure. For a real scenario, replace with actual logic.
    if "FAIL" in msg_str:
        raise ValueError("Simulated processing error: 'FAIL' found")
    # Otherwise it "succeeds"
    print("[consumer] Done processing.", file=sys.stdout)

# We don't have an explicit producer in this queue, because the consumer of 1st queue is acting as one
def callback(ch, method, properties, body):
    # Extract or initialize retry count from headers
    headers = properties.headers or {}
    retry_count = headers.get("x-retry-count", 0)

    try:
        # hl7 mssg parsing 
        mssg_type, data = mssg_parser(body)
        process_message(body)  
        # Fetch data from DB 
        if mssg_type=='ADT^A01':
            old_feat = handle_adt_a01(data)
        elif mssg_type=='ORU^R01':
            old_feat = handle_oru_a01(data)
        else:
            old_feat = None
        # feture construction
        if old_feat is not None and mssg_type=='ORU^R01':
            new_feature = update(old_feat, data, mssg_type)
            # Send to ML Queue when ready for inference
            if new_feature['Ready_for_Inference'] == 'Yes':
                # Publish to the second queue
                ch.basic_publish(
                    exchange="",
                    routing_key=ML_QUEUE_NAME,
                    body=json.dumps(new_feature), 
                    properties=pika.BasicProperties(delivery_mode=2)  # durable
                )
                new_feature['Ready_for_Inference'] = 'No'

            update_feature_store(new_feature['PID'], new_feature)  # data[0] is the patient_id
        # ack the message    
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        # Something went wrong
        print(f"[consumer] Error processing message: {e}",file=sys.stderr)
        
        if retry_count < 1:
            # 1) We'll republish the message with retry_count+1
            new_retry_count = retry_count + 1
            print(f"[consumer] Requeue attempt #{new_retry_count} ...", file=sys.stderr)

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
            print("[consumer] Retry limit exceeded, sending to Dead Letter Queue...", file=sys.stdout)
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def main():
    populate_db.main()
    connection_params = pika.ConnectionParameters(host=RABBIT_HOST)
    connection = pika.BlockingConnection(connection_params)
    channel = connection.channel()

    # -- Declare DLX and DLQ (for dead letters) --
    DLX_NAME = "dlx_message_parsing"
    channel.exchange_declare(exchange=DLX_NAME, exchange_type="direct", durable=True)

    DLQ_NAME = "message_parsing_queue_dlx"
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

    print(f"[consumer] Waiting for messages in '{QUEUE_NAME}'. Press Ctrl+C to exit.", file=sys.stdout)
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        print("Interrupted by user")
    finally:
        channel.stop_consuming()
        connection.close()

if __name__ == "__main__":
    main()