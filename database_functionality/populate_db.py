import pandas as pd
import sqlite3
import os
import random
from datetime import datetime, timedelta

def process_creatinine_data(file_path):
    """
    Loads the CSV, computes creatinine aggregated features,
    extracts the latest creatinine test result and timestamp,
    counts the number of valid samples and drops the unneeded columns.
    """
    dataset = pd.read_csv(file_path)
    
    # Identify creatinine date and corresponding result columns
    creatinine_date_cols = [col for col in dataset.columns if "creatinine_date" in col]
    creatinine_results_cols = [col.replace("date", "result") for col in creatinine_date_cols]
    
    # Create aggregated creatinine features if applicable
    if creatinine_results_cols:
        dataset['creatinine_mean'] = dataset[creatinine_results_cols].mean(axis=1)
        dataset['creatinine_max'] = dataset[creatinine_results_cols].max(axis=1)
        dataset['creatinine_min'] = dataset[creatinine_results_cols].min(axis=1)
        dataset['creatinine_std'] = dataset[creatinine_results_cols].std(axis=1, ddof=0)
    
    # Identify and store the latest creatinine test value and timestamp
    if creatinine_date_cols:
        # Convert date columns to datetime
        dataset[creatinine_date_cols] = dataset[creatinine_date_cols].apply(pd.to_datetime, errors='coerce')
        # Find the column with the maximum date per row
        latest_date_idx = dataset[creatinine_date_cols].idxmax(axis=1)
        # Determine corresponding result column (assumes naming like date_X and result_X)
        latest_result_column = latest_date_idx.apply(
            lambda x: x.replace('date_', 'result_') if pd.notna(x) else None
        )
        # Safely retrieve the latest test result and timestamp
        dataset['latest_test_value'] = [
            dataset.at[idx, col] if pd.notna(col) else None
            for idx, col in zip(dataset.index, latest_result_column)
        ]
        dataset['latest_test_timestamp'] = [
            dataset.at[idx, col].strftime("%Y%m%d%H%M%S") if pd.notna(col) else None
            for idx, col in zip(dataset.index, latest_date_idx)
        ]
    
    # Compute number of valid creatinine samples
    dataset["No_of_Samples"] = dataset[creatinine_results_cols].notna().sum(axis=1)
    
    # Drop the original creatinine date/result columns
    dataset.drop(columns=creatinine_date_cols, inplace=True, errors='ignore')
    dataset.drop(columns=creatinine_results_cols, inplace=True, errors='ignore')
    
    return dataset

def add_demographics(dataset, use_random=True):
    """
    Adds demographic information (DOB, Age, Sex, Ready_for_Inference) to the dataset.
    
    If use_random is True:
      - Generates a random DOB (between 18 and 90 years ago)
      - Computes Age from DOB
      - Randomly assigns Sex and Ready_for_Inference.
      
    Otherwise, the demographic columns are set to None.
    """
    if use_random:
        # Generate random date of birth between 18 and 90 years ago
        dataset["DOB"] = [
            (datetime.now() - timedelta(days=random.randint(18 * 365, 90 * 365))).strftime("%Y%m%d")
            for _ in range(len(dataset))
        ]
        # Convert DOB to Age
        current_year = datetime.now().year
        dataset["Age"] = dataset["DOB"].apply(lambda x: current_year - int(x[:4]))
        # Randomly assign Sex (0 or 1) and Ready_for_Inference ("Yes" or "No")
        dataset["Sex"] = [random.choice([0, 1]) for _ in range(len(dataset))]
        dataset["Ready_for_Inference"] = [random.choice(["Yes", "No"]) for _ in range(len(dataset))]
    else:
        # Do not generate demographic data: set these columns to None
        dataset["DOB"] = None
        dataset["Age"] = None
        dataset["Sex"] = None
        dataset["Ready_for_Inference"] = "No"
    return dataset

def insert_into_database(dataset, db_path, use_random=True):
    """
    Inserts data into the SQLite database.
    
    First, the Feature_Store table is populated (after renaming columns).
    Then the Patient_Data table is updated:
      - If use_random is True, the patient data (PID, DOB, Admission_Status, Admission_Date)
        are inserted based on the dataset’s original demographic data.
      - If use_random is False, for every PID in Feature_Store a row is inserted into Patient_Data
        with only the patient ID (all other fields are left as null).
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Clear existing data
    cursor.execute("DELETE FROM Feature_Store")
    cursor.execute("DELETE FROM Patient_Data")
    conn.commit()
    
    # --- Prepare Patient_Data insertion BEFORE renaming for Feature_Store ---
    if use_random:
        # Use the original 'mrn' column and DOB (generated above)
        patient_data = dataset[['mrn', 'DOB']].drop_duplicates(subset=['mrn']).copy()
        patient_data.rename(columns={'mrn': 'PID'}, inplace=True)
        patient_data["Admission_Status"] = "Pending"
        patient_data["Admission_Date"] = datetime.now().strftime("%Y%m%d%H%M")
    else:
        # Non-random mode: for every PID in Feature_Store, add a row with other fields null.
        pids = dataset['mrn'].drop_duplicates()
        patient_data = pd.DataFrame({'PID': pids})
        patient_data["DOB"] = None
        patient_data["Admission_Status"] = "Pending"
        patient_data["Admission_Date"] = None

    # --- Insert into Feature_Store ---
    # Create a copy so that we can rename columns without affecting the patient_data extraction above.
    fs_dataset = dataset.copy()
    fs_dataset.rename(columns={
        "mrn": "PID",
        "creatinine_min": "Min",
        "creatinine_max": "Max",
        "creatinine_mean": "Mean",
        "creatinine_std": "Standard_Deviation",
        "latest_test_value": "Last_Result_Value",
        "latest_test_timestamp": "Latest_Result_Timestamp"
    }, inplace=True)
    
    # Order the columns as required by Feature_Store
    feature_store_cols = ["PID", "Sex", "Age", "Min", "Max", "Mean", "Standard_Deviation",
                            "Last_Result_Value", "Latest_Result_Timestamp", "No_of_Samples", "Ready_for_Inference"]
    fs_dataset = fs_dataset[feature_store_cols]
    
    fs_dataset.to_sql("Feature_Store", conn, if_exists="append", index=False)
    
    # --- Insert into Patient_Data ---
    patient_data.to_sql("Patient_Data", conn, if_exists="append", index=False)
    
    conn.commit()
    conn.close()

def main(use_random=True):
    # File paths
    file_path = os.path.join(os.path.dirname(__file__), "../history.csv")
    output_file_path = "processed_creatinine_data.csv"
    
    # Process the CSV to compute creatinine features
    dataset = process_creatinine_data(file_path)
    
    # Add demographic information according to the flag
    dataset = add_demographics(dataset, use_random=use_random)
    
    # Save the processed dataset to CSV
    dataset.to_csv(output_file_path, index=False)
    
    # Determine the SQLite database path (relative to this script)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(script_dir, "patient_database.db")
    
    # Insert the processed data into the database
    insert_into_database(dataset, db_path, use_random=use_random)
    
    print(f"Processed dataset saved to {output_file_path} and inserted into SQLite database {db_path}.")

if __name__ == "__main__":
    # Set use_random to True to generate Sex, Age, Ready_for_Inference randomly.
    # Set use_random to False to insert, for every PID, a patient record in Patient_Data with null values.
    main(use_random=False)  # Change to False if you do not want random demographic data.
