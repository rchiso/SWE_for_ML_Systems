#!/usr/bin/env python3
import socket
import os
from utils import parse_mllp_stream, build_hl7_ack
from message_parsing.main import message_consumer
from database_functionality import create_db
from database_functionality import populate_db

def main():
    populate_db.main()   # populate the db with history.csv

    sim_address = os.getenv('MLLP_ADDRESS')  # Connect to Simulator's TCP MLLP port
    #sim_address = 'localhost:8440'

    sim_host, sim_port = sim_address.split(":")

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((sim_host, int(sim_port)))
    sock.settimeout(20.0)

    print(f"[main] Connected to simulator at {sim_host}:{sim_port} ...")
    leftover = b""
    ack_message = build_hl7_ack()

    try:
        while True:
            # 1. Read data from the simulator
            chunk = sock.recv(1024)
            if not chunk:
                print("[main] Simulator closed connection.")
                break  # connection closed by server
            leftover += chunk

            # 2. Try to parse out complete MLLP‐framed messages
            messages, leftover = parse_mllp_stream(leftover)

            # 3. For each complete HL7 message:
            for msg in messages:
                # Here 'msg' is the raw HL7 bytes between 0x0B and 0x1C
                hl7_str = msg.decode("utf-8", errors="replace")
                #print(f"[main] Received HL7 message:\n{hl7_str}")

                message_consumer(msg)

                sock.sendall(ack_message)
                print("[main] Sent MLLP ACK.")

    except socket.timeout:
        print("[main] Socket timed out. Stopping client.")
    except KeyboardInterrupt:
        print("[main] Interrupted by user.")
    except Exception as e:
        print(f"[main] Error: {e}")

    finally:
        sock.close()

        print("[main] Connection closed. Exiting.")

if __name__ == "__main__":
    main()