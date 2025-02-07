import unittest
import sqlite3
import pandas as pd
from unittest.mock import patch
from database_functionality.populate_db import (
    process_creatinine_data,
    add_demographics,
    insert_into_database,
)

class ConnectionWrapper:
    """
    A simple wrapper for a sqlite3.Connection that overrides the close() method.
    Any attribute access not defined in this wrapper is delegated to the underlying connection.
    """
    def __init__(self, conn):
        self._conn = conn

    def close(self):
        # Override close to do nothing.
        pass

    def __getattr__(self, attr):
        return getattr(self._conn, attr)

class TestHistoryFileProcessing(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Load the history.csv file for testing."""
        cls.file_path = "data/history.csv"  # Path to the history.csv file
        cls.dataset = pd.DataFrame({
            "mrn": [1],
            "creatinine_date_0": ["2024-01-01 15:13:00"],
            "creatinine_result_0": [126.48],
            "creatinine_date_1": ["2024-01-15 10:45:00"],
            "creatinine_result_1": [152.24],
            "creatinine_date_2": ["2024-02-05 14:34:00"],
            "creatinine_result_2": [128.38],
            "creatinine_date_3": ["2024-02-06 10:19:00"],
            "creatinine_result_3": [97.18],
            "creatinine_date_4": ["2024-02-06 14:45:00"],
            "creatinine_result_4": [130.04],
        })  # Simulated history.csv data

    def setUp(self):
        """Set up an in-memory SQLite database."""
        self.conn = sqlite3.connect(":memory:")
        self.cursor = self.conn.cursor()

        # Create the required tables
        self.cursor.execute("""
        CREATE TABLE Feature_Store (
            PID INTEGER PRIMARY KEY,
            Sex FLOAT,
            Age INTEGER,
            Min FLOAT,
            Max FLOAT,
            Mean FLOAT,
            Standard_Deviation FLOAT,
            Last_Result_Value FLOAT,
            Latest_Result_Timestamp TEXT,
            No_of_Samples INTEGER,
            Ready_for_Inference TEXT
        );
        """)
        self.cursor.execute("""
        CREATE TABLE Patient_Data (
            PID INTEGER PRIMARY KEY,
            DOB TEXT,
            Admission_Status TEXT,
            Admission_Date TEXT
        );
        """)
        self.conn.commit()

    def tearDown(self):
        """Close the in-memory SQLite database."""
        self.conn.close()

    @patch("database_functionality.populate_db.sqlite3.connect")
    def test_process_creatinine_data_values(self, mock_connect):
        """Test processing of creatinine data with mock database."""
        mock_connect.return_value = self.conn
        processed_dataset = process_creatinine_data(self.file_path)

        # Check that the processed dataset contains the correct columns
        self.assertIn("creatinine_mean", processed_dataset.columns)
        self.assertIn("latest_test_value", processed_dataset.columns)
        self.assertIn("No_of_Samples", processed_dataset.columns)

        # Verify computations for the first row
        first_row = processed_dataset.iloc[0]
        self.assertAlmostEqual(first_row["creatinine_mean"], 126.864, delta=0.1)
        self.assertEqual(first_row["No_of_Samples"], 5)
        self.assertEqual(first_row["latest_test_value"], 130.04)

    @patch("database_functionality.populate_db.sqlite3.connect")
    def test_add_demographics_with_history(self, mock_connect):
        """Test addition of demographic information using processed history data."""
        mock_connect.return_value = self.conn
        processed_dataset = process_creatinine_data(self.file_path)
        demographic_dataset = add_demographics(processed_dataset, use_random=True)

        # Ensure demographic columns are added
        self.assertIn("DOB", demographic_dataset.columns)
        self.assertIn("Age", demographic_dataset.columns)
        self.assertIn("Sex", demographic_dataset.columns)

        # Validate demographics for the first row
        first_row = demographic_dataset.iloc[0]
        self.assertIsNotNone(first_row["DOB"])
        self.assertGreaterEqual(first_row["Age"], 18)  # Ensure age is at least 18

    @patch("database_functionality.populate_db.sqlite3.connect")
    def test_insert_into_database_with_history(self, mock_connect):
        """Test insertion of processed history data into the in-memory database."""
        # Wrap self.conn with our ConnectionWrapper to override close()
        wrapped_conn = ConnectionWrapper(self.conn)
        mock_connect.return_value = wrapped_conn

        # Process and insert the dataset
        processed_dataset = process_creatinine_data(self.file_path)
        demographic_dataset = add_demographics(processed_dataset, use_random=True)
        insert_into_database(demographic_dataset, wrapped_conn, use_random=True)

        # # Verify data in Feature_Store
        # self.cursor.execute("SELECT * FROM Feature_Store")
        # feature_store_records = self.cursor.fetchall()
        # self.assertEqual(len(feature_store_records), len(self.dataset))

        # # Verify data in Patient_Data
        # self.cursor.execute("SELECT * FROM Patient_Data")
        # patient_data_records = self.cursor.fetchall()
        # self.assertEqual(len(patient_data_records), len(self.dataset))


if __name__ == "__main__":
    unittest.main()
