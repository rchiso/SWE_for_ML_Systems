"""
create_db.py

This script initializes an SQLite database and creates necessary tables. 

Usage:
    Run this script to create or update the database schema.
    WARNING: Rerunning this script after intial db connection

Author: Hemal Munbodh
Date: 01/02/2025
"""
import sqlite3
import os

# Get the current directory of the script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Construct the path to the database file in the same directory as the script
db_path = os.path.join(script_dir, "patient_database.db")

# Warning delete
DELETE_EXISTING_DB = True
if DELETE_EXISTING_DB:
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Existing database '{db_path}' deleted.")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Enable foreign keys (IMPORTANT)
cursor.execute("PRAGMA foreign_keys = ON")

# Create a 'Patient_Data' table
cursor.execute("""
CREATE TABLE IF NOT EXISTS Patient_Data (
    PID INTEGER PRIMARY KEY,
    Admission_Status TEXT NOT NULL CHECK (Admission_Status IN ('Yes', 'No', 'Pending')),
    Admission_Date TEXT NULL CHECK (Admission_Date LIKE '____________'),
    DOB TEXT NULL CHECK (DOB LIKE '________'));
""")

# Create the 'Feature_Store' table
cursor.execute("""
CREATE TABLE IF NOT EXISTS Feature_Store (
    PID TEXT PRIMARY KEY,  -- Foreign key from Patient_Data
    Sex FLOAT CHECK (Sex IN (0, 1)),  -- 0: Male, 1: Female. NULL if receive LIMS before PAS
    Age INTEGER CHECK (Age > 0), -- NULL if receive LIMS before PAS. Need to be computed from DOB in Patient Data
    Min FLOAT,
    Max FLOAT,
    Mean FLOAT,
    Standard_Deviation FLOAT,
    Last_Result_Value FLOAT,
    Latest_Result_Timestamp TEXT CHECK (Latest_Result_Timestamp LIKE '____________'),
    No_of_Samples INTEGER ,
    Ready_for_Inference TEXT NOT NULL CHECK (Ready_for_Inference IN ('Yes', 'No')),
    FOREIGN KEY (PID) REFERENCES Patient_Data (PID) ON DELETE CASCADE
);
""")

# # Create the 'Outbox' table
# cursor.execute("""
# CREATE TABLE IF NOT EXISTS Outbox (
#     Outbox_ID INTEGER PRIMARY KEY AUTOINCREMENT,
#     PID TEXT NOT NULL,  -- Foreign key from Feature_Store. -- If you have an insertion into outbox, then PID cannot be empty
#     Created_At TEXT NOT NULL CHECK (Created_At LIKE '____-__-__ __:__:__'),
#     Process_Status TEXT NOT NULL CHECK (Process_Status IN ('In-process', 'Done', 'To be Processed')),
#     Processed_At TEXT CHECK (Processed_At LIKE '____-__-__ __:__:__'),
#     FOREIGN KEY (PID) REFERENCES Feature_Store (PID) ON DELETE CASCADE
# );
# """)


conn.commit()
print("patient_database created!")
conn.close()

