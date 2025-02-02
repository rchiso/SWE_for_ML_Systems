#!/usr/bin/env python3
import argparse
import socket
import pika

# MLLP control characters
MLLP_START_OF_BLOCK = 0x0b  # \x0B
MLLP_END_OF_BLOCK   = 0x1c  # \x1C
MLLP_CARRIAGE_RETURN= 0x0d  # \x0D

def parse_mllp_stream(buffer):
    """
    Parse out zero or more complete MLLP messages from the given buffer.
    Return (list_of_messages, leftover_buffer).
    
    A well-formed MLLP message is framed by:
      0x0B (start) ... data ... 0x1C (end) 0x0D (carriage return)
    We may receive partial or multiple messages at once, so we accumulate
    in 'buffer' and extract fully framed messages.
    """
    messages = []
    i = 0
    start_idx = None

    while i < len(buffer):
        if start_idx is None:
            # Looking for 0x0B
            if buffer[i] == MLLP_START_OF_BLOCK:
                start_idx = i + 1  # message starts after 0x0B
            i += 1
        else:
            # We have started a message; look for 0x1C, then 0x0D
            if buffer[i] == MLLP_END_OF_BLOCK:
                # Next character should be 0x0D if we have a full message
                if i + 1 < len(buffer) and buffer[i+1] == MLLP_CARRIAGE_RETURN:
                    # Extract the message (everything between 0x0B and 0x1C)
                    msg = buffer[start_idx:i]
                    messages.append(msg)
                    # Advance i to after the 0x1C 0x0D
                    i += 2
                    # Reset start_idx to look for next 0x0B
                    start_idx = None
                else:
                    # Found 0x1C but not followed by 0x0D -> incomplete frame
                    i += 1
            else:
                i += 1

    leftover = buffer[i:]  # anything we haven’t consumed
    return messages, leftover

def build_hl7_ack():
    """
    Return a minimal HL7 ACK message wrapped in MLLP.
    The simulator only checks for 'MSH' + 'MSA|AA', so we can keep it simple.
    """
    # A minimal HL7 ACK (version 2.3 style) could be something like:
    hl7_ack = b"MSH|^~\\&|ACK_APP|ACK_FAC|SIMULATOR|SIM_FAC|20250129090000||ACK|12345|P|2.3\rMSA|AA|12345\r"
    # Wrap with MLLP framing: 0x0B (start), 0x1C (end), 0x0D
    return bytes([MLLP_START_OF_BLOCK]) + hl7_ack + bytes([MLLP_END_OF_BLOCK, MLLP_CARRIAGE_RETURN])

def main():
    parser = argparse.ArgumentParser(description="MLLP Producer that reads from simulator and pushes to RabbitMQ.")
    parser.add_argument("--sim_host", default="localhost", help="Host where the simulator is running")
    parser.add_argument("--sim_port", type=int, default=8440, help="Port where the simulator is listening for MLLP")
    parser.add_argument("--rabbit_host", default="localhost", help="RabbitMQ host")
    parser.add_argument("--queue_name", default="main_queue", help="Name of the RabbitMQ queue")
    args = parser.parse_args()

    # 1. Connect to RabbitMQ (blocking connection)
    connection_params = pika.ConnectionParameters(host=args.rabbit_host)
    rabbit_connection = pika.BlockingConnection(connection_params)
    channel = rabbit_connection.channel()

    # 2. Connect to Simulator's TCP MLLP port
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((args.sim_host, args.sim_port))
    sock.settimeout(20.0)

    print(f"[producer_mllp] Connected to simulator at {args.sim_host}:{args.sim_port} ...")

    leftover = b""
    ack_message = build_hl7_ack()

    try:
        while True:
            # 3. Read data from the simulator
            chunk = sock.recv(1024)
            if not chunk:
                print("[producer_mllp] Simulator closed connection.")
                break  # connection closed by server
            leftover += chunk

            # 4. Try to parse out complete MLLP‐framed messages
            messages, leftover = parse_mllp_stream(leftover)

            # 5. For each complete HL7 message:
            for msg in messages:
                # Here 'msg' is the raw HL7 bytes between 0x0B and 0x1C
                hl7_str = msg.decode("utf-8", errors="replace")
                print(f"[producer_mllp] Received HL7 message:\n{hl7_str}")

                # 6. Publish to RabbitMQ
                channel.basic_publish(
                    exchange="",
                    routing_key=args.queue_name,
                    body=msg,
                    properties=pika.BasicProperties(delivery_mode=2)
                )
                print("[producer_mllp] Published message to RabbitMQ.")

                # 7. Send an ACK back to the simulator
                sock.sendall(ack_message)
                print("[producer_mllp] Sent MLLP ACK.")

    except socket.timeout:
        print("[producer_mllp] Socket timed out. Stopping client.")
    except KeyboardInterrupt:
        print("[producer_mllp] Interrupted by user.")
    except Exception as e:
        print(f"[producer_mllp] Error: {e}")

    finally:
        sock.close()
        rabbit_connection.close()
        print("[producer_mllp] Connection closed. Exiting.")

if __name__ == "__main__":
    main()