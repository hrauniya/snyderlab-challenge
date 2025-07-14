# snyderlab-challenge
Stanford Snyder Lab two week challenge

#Task 1 (Ingestion)
The Ingestion is designed to handle two cases -- synthetic and non synthetic data. Assuming that the start date and end date endpoints are fixed in the future, we can set the IS_SYNTHETIC environment variable in the docker compose to false to ETL real data for a client.

However, for now the ETL is being done with IS_SYNTHETIC = True. Therefore, the ETL will be done for 30 days worth of data.

Run to build the Timescale DB container and the ETL container which will automatically start the daily ETL process configured through cron.
```
docker-compose up --build -d
```
