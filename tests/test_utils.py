import unittest
from utils import parse_mllp_stream, build_hl7_ack
from utils import MLLP_START_OF_BLOCK, MLLP_END_OF_BLOCK, MLLP_CARRIAGE_RETURN

class TestUtils(unittest.TestCase):
    
    def test_parse_mllp_stream_single_message(self):
        #Arrange
        buffer = bytes([MLLP_START_OF_BLOCK]) + b"HL7_MESSAGE" + bytes([MLLP_END_OF_BLOCK, MLLP_CARRIAGE_RETURN])
        #Act
        messages, leftover = parse_mllp_stream(buffer)
        #Assert
        self.assertEqual(messages, [b"HL7_MESSAGE"])
        self.assertEqual(leftover, b"")
    
    def test_parse_mllp_stream_multiple_messages(self):
        #Arrange
        buffer = (
            bytes([MLLP_START_OF_BLOCK]) + b"MSG1" + bytes([MLLP_END_OF_BLOCK, MLLP_CARRIAGE_RETURN]) +
            bytes([MLLP_START_OF_BLOCK]) + b"MSG2" + bytes([MLLP_END_OF_BLOCK, MLLP_CARRIAGE_RETURN])
        )
        #Act
        messages, leftover = parse_mllp_stream(buffer)
        #Assert
        self.assertEqual(messages, [b"MSG1", b"MSG2"])
        self.assertEqual(leftover, b"")
    
    def test_build_hl7_ack(self):
        #Act
        ack = build_hl7_ack()
        #Assert
        self.assertTrue(ack.startswith(bytes([MLLP_START_OF_BLOCK])))
        self.assertTrue(ack.endswith(bytes([MLLP_END_OF_BLOCK, MLLP_CARRIAGE_RETURN])))
        self.assertIn(b"MSH|^~\\&|ACK_APP|ACK_FAC|SIMULATOR|SIM_FAC", ack)
        self.assertIn(b"MSA|AA|12345", ack)


if __name__ == "__main__":
    unittest.main()