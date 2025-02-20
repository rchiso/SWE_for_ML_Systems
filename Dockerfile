FROM ubuntu:oracular

# Install system deps
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get -y install \
    python3 python3-pip python3-venv sqlite3

# Create a directory for application
WORKDIR /container
ENV PYTHONPATH=/container

# Copy project files into the container
COPY . /container/

# Create a virtual environment, install python deps
RUN python3 -m venv /container/venv
RUN /container/venv/bin/pip install -r /container/requirements.txt

# Expose Prometheus metrics port
EXPOSE 9090

# Initialize environment variables
ENV PROMETHEUS_PORT=9090

CMD [ "/container/venv/bin/python", "/container/main.py" ]