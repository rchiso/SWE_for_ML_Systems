import pika

# Define RabbitMQ connection details
RABBIT_HOST = "localhost"
QUEUE_NAME = "message_parsing_queue"

# Establish connection
connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBIT_HOST))
channel = connection.channel()

# Purge the queue
channel.queue_purge(queue=QUEUE_NAME)
print(f"Queue '{QUEUE_NAME}' has been purged.")

# Close the connection
connection.close()
