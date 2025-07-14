
FROM python:3.11-slim


RUN apt-get update && apt-get install -y --no-install-recommends \
    cron \
    gcc \
    python3-dev \
    musl-dev

RUN rm -rf /var/lib/apt/lists/*



WORKDIR /app


COPY requirements.txt .


RUN pip install --no-cache-dir -r requirements.txt


COPY crontab /etc/cron.d/etl-cron


RUN chmod 0644 /etc/cron.d/etl-cron


RUN crontab /etc/cron.d/etl-cron


COPY . .


RUN touch /var/log/cron.log


CMD cron && tail -f /var/log/cron.log