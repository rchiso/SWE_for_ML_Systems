import unittest
import sqlite3
from unittest.mock import patch

class TestDatabaseOperations(unittest.TestCase):

    def setUp(self):
        """Set up an in-memory SQLite database and create tables for testing."""
        self.conn = sqlite3.connect(":memory:")  # Use in-memory database for testing
        self.conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints
        self.cursor = self.conn.cursor()

        # Create Patient_Data table
        self.cursor.execute("""
        CREATE TABLE Patient_Data (
            PID INTEGER PRIMARY KEY,
            Admission_Status TEXT NOT NULL CHECK (Admission_Status IN ('Yes', 'No', 'Pending')),
            Admission_Date TEXT NULL CHECK (Admission_Date LIKE '________'),
            DOB TEXT NULL CHECK (DOB LIKE '________')
        );
        """)

        # Create Feature_Store table
        self.cursor.execute("""
        CREATE TABLE Feature_Store (
            PID INTEGER PRIMARY KEY,
            Sex FLOAT CHECK (Sex IN (0, 1)),
            Age INTEGER CHECK (Age > 0),
            Min FLOAT,
            Max FLOAT,
            Mean FLOAT,
            Standard_Deviation FLOAT,
            Last_Result_Value FLOAT,
            Latest_Result_Timestamp TEXT CHECK (Latest_Result_Timestamp LIKE '______________'),
            No_of_Samples INTEGER,
            Ready_for_Inference TEXT NOT NULL CHECK (Ready_for_Inference IN ('Yes', 'No')),
            FOREIGN KEY (PID) REFERENCES Patient_Data (PID) ON DELETE CASCADE
        );
        """)

    def tearDown(self):
        """Close the database connection after each test."""
        self.conn.close()

    def test_insert_patient_data(self):
        """Test inserting a valid record into the Patient_Data table."""
        self.cursor.execute("""
        INSERT INTO Patient_Data (PID, Admission_Status, Admission_Date, DOB)
        VALUES (1, 'Yes', '20240223', '19800520');
        """)
        self.conn.commit()

        # Verify insertion
        self.cursor.execute("SELECT * FROM Patient_Data WHERE PID = 1;")
        record = self.cursor.fetchone()
        self.assertIsNotNone(record)
        self.assertEqual(record[0], 1)  # PID
        self.assertEqual(record[1], 'Yes')  # Admission_Status

    def test_insert_invalid_patient_data(self):
        """Test inserting invalid data into Patient_Data (should fail)."""
        with self.assertRaises(sqlite3.IntegrityError):
            self.cursor.execute("""
            INSERT INTO Patient_Data (PID, Admission_Status, Admission_Date, DOB)
            VALUES (1, 'Invalid_Status', '20240223', '19800520');
            """)

    def test_cascade_delete_patient(self):
        """Test cascade delete from Patient_Data to Feature_Store."""
        # Insert data into Patient_Data
        self.cursor.execute("""
        INSERT INTO Patient_Data (PID, Admission_Status, Admission_Date, DOB)
        VALUES (1, 'Yes', '20240223', '19800520');
        """)

        # Insert data into Feature_Store
        self.cursor.execute("""
        INSERT INTO Feature_Store (PID, Sex, Age, Min, Max, Mean, Standard_Deviation,
                                   Last_Result_Value, Latest_Result_Timestamp, No_of_Samples, Ready_for_Inference)
        VALUES (1, 1, 40, 10.0, 20.0, 15.0, 2.0, 18.0, '20240223120000', 5, 'Yes');
        """)
        self.conn.commit()

        # Delete the patient
        self.cursor.execute("DELETE FROM Patient_Data WHERE PID = 1;")
        self.conn.commit()

        # Verify cascade delete
        self.cursor.execute("SELECT * FROM Feature_Store WHERE PID = 1;")
        feature_record = self.cursor.fetchone()
        self.assertIsNone(feature_record)

    def test_update_patient_data(self):
        """Test updating a record in Patient_Data."""
        self.cursor.execute("""
        INSERT INTO Patient_Data (PID, Admission_Status, Admission_Date, DOB)
        VALUES (1, 'No', '20240223', '19800520');
        """)
        self.conn.commit()

        # Update Admission_Status
        self.cursor.execute("""
        UPDATE Patient_Data
        SET Admission_Status = 'Yes'
        WHERE PID = 1;
        """)
        self.conn.commit()

        # Verify update
        self.cursor.execute("SELECT Admission_Status FROM Patient_Data WHERE PID = 1;")
        updated_status = self.cursor.fetchone()[0]
        self.assertEqual(updated_status, 'Yes')


if __name__ == "__main__":
    unittest.main()
