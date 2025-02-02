# ML for software systems

### Docker setup
1. Install docker
2. `docker build -t single-container-system .`
3. `docker run -d --name ml_for_swe_system -p 5672:5672 -p 8440:8440 -p 8441:8441 single-container-system`
4. (Optional) `docker logs -f ml_for_swe_system` to see logs. Because we have to put everything in one dockerfile, all logs are annoyingly in one place.
5. Can also check stderr and stdout files (as defined in supervisord.conf) for debugging, e.g.: `docker exec -it ml_for_swe_system  cat /var/log/supervisor/consumer.stderr.log`