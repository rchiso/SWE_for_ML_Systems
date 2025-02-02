import pandas as pd
import sqlite3
import os
import random
from datetime import datetime, timedelta

# Load the file
file_path = "../history.csv"
dataset = pd.read_csv(file_path)

# Identify creatinine result and date columns
creatinine_date_cols = [col for col in dataset.columns if "creatinine_date" in col]
creatinine_results_cols = [col.replace("date", "result") for col in creatinine_date_cols]

# ---- Create aggregated features ----
if creatinine_results_cols:
    dataset['creatinine_mean'] = dataset[creatinine_results_cols].mean(axis=1)
    dataset['creatinine_max'] = dataset[creatinine_results_cols].max(axis=1)
    dataset['creatinine_min'] = dataset[creatinine_results_cols].min(axis=1)
    dataset['creatinine_std'] = dataset[creatinine_results_cols].std(axis=1, ddof=0)

# ---- Identify and store the latest creatinine test value ----
if creatinine_date_cols:
    # Convert to datetime
    dataset[creatinine_date_cols] = dataset[creatinine_date_cols].apply(pd.to_datetime, errors='coerce')
    # Find the column with the max date per row
    latest_date_idx = dataset[creatinine_date_cols].idxmax(axis=1)
    
    # Convert latest date column to its corresponding result column
    latest_result_column = latest_date_idx.apply(lambda x: x.replace('date_', 'result_') if pd.notna(x) else None)
    
    # Retrieve latest test values safely
    dataset['latest_test_value'] = [
        dataset.at[idx, col] if pd.notna(col) else None
        for idx, col in zip(dataset.index, latest_result_column)
    ]
    
    # Store latest timestamp
    dataset['latest_test_timestamp'] = [
        dataset.at[idx, col] if pd.notna(col) else None
        for idx, col in zip(dataset.index, latest_date_idx)
    ]

# ---- Generate Random Dates of Birth ----
dataset["DOB"] = [(datetime.now() - timedelta(days=random.randint(18*365, 90*365))).strftime("%Y-%m-%d") for _ in range(len(dataset))]

# ---- Convert DOB to Age ----
current_year = datetime.now().year
dataset["Age"] = dataset["DOB"].apply(lambda x: current_year - int(x[:4]))

# ---- Add Random Fake Values for Sex and Inference ----
dataset["Sex"] = [random.choice([0, 1]) for _ in range(len(dataset))]
dataset["Ready_for_Inference"] = [random.choice(["Yes", "No"]) for _ in range(len(dataset))]

# ---- Compute Number of Samples ----
dataset["No_of_Samples"] = dataset[creatinine_results_cols].notna().sum(axis=1)

# ---- Drop now-unneeded columns ----
dataset.drop(columns=creatinine_date_cols, inplace=True, errors='ignore')
dataset.drop(columns=creatinine_results_cols, inplace=True, errors='ignore')

# ---- Store as a new dataset ----
output_file_path = "processed_creatinine_data.csv"
dataset.to_csv(output_file_path, index=False)

# ---- Insert into SQLite database ----
script_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(script_dir, "patient_database.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Clear existing data in Patient_Data and Feature_Store
cursor.execute("DELETE FROM Feature_Store")
cursor.execute("DELETE FROM Patient_Data")
conn.commit()

# Insert data into Patient_Data
dataset_patient = dataset[["mrn", "DOB"]].copy()
dataset_patient.rename(columns={"mrn": "PID"}, inplace=True)
dataset_patient.drop_duplicates(subset=["PID"], inplace=True)
dataset_patient["Admission_Status"] = "Pending"
dataset_patient["Admission_Date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
# dataset_patient["Admission_Time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
dataset_patient.to_sql("Patient_Data", conn, if_exists="append", index=False)

# Insert data into Feature_Store
dataset.rename(columns={
    "mrn": "PID",
    "creatinine_min": "Min",
    "creatinine_max": "Max",
    "creatinine_mean": "Mean",
    "creatinine_std": "Standard_Deviation",
    "latest_test_value": "Last_Result_Value",
    "latest_test_timestamp": "Latest_Result_Timestamp"
}, inplace=True)

dataset = dataset[["PID", "Sex", "Age", "Min", "Max", "Mean", "Standard_Deviation", "Last_Result_Value", "Latest_Result_Timestamp", "No_of_Samples", "Ready_for_Inference"]]

dataset.to_sql("Feature_Store", conn, if_exists="append", index=False)

conn.commit()
conn.close()

# Display the processed dataset
print(f"Processed dataset saved to {output_file_path} and inserted into SQLite database {db_path}.")
