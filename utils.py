import signal
from monitoring.metrics import SIGTERM_COUNTER

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
    try:
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
    except Exception as e:
        print(f"[utils] Exception {e}")

def build_hl7_ack():
    """
    Return a minimal HL7 ACK message wrapped in MLLP.
    The simulator only checks for 'MSH' + 'MSA|AA', so we can keep it simple.
    """
    # A minimal HL7 ACK (version 2.3 style) could be something like:
    hl7_ack = b"MSH|^~\\&|ACK_APP|ACK_FAC|SIMULATOR|SIM_FAC|20250129090000||ACK|12345|P|2.3\rMSA|AA|12345\r"
    # Wrap with MLLP framing: 0x0B (start), 0x1C (end), 0x0D
    return bytes([MLLP_START_OF_BLOCK]) + hl7_ack + bytes([MLLP_END_OF_BLOCK, MLLP_CARRIAGE_RETURN])


class GracefulKiller:
  # All credits to https://stackoverflow.com/questions/18499497/how-to-process-sigterm-signal-gracefully for this code snippet
  kill_now = False
  def __init__(self):
    signal.signal(signal.SIGINT, self.exit_gracefully)
    signal.signal(signal.SIGTERM, self.exit_gracefully)

  def exit_gracefully(self, signum, frame):
    print("[utils] Received SIGTERM")
    SIGTERM_COUNTER.inc()
    self.kill_now = True