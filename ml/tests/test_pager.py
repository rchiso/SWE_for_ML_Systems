import unittest
import requests
from unittest.mock import patch, MagicMock
from ml.pager import send_pager_request

class TestSendPagerRequest(unittest.TestCase):

    @patch("ml.pager.requests.post")
    def test_pager_success(self, mock_post):
        """Test successful pager request."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        status = send_pager_request("163244486", "20240323231900")
        self.assertEqual(status, 200)

    @patch("ml.pager.requests.post")
    def test_pager_http_error(self, mock_post):
        """Test pager request with an HTTP error (e.g., 404 or 500)."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response

        status = send_pager_request("163244486", "20240323231900")
        self.assertEqual(status, 500)

    @patch("ml.pager.requests.post")
    def test_pager_timeout(self, mock_post):
        """Test pager request timeout handling."""
        mock_post.side_effect = requests.exceptions.Timeout()

        status = send_pager_request("163244486", "20240323231900")
        self.assertIsNone(status)

    @patch("ml.pager.requests.post")
    def test_pager_connection_error(self, mock_post):
        """Test pager request with a connection error."""
        mock_post.side_effect = requests.exceptions.ConnectionError()

        status = send_pager_request("163244486", "20240323231900")
        self.assertIsNone(status)

if __name__ == "__main__":
    unittest.main()
