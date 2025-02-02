# ML for software systems

### Docker setup
1. Install docker
2. `docker build -t ml_for_swe_image .`
3. `docker run -d --name ml_for_swe_system -p 5672:5672 -p 8440:8440 -p 8441:8441 -p 15672:15672 ml_for_swe_image`
4. (Optional) `docker logs -f ml_for_swe_system` to see logs. Because we have to put everything in one dockerfile, all logs are annoyingly in one place.
5. Can also check stderr and stdout files (as defined in supervisord.conf) for debugging, e.g.: `docker exec -it ml_for_swe_system  cat /var/log/supervisor/consumer.stderr.log`
6. Run bash with: `docker exec -it ml_for_swe_system bash` (useful for digging into sqlite, among other things)
7. For rabbit mgmt console, will need to run these too and log in with these creds:
```
docker exec -it <container_id> rabbitmqctl add_user admin mypassword
docker exec -it <container_id> rabbitmqctl set_user_tags admin administrator
docker exec -it <container_id> rabbitmqctl set_permissions -p / admin ".*" ".*" ".*"
```


## Fresh Database Setup
1. Ensure history.csv is in your root.
2. Run create_db.py. This creates a database.
3. Run populate_db.py. This inserts the history.csv into Feature_store table. Also creates Patient_data table.
Note that ages, inference flags and sexes will all be randomly generated.

### Use existing database
4. Alternatively, you can just work with patient_database.db file which already has a loaded history.csv
