import unittest
from unittest.mock import patch, MagicMock
from ml.inference import predict_aki, preprocess_data

class TestPredictAki(unittest.TestCase):

    @patch("ml.inference.model")  # Mock the model
    def test_predict_valid_input(self, mock_model):
        """Test prediction with valid input data."""
        mock_model.predict.return_value = [1]  # Simulated model output

        data = {
            "PID": "163244486",
            "Latest_Result_Timestamp": "20240323231900",
            "Age": 40,
            "Sex": 1,
            "Mean": 410,
            "Standard_Deviation": 10,
            "Max": 420,
            "Min": 400,
            "Last_Result_Value": 420
        }

        result, returned_mrn, returned_timestamp = predict_aki(data)

        self.assertEqual(result, [1])  # Check if prediction is correct
        self.assertEqual(returned_mrn, "163244486")
        self.assertEqual(returned_timestamp, "20240323231900")

    def test_preprocess_data(self):
        """Test preprocessing function with valid input."""
        data = {
            "PID": "163244486",
            "Latest_Result_Timestamp": "20240323231900",
            "Age": 40,
            "Sex": 1,
            "Mean": 410,
            "Standard_Deviation": 10,
            "Max": 420,
            "Min": 400,
            "Last_Result_Value": 420
        }

        features, mrn, timestamp = preprocess_data(data)

        self.assertEqual(features, [40, 1, 410, 10, 420, 400, 420])
        self.assertEqual(mrn, "163244486")
        self.assertEqual(timestamp, "20240323231900")

    @patch("ml.inference.model")
    def test_predict_invalid_data(self, mock_model):
        """Test predict_aki with incorrect data format."""
        mock_model.predict.side_effect = ValueError("Invalid input shape")

        data = {
            "PID": "163244486",
            "Latest_Result_Timestamp": "20240323231900",
            "Age": None,
            "Sex": 1,
            "Mean": 410,
            "Standard_Deviation": 10,
            "Max": 420,
            "Min": 400,
            "Last_Result_Value": 420
        }

        result, mrn, timestamp = predict_aki(data)

        self.assertIsNone(result)  # Should return None on failure

if __name__ == "__main__":
    unittest.main()
