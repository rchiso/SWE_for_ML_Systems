import sqlite3
import os
from datetime import datetime

# Get database path
script_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(script_dir, "patient_database.db")


def connect_db():
    """Establish a connection to SQLite database."""
    return sqlite3.connect(db_path)


def handle_adt_a01(data):
    """Handles ADT^A01 signal - Patient Admission."""
    patient_id, age, sex_key = data
    sex_mapping = {"M": 0, "F": 1}
    sex = sex_mapping.get(sex_key, None)  # Ensure safe mapping
    print("Handling ADT")

    with connect_db() as conn:
        cursor = conn.cursor()

        # Insert into Patient_Data
        cursor.execute("""
            INSERT INTO Patient_Data (PID, Admission_Status)
            VALUES (?, ?);
        """, (patient_id, "Yes"))

        # Insert into Feature_Store with default NULL values
        cursor.execute("""
            INSERT INTO Feature_Store (PID, Sex, Age, Min, Max, Mean, Standard_Deviation,
                                       Last_Result_Value, Latest_Result_Timestamp, No_of_Samples, Ready_for_Inference)
            VALUES (?, ?, ?, NULL, NULL, NULL, NULL, NULL, NULL, 0, 'No');
        """, (patient_id, sex, age))

        conn.commit()


def handle_oru_a01(data):
    """Handles ORU^A01 signal - Lab Result Update and returns existing record for feature reconstruction."""
    patient_id, latest_result, latest_result_test_date = data

    print("Handling ORU")

    with connect_db() as conn:
        cursor = conn.cursor()

        # Check if patient exists in Feature_Store
        cursor.execute("SELECT * FROM Feature_Store WHERE PID = ?", (patient_id,))
        record = cursor.fetchone()

        if record:
            # Get column names from cursor description
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, record))  # Return as dictionary for feature reconstruction
        else:
            # Insert patient into Patient_Data (if missing)
            cursor.execute("""
                INSERT INTO Patient_Data (PID, Admission_Status, DOB, Admission_Date)
                VALUES (?, 'Pending', NULL, NULL);
            """, (patient_id,))

            # Insert new record into Feature_Store
            cursor.execute("""
                INSERT INTO Feature_Store (PID, Sex, Age, Min, Max, Mean, Standard_Deviation,
                                           Last_Result_Value, Latest_Result_Timestamp, No_of_Samples, Ready_for_Inference)
                VALUES (?, NULL, NULL, NULL, NULL, NULL, NULL, ?, ?, 1, 'No');
            """, (patient_id, latest_result, latest_result_test_date))

            conn.commit()
            return None  # Return None when patient was missing and newly added
