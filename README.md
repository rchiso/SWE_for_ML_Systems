# SWE_for_ML_Systems

## Making and deploying changes to Kubernetes
1. After you make any changes, build the image again.
   ```docker build --platform=linux/amd64 -t imperialswemlsspring2025.azurecr.io/coursework4-alameda .```
2. Push the image (need to login to azure, see below)
   ```docker push imperialswemlsspring2025.azurecr.io/coursework4-alameda```
3. In Kubernetes, stop the running pod (check pod-name via `kubectl get pods -n alameda`)
   ```kubectl delete pod <pod-name> -n alameda```
4. Kubernetes will automatically make a new pod using the new updated image. 
5. Export logs using
   ```kubectl logs --namespace=alameda -l app=aki-detection --tail=-1 > pod.log```
6. To see prometheus UI, forward the 9090 port from the prometheus service:
   ```kubectl port-forward -n alameda service/prometheus 9090:9090```
   Then, visit `http://localhost:9090`


### Azure login
1. `az login`
2. `az acr login --name imperialswemlsspring2025`

### Docker setup (outdated)
1. Install docker
2. `docker build -t swe_for_ml_image .`
3. `docker run -d --name swe_for_ml_system -e MLLP_ADDRESS=localhost:8440 -e PAGER_ADDRESS=localhost:8441 -p 9090:9090 swe_for_ml_image`
4. (Optional) `docker logs -f swe_for_ml_system` to see logs. Because we have to put everything in one dockerfile, all logs are in one place.
5. Run bash with: `docker exec -it swe_for_ml_system bash` (useful for digging into sqlite, among other things)


## Fresh Database Setup
1. Ensure history.csv is in your root.
2. Run create_db.py. This creates a database.
3. Run populate_db.py. This inserts the history.csv into Feature_store table. Also creates Patient_data table.
Note that ages and sexes will all be set to NULL.

### Use existing database
4. Alternatively, you can just work with patient_database.db file which already has a loaded history.csv

## Running Tests
Tests are present in `/tests` and each subdirectory has their owns tests as well. To run tests, use:

`python -m unittest <path_to_unittest_file>` 
