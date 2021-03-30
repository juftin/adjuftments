#!/usr/bin/env bash

set -e
COMMAND="${@}"

log_event() {
  LOGGING_TIMESTAMP=$(date +"%F %T.%3N")
  echo "${LOGGING_TIMESTAMP} [    INFO]: ${1}"
}

# CAPTURE THE ROOT OF THE DATASCIENCE DIR TO ASSIST WITH SCRIPTS / CLEANUP
BUILD_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
ADJUFTMENTS_DIR=$(dirname ${BUILD_DIR})
DOT_ENV_FILE="${ADJUFTMENTS_DIR}/.env"

if [ -f ${DOCKER_ALIAS_FILE} ]; then
  source ${DOT_ENV_FILE}
  log_event "Credentials set... connecting to Postgres"
else
  log_event "Credentials not set... exiting"
  exit 1
fi

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
