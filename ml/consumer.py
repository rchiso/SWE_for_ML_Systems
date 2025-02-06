#!/usr/bin/env python3
import pika
import random
import json
from ml.inference import predict_aki
from ml.pager import send_pager_request

RABBIT_HOST = "localhost"
QUEUE_NAME = "ml_queue"

def do_fake_pager_call(inference_result):
    """Pretend to call a pager system. We'll simulate a 200 or 400 randomly."""
    print(f"[ml_consumer] Sending to pager: {inference_result}")
    # For testing, we randomly succeed or fail
    status_code = random.choice([200, 400])  # 50% success, 50% fail
    return status_code

def callback(ch, method, properties, body):
    headers = properties.headers or {}
    retry_count = headers.get("x-retry-count", 0)

    #data = body.decode("utf-8", errors="replace") # TODO: this should be the row from feature store table
    data = json.loads(body)
    print(f"[ml_consumer] Received message: data={data}")

    # TODO: send to ml for inference
    aki_result, mrn, timestamp = predict_aki(data)
    if aki_result == None:
        print("[ml_consumer] Prediction Error")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        return
    if aki_result[0] == 1:
        try:
            # TODO: send result to pager
            pager_status = send_pager_request(mrn, timestamp)
            #pager_status = do_fake_pager_call(data)
            
            if pager_status == None or pager_status % 100 == 5:
                # Network Error or Pager returned 5xx => let's retry once, else DLQ
                if retry_count < 1:
                    print(f"[ml_consumer] Pager error {pager_status}, retrying...")
                    new_headers = dict(headers)
                    new_headers["x-retry-count"] = retry_count + 1
                    ch.basic_publish(
                        exchange="",
                        routing_key=QUEUE_NAME,
                        body=body,
                        properties=pika.BasicProperties(
                            headers=new_headers,
                            delivery_mode=2
                        )
                    )
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                else:
                    print("[ml_consumer] Pager error, reached retry limit => DLQ.")
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            elif pager_status == 200:
                # Success => ACK
                print("[ml_consumer] Pager success, ACKing message.")
                ch.basic_ack(delivery_tag=method.delivery_tag)

        except Exception as e:
            # Python error => direct to DLQ
            print(f"[ml_consumer] ERROR: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    else:
        #TODO: Add logging for when AKI is not detected
        print("[ml_consumer] AKI not detected")
        ch.basic_ack(delivery_tag=method.delivery_tag)

def main():
    conn_params = pika.ConnectionParameters(host=RABBIT_HOST)
    connection = pika.BlockingConnection(conn_params)
    channel = connection.channel()

    # Declare a DLX + DLQ for the ML queue
    DLX_NAME = "dlx_ml"
    ML_DLX_QUEUE = "ml_queue_dlx"
    channel.exchange_declare(exchange=DLX_NAME, exchange_type="direct", durable=True)
    channel.queue_declare(queue=ML_DLX_QUEUE, durable=True)
    channel.queue_bind(exchange=DLX_NAME, queue=ML_DLX_QUEUE, routing_key="ml_dlx_routing_key")

    # Declare the ML queue with the DLX
    channel.queue_declare(
        queue=QUEUE_NAME,
        durable=True,
        arguments={
            'x-dead-letter-exchange': DLX_NAME,
            'x-dead-letter-routing-key': 'ml_dlx_routing_key'
        }
    )

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback, auto_ack=False)
    print(f"[ml_consumer] Listening on '{QUEUE_NAME}' for ML tasks.")
    channel.start_consuming()

if __name__ == "__main__":
    main()

