import unittest
from copy import deepcopy
from ml.feature_construct import update

class TestUpdateFunction(unittest.TestCase):
    def setUp(self):
        """Setup a base feature dictionary before each test."""
        self.base_feature = {
            'PID': '12345',
            'Sex': 1.0,
            'Age': 45,
            'Min': None,
            'Max': None,
            'Mean': None,
            'Standard_Deviation': None,
            'Last_Result_Value': None,
            'Latest_Result_Timestamp': None,
            'No_of_Samples': 0,
            'Ready_for_Inference': "No"
        }

    def test_first_time_patient(self):
        """Test first-time patient scenario."""
        feature = deepcopy(self.base_feature)
        data = ['12345', 1.2, '20250204120000']
        updated_feature = update(feature, data, 'ORU^R01')

        self.assertEqual(updated_feature['Min'], 1.2)
        self.assertEqual(updated_feature['Max'], 1.2)
        self.assertEqual(updated_feature['Mean'], 1.2)
        self.assertEqual(updated_feature['Standard_Deviation'], 0)
        self.assertEqual(updated_feature['Last_Result_Value'], 1.2)
        self.assertEqual(updated_feature['Latest_Result_Timestamp'], '20250204120000')
        self.assertEqual(updated_feature['No_of_Samples'], 1)
        self.assertEqual(updated_feature['Ready_for_Inference'], "Yes")

    def test_subsequent_updates(self):
        """Test multiple updates to the same patient."""
        feature = deepcopy(self.base_feature)
        feature['Min'] = 1.2
        feature['Max'] = 1.2
        feature['Mean'] = 1.2
        feature['Standard_Deviation'] = 0
        feature['Last_Result_Value'] = 1.2
        feature['Latest_Result_Timestamp'] = '20250204120000'
        feature['No_of_Samples'] = 1

        data = ['12345', 2.0, '20250204120500']
        updated_feature = update(feature, data, 'ORU^R01')

        self.assertEqual(updated_feature['Min'], 1.2)
        self.assertEqual(updated_feature['Max'], 2.0)
        self.assertAlmostEqual(updated_feature['Mean'], 1.6, places=2)
        self.assertGreater(updated_feature['Standard_Deviation'], 0)  # Should not be 0 anymore
        self.assertEqual(updated_feature['Last_Result_Value'], 2.0)
        self.assertEqual(updated_feature['Latest_Result_Timestamp'], '20250204120500')
        self.assertEqual(updated_feature['No_of_Samples'], 2)

    def test_ready_for_inference(self):
        """Test if Ready_for_Inference is set when all fields are filled."""
        feature = deepcopy(self.base_feature)
        data = ['12345', 2.0, '20250204120500']
        
        # Simulate multiple updates
        for _ in range(5):
            feature = update(feature, data, 'ORU^R01')
        
        self.assertEqual(feature['Ready_for_Inference'], 'Yes')

    def test_ignore_unknown_message_type(self):
        """Test that an unknown message type does not modify the feature."""
        feature = deepcopy(self.base_feature)
        data = ['12345', 1.2, '20250204120000']
        updated_feature = update(feature, data, 'UNKNOWN_TYPE')

        self.assertEqual(updated_feature, self.base_feature)  # No change

if __name__ == '__main__':
    unittest.main()
