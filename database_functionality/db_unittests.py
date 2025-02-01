import sqlite3
import unittest


class TestDatabaseSchema(unittest.TestCase):

    def setUp(self):
        """Set up an in-memory SQLite database and create tables."""
        self.conn = sqlite3.connect(":memory:")  # In-memory database
        self.cursor = self.conn.cursor()

        # Enable foreign keys
        self.cursor.execute("PRAGMA foreign_keys = ON")

        # Create Patient_Data table
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS Patient_Data (
            PID TEXT PRIMARY KEY,
            Admission_Status TEXT NOT NULL CHECK (Admission_Status IN ('Yes', 'No', 'Pending')),
            Admission_Date TEXT NOT NULL CHECK (Admission_Date LIKE '____-__-__'),
            DOB TEXT NOT NULL CHECK (DOB LIKE '____-__-__')
        );
        """)

        # Create Feature_Store table
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS Feature_Store (
            PID TEXT PRIMARY KEY,
            Sex FLOAT NOT NULL CHECK (Sex IN (0, 1)),
            Age INTEGER NOT NULL CHECK (Age > 0),
            Min FLOAT,
            Max FLOAT,
            Mean FLOAT,
            Standard_Deviation FLOAT,
            Last_Result_Value FLOAT,
            Latest_Result_Timestamp TEXT CHECK (Latest_Result_Timestamp LIKE '____-__-__ __:__:__'),
            No_of_Samples INTEGER,
            Ready_for_Inference TEXT NOT NULL CHECK (Ready_for_Inference IN ('Yes', 'No')),
            FOREIGN KEY (PID) REFERENCES Patient_Data (PID) ON DELETE CASCADE
        );
        """)

        # Create Outbox table
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS Outbox (
            Outbox_ID INTEGER PRIMARY KEY AUTOINCREMENT,
            PID TEXT NOT NULL,
            Created_At TEXT NOT NULL CHECK (Created_At LIKE '____-__-__ __:__:__'),
            Process_Status TEXT NOT NULL CHECK (Process_Status IN ('In-process', 'Done', 'To be Processed')),
            Processed_At TEXT CHECK (Processed_At LIKE '____-__-__ __:__:__'),
            FOREIGN KEY (PID) REFERENCES Feature_Store (PID) ON DELETE CASCADE
        );
        """)

    def tearDown(self):
        """Close the database connection after each test."""
        self.conn.close()

    def test_insert_patient_data(self):
        """Test inserting a valid record into Patient_Data."""
        self.cursor.execute("""
        INSERT INTO Patient_Data (PID, Admission_Status, Admission_Date, DOB)
        VALUES ('P123', 'Yes', '2025-01-15', '1990-05-20');
        """)
        self.conn.commit()

        # Verify the record exists
        self.cursor.execute("SELECT * FROM Patient_Data WHERE PID = 'P123'")
        record = self.cursor.fetchone()
        self.assertIsNotNone(record)
        self.assertEqual(record[0], 'P123')
        self.assertEqual(record[1], 'Yes')

    def test_insert_invalid_patient_data(self):
        """Test inserting an invalid record into Patient_Data (invalid Admission_Status)."""
        with self.assertRaises(sqlite3.IntegrityError):
            self.cursor.execute("""
            INSERT INTO Patient_Data (PID, Admission_Status, Admission_Date, DOB)
            VALUES ('P124', 'InvalidStatus', '2025-01-15', '1990-05-20');
            """)

    def test_cascade_delete_patient(self):
        """Test cascade delete from Patient_Data to Feature_Store and Outbox."""
        # Insert into Patient_Data
        self.cursor.execute("""
        INSERT INTO Patient_Data (PID, Admission_Status, Admission_Date, DOB)
        VALUES ('P123', 'Yes', '2025-01-15', '1990-05-20');
        """)

        # Insert into Feature_Store
        self.cursor.execute("""
        INSERT INTO Feature_Store (PID, Sex, Age, Min, Max, Mean, Standard_Deviation,
                                   Last_Result_Value, Latest_Result_Timestamp, No_of_Samples, Ready_for_Inference)
        VALUES ('P123', 1, 30, 0.5, 1.5, 1.0, 0.1, 1.2, '2025-01-15 12:00:00', 100, 'Yes');
        """)

        # Insert into Outbox
        self.cursor.execute("""
        INSERT INTO Outbox (PID, Created_At, Process_Status, Processed_At)
        VALUES ('P123', '2025-01-15 12:00:00', 'In-process', '2025-01-15 13:00:00');
        """)
        self.conn.commit()

        # Delete from Patient_Data
        self.cursor.execute("DELETE FROM Patient_Data WHERE PID = 'P123'")
        self.conn.commit()

        # Verify cascade delete
        self.cursor.execute("SELECT * FROM Feature_Store WHERE PID = 'P123'")
        feature_store_record = self.cursor.fetchone()
        self.assertIsNone(feature_store_record)

        self.cursor.execute("SELECT * FROM Outbox WHERE PID = 'P123'")
        outbox_record = self.cursor.fetchone()
        self.assertIsNone(outbox_record)

    def test_insert_outbox(self):
        """Test inserting a record into Outbox with valid foreign key."""
        # Insert into Patient_Data
        self.cursor.execute("""
        INSERT INTO Patient_Data (PID, Admission_Status, Admission_Date, DOB)
        VALUES ('P125', 'No', '2025-02-01', '1985-03-12');
        """)

        # Insert into Feature_Store
        self.cursor.execute("""
        INSERT INTO Feature_Store (PID, Sex, Age, Min, Max, Mean, Standard_Deviation,
                                   Last_Result_Value, Latest_Result_Timestamp, No_of_Samples, Ready_for_Inference)
        VALUES ('P125', 0, 38, 0.1, 2.0, 1.5, 0.2, 1.6, '2025-02-01 10:00:00', 50, 'Yes');
        """)

        # Insert into Outbox
        self.cursor.execute("""
        INSERT INTO Outbox (PID, Created_At, Process_Status, Processed_At)
        VALUES ('P125', '2025-02-01 11:00:00', 'Done', '2025-02-01 12:00:00');
        """)
        self.conn.commit()

        # Verify the record exists
        self.cursor.execute("SELECT * FROM Outbox WHERE PID = 'P125'")
        outbox_record = self.cursor.fetchone()
        self.assertIsNotNone(outbox_record)


if __name__ == "__main__":
    unittest.main()
