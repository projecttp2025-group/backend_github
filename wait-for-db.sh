#!/bin/sh
# wait-for-db.sh — waits until Postgres is accepting connections
set -e
host=$DB_HOST
port=$DB_PORT
tries=0
max_tries=${DB_WAIT_TRIES:-60}

printf "Waiting for postgres at %s:%s...\n" "$host" "$port"
while ! pg_isready -h "$host" -p "$port" >/dev/null 2>&1; do
  tries=$((tries+1))
  if [ "$tries" -ge "$max_tries" ]; then
    printf "Timed out waiting for Postgres (%s tries)\n" "$tries" >&2
    exit 1
  fi
  sleep 1
done
printf "Postgres is ready\n"

exit 0
