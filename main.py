#!/usr/bin/env python3
import socket
import os
import time
from utils import parse_mllp_stream, build_hl7_ack, GracefulKiller
from message_parsing.main import message_consumer
from database_functionality import populate_db
from database_functionality import create_db
from monitoring.metrics import init_metrics, SOCKET_TIMEOUTS

DELAY_RETRY = 10
TIMEOUT = 20

def main():
    killer = GracefulKiller()
    init_flag = True
    timeout_reconnect_flag = False #prevent print statement if reconnect is due to timeout (prevent spam)
    while not killer.kill_now:
        try:
            if init_flag:
                init_flag = False
                prometheus_port = int(os.getenv("PROMETHEUS_PORT", 9090))
                init_metrics(prometheus_port)
                print(f"[main] Prometheus metrics server running on port {prometheus_port}.")
                db_flag = create_db.main()
                if not db_flag:
                    populate_db.main()   # populate the db with history.csv

            sim_address = os.getenv('MLLP_ADDRESS')  # Connect to Simulator's TCP MLLP port
            # sim_address = 'localhost:8440'

            sim_host, sim_port = sim_address.split(":")
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((sim_host, int(sim_port)))
            sock.settimeout(TIMEOUT)
            if not timeout_reconnect_flag:
                timeout_reconnect_flag = False
                print(f"[main] Connected to simulator at {sim_host}:{sim_port} ...")
            leftover = b""
            ack_message = build_hl7_ack()
            while not killer.kill_now:
                try:
                    # 1. Read data from the simulator
                    chunk = sock.recv(1024)
                    if not chunk:
                        print("[main] Simulator closed connection.")
                        timeout_reconnect_flag = False
                        break  # connection closed by server
                    leftover += chunk

                    # 2. Try to parse out complete MLLP‐framed messages
                    messages, leftover = parse_mllp_stream(leftover)

                    # 3. For each complete HL7 message:
                    for msg in messages:
                        # Here 'msg' is the raw HL7 bytes between 0x0B and 0x1C
                        # hl7_str = msg.decode("utf-8", errors="replace")
                        # print(f"[main] Received HL7 message:\n{hl7_str}")

                        message_consumer(msg)

                        sock.sendall(ack_message)
                        print("[main] Sent MLLP ACK.")

                except socket.timeout:
                    #print(f"[main] Socket timed out.")
                    timeout_reconnect_flag = True
                    SOCKET_TIMEOUTS.inc()
                    break
                except Exception as e:
                    print(f"[main] Error: {e}, reconnecting to socket in {DELAY_RETRY} seconds")
                    timeout_reconnect_flag = False
                    try:
                        sock.close()
                    except Exception as e:
                        print(f"[main] Error {e} while closing socket")
                        pass
                    finally:
                        time.sleep(DELAY_RETRY)
                        break

        except Exception as e:
            print(f"[main] Received Error: {e}")
            continue

if __name__ == "__main__":
    main()
