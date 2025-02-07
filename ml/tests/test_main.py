import unittest
from unittest.mock import patch, MagicMock
from ml.main import ml_consumer

class TestMLConsumer(unittest.TestCase):
    @patch("ml.main.predict_aki")
    @patch("ml.main.send_pager_request")
    def test_aki_detected_pager_success(self, mock_send_pager_request, mock_predict_aki):
        """Test when AKI is detected and pager request succeeds."""
        mock_predict_aki.return_value = ([1], "12345", "20250204120000")
        mock_send_pager_request.return_value = 200

        with patch("builtins.print") as mock_print:
            ml_consumer({"some": "data"})

        #mock_predict_aki.assert_called_once()
        mock_send_pager_request.assert_called_once_with("12345", "20250204120000")
        mock_print.assert_any_call("[ml_consumer] Pager success, ACKing message.")

    @patch("ml.main.predict_aki")
    @patch("ml.main.send_pager_request")
    def test_aki_detected_pager_network_error(self, mock_send_pager_request, mock_predict_aki):
        """Test when AKI is detected but pager request raises an exception."""
        mock_predict_aki.return_value = ([1], "12345", "20250204120000")
        mock_send_pager_request.side_effect = Exception("Network issue")

        with patch("builtins.print") as mock_print:
            ml_consumer({"some": "data"})

        mock_predict_aki.assert_called_once()
        mock_send_pager_request.assert_called_once()
        mock_print.assert_any_call("[ml_consumer] ERROR: Network issue")

    @patch("ml.main.predict_aki")
    def test_aki_not_detected(self, mock_predict_aki):
        """Test when AKI is not detected."""
        mock_predict_aki.return_value = ([0], "12345", "20250204120000")

        with patch("builtins.print") as mock_print:
            ml_consumer({"some": "data"})

        mock_predict_aki.assert_called_once()
        mock_print.assert_any_call("[ml_consumer] AKI not detected")

    @patch("ml.main.predict_aki")
    def test_prediction_error(self, mock_predict_aki):
        """Test when prediction returns None."""
        mock_predict_aki.return_value = [None, None, None]  # Simulating an error

        with patch("builtins.print") as mock_print:
            ml_consumer({"some": "data"})

        mock_predict_aki.assert_called_once()
        mock_print.assert_any_call("[ml_consumer] Prediction Error")

if __name__ == "__main__":
    unittest.main()
