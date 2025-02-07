import unittest
from unittest.mock import MagicMock, patch
from message_parsing.consumer import callback, process_message

class TestConsumer(unittest.TestCase):
    def setUp(self):
        # Common mocks we'll reuse
        self.mock_channel = MagicMock()
        self.mock_method = MagicMock()
        self.mock_method.delivery_tag = 123  # just some arbitrary tag
        self.mock_properties = MagicMock()
        self.mock_properties.headers = {}  # default: no headers

    def test_process_message_success(self):
        """process_message should not raise if message doesn't contain 'FAIL'."""
        body = b"Hello World"
        # Should not raise an exception
        process_message(body)  # no assert needed, just verifying it doesn't fail

    def test_process_message_failure(self):
        """process_message should raise ValueError if message contains 'FAIL'."""
        body = b"Something FAIL here"
        with self.assertRaises(ValueError):
            process_message(body)

    def test_callback_success_ack(self):
        """
        If process_message succeeds, consumer should basic_ack the message.
        No retry logic, no republish, no nack.
        """
        body = b"Hello"  # 'FAIL' not in message => success
        callback(self.mock_channel, self.mock_method, self.mock_properties, body)
        self.mock_channel.basic_ack.assert_called_once_with(delivery_tag=123)
        self.mock_channel.basic_publish.assert_not_called()
        self.mock_channel.basic_nack.assert_not_called()

    def test_callback_first_failure_retry(self):
        """
        If process_message fails, but x-retry-count < 1 (0 by default),
        we should republish with x-retry-count=1 and basic_ack the original.
        """
        body = b"FAIL"
        callback(self.mock_channel, self.mock_method, self.mock_properties, body)

        # Should ACK the original
        self.mock_channel.basic_ack.assert_called_once_with(delivery_tag=123)

        # Should republish once with updated headers
        self.mock_channel.basic_publish.assert_called_once()
        publish_args, publish_kwargs = self.mock_channel.basic_publish.call_args
        self.assertEqual(publish_kwargs["routing_key"], "main_queue")
        self.assertIn("x-retry-count", publish_kwargs["properties"].headers)
        self.assertEqual(publish_kwargs["properties"].headers["x-retry-count"], 1)

        # No NACK
        self.mock_channel.basic_nack.assert_not_called()

    def test_callback_second_failure_dead_letter(self):
        """
        If process_message fails and x-retry-count is already 1,
        we exceed our retry limit (which is 1 in this code),
        so we should basic_nack with requeue=False => goes to DLQ.
        """
        body = b"FAIL"
        # Indicate we've already retried once
        self.mock_properties.headers = {"x-retry-count": 1}

        callback(self.mock_channel, self.mock_method, self.mock_properties, body)

        # Should not republish
        self.mock_channel.basic_publish.assert_not_called()

        # Should not ack
        self.mock_channel.basic_ack.assert_not_called()

        # Should NACK with requeue=False
        self.mock_channel.basic_nack.assert_called_once_with(
            delivery_tag=123, requeue=False
        )

if __name__ == "__main__":
    unittest.main()