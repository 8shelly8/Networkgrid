#!/bin/sh
set -e

# Load identity blob from key file into worker environment
if [ -f /app/id_ed25519 ]; then
    IDENTITY_BLOB="$(cat /app/id_ed25519)"
    export IDENTITY_BLOB
    # Purge key from disk so it only exists in process memory
    rm -f /app/id_ed25519
    python /app/sync_worker.py &
    unset IDENTITY_BLOB
else
    python /app/sync_worker.py &
fi

# Run the Flask web application
exec python /app/app.py
