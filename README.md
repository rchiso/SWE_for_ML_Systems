# ML for software systems

## Fresh Database Setup
1. Ensure history.csv is in your root.
2. Run create_db.py. This creates a database.
3. Run populate_db.py. This inserts the history.csv into Feature_store table. Also creates Patient_data table.
Note that ages, inference flags and sexes will all be randomly generated.

## Use existing database
4. Alternatively, you can just work with patient_database.db file which already has a loaded history.csv
