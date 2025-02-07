# ML for software systems

### Docker setup
1. Install docker
2. `docker build -t swe_for_ml_image .`
3. `docker run -d --name swe_for_ml_system -p 8400:8400 -p 8411:8411 -e MLLP_ADDRESS=localhost:8440 -e PAGER_ADDRESS=localhost:8441 swe_for_ml_image`
4. (Optional) `docker logs -f swe_for_ml_system` to see logs. Because we have to put everything in one dockerfile, all logs are annoyingly in one place.
5. Can also check stderr and stdout files (as defined in supervisord.conf) for debugging, e.g.: `docker exec -it swe_for_ml_system  cat /var/log/supervisor/consumer.stderr.log`
6. Run bash with: `docker exec -it swe_for_ml_system bash` (useful for digging into sqlite, among other things)


## Fresh Database Setup
1. Ensure history.csv is in your root.
2. Run create_db.py. This creates a database.
3. Run populate_db.py. This inserts the history.csv into Feature_store table. Also creates Patient_data table.
Note that ages and sexes will all be set to NULL.

### Use existing database
4. Alternatively, you can just work with patient_database.db file which already has a loaded history.csv
