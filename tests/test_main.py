import unittest
from unittest.mock import patch, MagicMock
import socket
from main import main

class TestMain(unittest.TestCase):
    @patch('main.populate_db.main')
    @patch('main.socket.socket')
    @patch('main.build_hl7_ack')
    @patch('main.parse_mllp_stream')
    @patch('main.message_consumer')
    @patch('main.os.getenv')
    def test_main_success(self, mock_getenv, mock_message_consumer,
                          mock_parse_mllp_stream, mock_build_hl7_ack,
                          mock_socket, mock_populate_db):
        #Arrange
        mock_getenv.return_value = "localhost:12345"
        fake_socket_instance = MagicMock()
        fake_socket_instance.recv.side_effect = [b"dummy chunk", b""]
        mock_socket.return_value = fake_socket_instance
        mock_parse_mllp_stream.return_value = ([b"HL7 message"], b"")
        mock_build_hl7_ack.return_value = b"ACK"

        #Act
        main()

        #Assert
        mock_populate_db.assert_called_once()
        fake_socket_instance.connect.assert_called_once_with(('localhost', 12345))
        fake_socket_instance.settimeout.assert_called_once_with(20.0)
        mock_parse_mllp_stream.assert_called()  
        mock_message_consumer.assert_called_once_with(b"HL7 message")
        fake_socket_instance.sendall.assert_called_once_with(b"ACK")
        fake_socket_instance.close.assert_called_once()

    @patch('main.populate_db.main')
    @patch('main.socket.socket')
    @patch('main.os.getenv')
    def test_main_timeout(self, mock_getenv, mock_socket, mock_populate_db):
        #Arrange
        mock_getenv.return_value = "localhost:12345"
        fake_socket_instance = MagicMock()
        fake_socket_instance.recv.side_effect = socket.timeout
        mock_socket.return_value = fake_socket_instance

        #Act
        main()

        #Assert
        fake_socket_instance.close.assert_called_once()
        mock_populate_db.assert_called_once()

    @patch('main.populate_db.main')
    @patch('main.socket.socket')
    @patch('main.os.getenv')
    def test_main_keyboard_interrupt(self, mock_getenv, mock_socket, mock_populate_db):
        #Arrange
        mock_getenv.return_value = "localhost:12345"
        fake_socket_instance = MagicMock()
        fake_socket_instance.recv.side_effect = KeyboardInterrupt
        mock_socket.return_value = fake_socket_instance

        #Act
        main()

        #Assert
        fake_socket_instance.close.assert_called_once()
        mock_populate_db.assert_called_once()

    @patch('main.populate_db.main')
    @patch('main.socket.socket')
    @patch('main.build_hl7_ack')
    @patch('main.parse_mllp_stream')
    @patch('main.message_consumer')
    @patch('main.os.getenv')
    def test_main_general_exception(self, mock_getenv, mock_message_consumer,
                                    mock_parse_mllp_stream, mock_build_hl7_ack,
                                    mock_socket, mock_populate_db):
        #Arrange
        mock_getenv.return_value = "localhost:12345"
        fake_socket_instance = MagicMock()
        fake_socket_instance.recv.side_effect = [b"dummy chunk", b""]
        mock_socket.return_value = fake_socket_instance
        mock_parse_mllp_stream.return_value = ([b"HL7 message"], b"")
        mock_build_hl7_ack.return_value = b"ACK"
        mock_message_consumer.side_effect = Exception("Test exception")

        #Act
        main()

        #Assert
        fake_socket_instance.close.assert_called_once()
        fake_socket_instance.sendall.assert_not_called()
        mock_populate_db.assert_called_once()

if __name__ == "__main__":
    unittest.main()