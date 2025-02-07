import sqlite3
import os
from datetime import datetime

# ----------------------------------------------------------------
# Database Setup: Clear all data from the tables
# ----------------------------------------------------------------

# Get the database path (assumes patient_database.db is in the same directory)
script_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(script_dir, "patient_database.db")

def clear_tables():
    """Delete all records from Patient_Data and Feature_Store."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    print("Clearing all data from Patient_Data and Feature_Store...")
    cursor.execute("DELETE FROM Patient_Data;")
    cursor.execute("DELETE FROM Feature_Store;")
    conn.commit()
    conn.close()
    print("All tables cleared.\n")

# ----------------------------------------------------------------
# Provided Function Definitions 
# ----------------------------------------------------------------

def connect_db():
    """Establish a connection to SQLite database."""
    return sqlite3.connect(db_path)

def handle_adt_a01(data):
    """Handles ADT^A01 signal - Patient Admission."""
    patient_id, age, sex_key = data
    sex_mapping = {"M": 0, "F": 1}
    sex = sex_mapping.get(sex_key)  # Safe mapping; returns None if key not found
    print(f"\n[ADT] Handling admission for patient {patient_id}")

    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Patient_Data WHERE PID = ?", (patient_id,))
        record = cursor.fetchone()

        # If the record exists, update it
        if record:
            if sex is None and age is None:
                print("[ADT] No update as both age and sex are missing.")
                return None

            cursor.execute("UPDATE Patient_Data SET Admission_Status = ? WHERE PID = ?", ('Yes', patient_id))

            if sex is not None and age is not None:
                cursor.execute("UPDATE Feature_Store SET Age = ?, Sex = ? WHERE PID = ?", (age, sex, patient_id))
            elif sex is not None:
                cursor.execute("UPDATE Feature_Store SET Sex = ? WHERE PID = ?", (sex, patient_id))
            elif age is not None:
                cursor.execute("UPDATE Feature_Store SET Age = ? WHERE PID = ?", (age, patient_id))

            conn.commit()
            cursor.execute("SELECT * FROM Feature_Store WHERE PID = ?", (patient_id,))
            updated_record = cursor.fetchone()
            columns = [desc[0] for desc in cursor.description]
            result = dict(zip(columns, updated_record))
            print("[ADT] Updated Feature_Store record:", result)
            return result

        # If no record exists, admit the patient for the first time.
        else:
            cursor.execute("""
                INSERT INTO Patient_Data (PID, Admission_Status)
                VALUES (?, ?);
            """, (patient_id, "Yes"))
            cursor.execute("""
                INSERT INTO Feature_Store (PID, Sex, Age, Min, Max, Mean, Standard_Deviation,
                                           Last_Result_Value, Latest_Result_Timestamp, No_of_Samples, Ready_for_Inference)
                VALUES (?, ?, ?, NULL, NULL, NULL, NULL, NULL, NULL, 0, 'No');
            """, (patient_id, sex, age))
            conn.commit()
            print(f"[ADT] New patient admitted with PID {patient_id}")
            return None

def handle_oru_a01(data):
    """Handles ORU^A01 signal - Lab Result Update and returns existing record for feature reconstruction."""
    patient_id, latest_result, latest_result_test_date = data
    print(f"\n[ORU] Handling lab update for patient {patient_id}")

    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Feature_Store WHERE PID = ?", (patient_id,))
        record = cursor.fetchone()

        if record:
            columns = [desc[0] for desc in cursor.description]
            result = dict(zip(columns, record))
            print("[ORU] Existing record in Feature_Store:", result)
            return result
        else:
            cursor.execute("""
                INSERT INTO Patient_Data (PID, Admission_Status, DOB, Admission_Date)
                VALUES (?, 'Pending', NULL, NULL);
            """, (patient_id,))
            cursor.execute("""
                INSERT INTO Feature_Store (PID, Sex, Age, Min, Max, Mean, Standard_Deviation,
                                           Last_Result_Value, Latest_Result_Timestamp, No_of_Samples, Ready_for_Inference)
                VALUES (?, NULL, NULL, NULL, NULL, NULL, NULL, ?, ?, 1, 'No');
            """, (patient_id, latest_result, latest_result_test_date))
            conn.commit()
            print(f"[ORU] New record created via ORU for patient {patient_id}")
            return None

# ----------------------------------------------------------------
# Test Scenarios
# ----------------------------------------------------------------

# Define test cases for ADT^A01 (patient admissions/updates)
adt_test_cases = [
    { "flag": "new_patient_complete", 
      "data": ("1001", 30, "M"), 
      "description": "New patient with complete data" },
    { "flag": "update_existing", 
      "data": ("1004", 35, "F"), 
      "description": "Update existing patient (PID 1001) with new age and sex" }
]

# Define test cases for ORU^A01 (lab result updates)
oru_test_cases = [
    { "flag": "update_existing_lab", 
      "data": ("1001", 98.7, "20250205123000"), 
      "description": "Lab result update for existing patient (PID 1001)" },
    { "flag": "new_patient_lab", 
      "data": ("1004", 100.1, "20250205124500"), 
      "description": "Lab result update for non-existent patient (PID 1004), should create a new record" },
    { "flag": "new_patient_lab", 
      "data": ("1004", 200, "20250205145000"), 
      "description": "Lab result update for non-existent patient (PID 1004), should create a new record" }
]

def run_test_scenarios():
    print("=== Running ADT^A01 Test Scenarios ===")

    print("\n=== Running ORU^A01 Test Scenarios ===")
    for test in oru_test_cases:
        print(f"\n[Test Flag: {test['flag']}] {test['description']}")
        handle_oru_a01(test["data"])

    for test in adt_test_cases:
        print(f"\n[Test Flag: {test['flag']}] {test['description']}")
        handle_adt_a01(test["data"])

if __name__ == "__main__":
    # Clear all tables before running tests.
    clear_tables()
    run_test_scenarios()
