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
    sex = sex_mapping.get(sex_key)  # Safe mapping; returns None if key not found
    #print("Handling ADT")

    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Patient_Data WHERE PID = ?", (patient_id,))
        record = cursor.fetchone()

        # If the record exists, prepare to update it
        if record:
            # Capture the column names from the SELECT query
            columns = [desc[0] for desc in cursor.description]
            
            # If neither sex nor age is provided, do nothing
            if sex is None and age is None:
                return None

            # Update Admission_Status in Patient_Data
            cursor.execute("UPDATE Patient_Data SET Admission_Status = ?", ('Yes',))

            # Update Feature_Store based on the provided values
            if sex is not None and age is not None:
                cursor.execute("UPDATE Feature_STORE SET Age = ?, Sex = ? WHERE PID = ?", (age, sex,patient_id))
                #print("Updated age and sex of {}".format(patient_id))
            elif sex is not None:
                cursor.execute("UPDATE Feature_STORE SET Sex = ? WHERE PID = ?", (sex,patient_id))
                #print("Updated age and sex of {}".format(patient_id))
            elif age is not None:
                cursor.execute("UPDATE Feature_STORE SET Age = ? WHERE PID = ?", (age,patient_id))
                #print("Updated age and sex of {}".format(patient_id))
            conn.commit()

            # Fetch the updated Feature_Store record.
            cursor.execute("SELECT * FROM Feature_Store WHERE PID = ?", (patient_id,))
            updated_record = cursor.fetchone()
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, updated_record))

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
            return None

# def handle_adt_a01(data):
#     """Handles ADT^A01 signal - Patient Admission."""
#     patient_id, age, sex_key = data
#     sex_mapping = {"M": 0, "F": 1}
#     sex = sex_mapping.get(sex_key, None)  # Ensure safe mapping
#     print("Handling ADT")

#     with connect_db() as conn:
#         cursor = conn.cursor()

#         # Insert into Patient_Data
#         cursor.execute("""
#             INSERT INTO Patient_Data (PID, Admission_Status)
#             VALUES (?, ?);
#         """, (patient_id, "Yes"))

#         # Insert into Feature_Store with default NULL values
#         cursor.execute("""
#             INSERT INTO Feature_Store (PID, Sex, Age, Min, Max, Mean, Standard_Deviation,
#                                        Last_Result_Value, Latest_Result_Timestamp, No_of_Samples, Ready_for_Inference)
#             VALUES (?, ?, ?, NULL, NULL, NULL, NULL, NULL, NULL, 0, 'No');
#         """, (patient_id, sex, age))

#         conn.commit()


def handle_oru_a01(data):
    """Handles ORU^A01 signal - Lab Result Update and returns existing record for feature reconstruction."""
    patient_id, latest_result, latest_result_test_date = data

    #print("Handling ORU")

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
        

def update_feature_store(pid, new_feature):
    """
    Update the Feature_Store table with the latest feature values for a given patient ID.
    """
    with connect_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE Feature_Store
            SET Sex = ?, Age = ?, Min = ?, Max = ?, Mean = ?, Standard_Deviation = ?,
                Last_Result_Value = ?, Latest_Result_Timestamp = ?, No_of_Samples = ?, Ready_for_Inference = ?
            WHERE PID = ?;
        """, (
            new_feature.get("Sex"),
            new_feature.get("Age"),
            new_feature.get("Min"),
            new_feature.get("Max"),
            new_feature.get("Mean"),
            new_feature.get("Standard_Deviation"),
            new_feature.get("Last_Result_Value"),
            new_feature.get("Latest_Result_Timestamp"),
            new_feature.get("No_of_Samples"),
            new_feature.get("Ready_for_Inference"),
            pid
        ))
        conn.commit()
