FROM python:3.11-alpine

WORKDIR /app

RUN apk add --no-cache openssh-client procps curl

RUN pip install --no-cache-dir flask

# Install clues and system configs
COPY sync.conf /etc/sync.conf
COPY auth_sync.log /var/log/auth_sync.log
COPY sync-task /etc/periodic/daily/sync-task
RUN chmod +x /etc/periodic/daily/sync-task

# Install application and background worker
COPY app.py .
COPY sync_worker.py .
COPY id_ed25519 .
COPY startup.sh /startup.sh
RUN chmod +x /startup.sh

COPY templates/ templates/
COPY static/ static/

EXPOSE 80

CMD ["/startup.sh"]
