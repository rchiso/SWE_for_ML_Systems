FROM ubuntu:oracular

# 1. Install system deps
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get -y install \
    python3 python3-pip python3-venv rabbitmq-server supervisor

# 2. Create a directory for application
WORKDIR /container

# 3. Copy project files into the container
COPY . /container/

# 4. Create a virtual environment, install python deps
RUN python3 -m venv /container/venv
RUN /container/venv/bin/pip install --upgrade pip
RUN /container/venv/bin/pip install -r /container/requirements.txt

# Enable RabbitMQ management plugin (web UI on port 15672)
RUN rabbitmq-plugins enable rabbitmq_management

# 5. Expose ports:
#  - 5672 for RabbitMQ (AMQP)
#  - 15672 for RabbitMQ management
#  - 8440, 8441 for simulator
EXPOSE 5672
EXPOSE 15672
EXPOSE 8440
EXPOSE 8441

# 6. Copy supervisord.conf to /etc/supervisor/conf.d so Supervisor picks it up.
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# 7. The final command: run Supervisor in the foreground
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]