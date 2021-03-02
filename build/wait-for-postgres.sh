#!/bin/sh

set -e

COMMAND="${@}"

log_event() {
  LOGGING_TIMESTAMP=$(date +"%F %T.%3N")
  echo "${LOGGING_TIMESTAMP} [    INFO]: ${1}"
}

until PGPASSWORD=${DATABASE_PASSWORD} psql --host="${DATABASE_HOST}" --username="${DATABASE_USER}" --dbname=${DATABASE_DB} --command='\q'; do
  log_event "Postgres Unavailable, Waiting..."
  sleep 3
done

# CREATE A POSTGRES ROLE IF IT DOESN'T EXIST - PREVENT NOISEY LOGGING ABOUT IT
if [ "${DATABASE_USER}" != "postgres" ]; then
  PGPASSWORD=$DATABASE_PASSWORD psql --host="${DATABASE_HOST}" --username="${DATABASE_USER}" --dbname=${DATABASE_DB} --command="DROP ROLE IF EXISTS postgres; CREATE ROLE postgres LOGIN PASSWORD '${DATABASE_PASSWORD}';"
fi

log_event "Postgres is Ready, Beginning..."
exec ${COMMAND}
