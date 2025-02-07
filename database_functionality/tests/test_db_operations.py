import unittest
import sqlite3
from unittest.mock import patch
from datetime import datetime
from database_functionality.db_operations import handle_adt_a01, handle_oru_a01, update_feature_store, connect_db  # Adjust the import as per your file structure

class TestDatabaseHandlers(unittest.TestCase):

    def setUp(self):
        """Set up an in-memory SQLite database and create the required tables."""
        self.conn = sqlite3.connect(":memory:")  # Use in-memory database for testing
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.cursor = self.conn.cursor()

        # Create Patient_Data table
        self.cursor.execute("""
        CREATE TABLE Patient_Data (
            PID INTEGER PRIMARY KEY,
            Admission_Status TEXT,
            DOB TEXT,
            Admission_Date TEXT
        );
        """)

        # Create Feature_Store table
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
            Ready_for_Inference TEXT,
            FOREIGN KEY (PID) REFERENCES Patient_Data (PID) ON DELETE CASCADE
        );
        """)

        self.conn.commit()

    def tearDown(self):
        """Close the database connection after each test."""
        self.conn.close()

    @patch("database_functionality.db_operations.connect_db")
    def test_handle_adt_a01_existing_patient(self, mock_connect_db):
        """Test ADT^A01 for an existing patient."""
        mock_connect_db.return_value = self.conn
        self.cursor.execute("""
        INSERT INTO Patient_Data (PID, Admission_Status) VALUES (1, 'No');
        """)
        self.cursor.execute("""
        INSERT INTO Feature_Store (PID, Sex, Age) VALUES (1, NULL, NULL);
        """)
        self.conn.commit()

        data = (1, 40, "M")
        result = handle_adt_a01(data)

        self.assertIsNotNone(result)
        self.assertEqual(result["Age"], 40)
        self.assertEqual(result["Sex"], 0)
        self.assertEqual(result["PID"], 1)

    @patch("database_functionality.db_operations.connect_db")
    def test_handle_adt_a01_new_patient(self, mock_connect_db):
        """Test ADT^A01 for a new patient."""
        mock_connect_db.return_value = self.conn
        data = (2, 35, "F")
        result = handle_adt_a01(data)

        self.assertIsNone(result)  # No Feature_Store record returned for new patients
        self.cursor.execute("SELECT * FROM Patient_Data WHERE PID = 2")
        patient_record = self.cursor.fetchone()
        self.assertEqual(patient_record[0], 2)  # PID
        self.assertEqual(patient_record[1], "Yes")  # Admission_Status

    @patch("database_functionality.db_operations.connect_db")
    def test_handle_oru_a01_existing_patient(self, mock_connect_db):
        """Test ORU^A01 for an existing patient."""
        mock_connect_db.return_value = self.conn
        self.cursor.execute("""
        INSERT INTO Patient_Data (PID, Admission_Status) VALUES (1, 'Yes');
        """)
        self.cursor.execute("""
        INSERT INTO Feature_Store (PID, Last_Result_Value, Latest_Result_Timestamp)
        VALUES (1, 420, '20240223120000');
        """)
        self.conn.commit()

        data = (1, 430, "20240224120000")
        result = handle_oru_a01(data)

        self.assertIsNotNone(result)
        self.assertEqual(result["Last_Result_Value"], 420)
        self.assertEqual(result["Latest_Result_Timestamp"], "20240223120000")

    @patch("database_functionality.db_operations.connect_db")
    def test_handle_oru_a01_new_patient(self, mock_connect_db):
        """Test ORU^A01 for a new patient."""
        mock_connect_db.return_value = self.conn
        data = (2, 450, "20240225120000")
        result = handle_oru_a01(data)

        self.assertIsNone(result)
        self.cursor.execute("SELECT * FROM Patient_Data WHERE PID = 2")
        patient_record = self.cursor.fetchone()
        self.assertEqual(patient_record[0], 2)  # PID
        self.assertEqual(patient_record[1], "Pending")  # Admission_Status

    @patch("database_functionality.db_operations.connect_db")
    def test_update_feature_store(self, mock_connect_db):
        """Test updating Feature_Store for an existing patient."""
        mock_connect_db.return_value = self.conn

        # Ensure the corresponding Patient_Data record exists
        self.cursor.execute("""
        INSERT INTO Patient_Data (PID, Admission_Status) VALUES (1, 'Yes');
        """)
        
        # Insert initial data into Feature_Store
        self.cursor.execute("""
        INSERT INTO Feature_Store (PID, Age, Sex, Min, Max, Mean, Standard_Deviation, Last_Result_Value, Latest_Result_Timestamp, No_of_Samples, Ready_for_Inference)
        VALUES (1, 40, 1, 10, 50, 30, 5, 420, '20240223120000', 10, 'No');
        """)
        self.conn.commit()

        # New feature values for update
        new_feature = {
            "Sex": 0,
            "Age": 45,
            "Min": 15,
            "Max": 55,
            "Mean": 35,
            "Standard_Deviation": 6,
            "Last_Result_Value": 430,
            "Latest_Result_Timestamp": "20240224120000",
            "No_of_Samples": 11,
            "Ready_for_Inference": "Yes"
        }
        update_feature_store(1, new_feature)

        # Verify the update
        self.cursor.execute("SELECT * FROM Feature_Store WHERE PID = 1")
        updated_record = self.cursor.fetchone()

        # Assertions
        self.assertEqual(updated_record[1], 0)  # Sex
        self.assertEqual(updated_record[2], 45)  # Age
        self.assertEqual(updated_record[10], "Yes")  # Ready_for_Inference


if __name__ == "__main__":
    unittest.main()
