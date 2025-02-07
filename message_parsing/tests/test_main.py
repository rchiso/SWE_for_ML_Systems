import unittest
from unittest.mock import patch, MagicMock
from message_parsing.main import message_consumer


class TestMessageConsumer(unittest.TestCase):

    @patch("message_parsing.main.mssg_parser")
    @patch("message_parsing.main.handle_adt_a01")
    @patch("message_parsing.main.handle_oru_a01")
    @patch("message_parsing.main.update")
    @patch("message_parsing.main.ml_consumer")
    @patch("message_parsing.main.update_feature_store")
    def test_message_consumer_oru_r01_ready_for_inference(
        self, mock_update_feature_store, mock_ml_consumer, 
        mock_update, mock_handle_oru_a01, mock_handle_adt_a01, mock_mssg_parser
    ):
        """Test ORU^R01 message where feature is ready for inference"""
        
        # Mock HL7 message parser
        mock_mssg_parser.return_value = ('ORU^R01', ['12345', 1.2, '20250204120000'])

        # Mock database response
        mock_handle_oru_a01.return_value = {'PID': '12345', 'Mean': 1.1, 'Ready_for_Inference': 'No'}

        # Mock feature update
        updated_feature = {'PID': '12345', 'Mean': 1.1, 'Ready_for_Inference': 'Yes'}
        mock_update.return_value = updated_feature

        # Call function
        message_consumer("fake_hl7_message")

        # Verify ML was called
        mock_ml_consumer.assert_called_once_with(updated_feature)

        # Verify feature store update was called
        mock_update_feature_store.assert_called_once_with('12345', {'PID': '12345', 'Mean': 1.1, 'Ready_for_Inference': 'No'})  

    @patch("message_parsing.main.mssg_parser")
    @patch("message_parsing.main.handle_adt_a01")
    @patch("message_parsing.main.update_feature_store")
    def test_message_consumer_adt_a01(self, mock_update_feature_store, mock_handle_adt_a01, mock_mssg_parser):
        """Test ADT^A01 message type"""
        
        # Mock HL7 message parser
        mock_mssg_parser.return_value = ('ADT^A01', ['12345', 'M', 30])

        # Mock database response
        mock_handle_adt_a01.return_value = {'PID': '12345', 'Sex': 'M', 'Age': 30}

        # Call function
        message_consumer("fake_hl7_message")

        # Verify update_feature_store was NOT called
        mock_update_feature_store.assert_not_called()


if __name__ == "__main__":
    unittest.main()
