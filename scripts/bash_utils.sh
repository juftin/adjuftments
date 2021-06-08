#!/usr/bin/env bash

set -e

SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
ADJUFTMENTS_DIR=$(dirname ${SCRIPTS_DIR})
DOT_ENV_FILE="${ADJUFTMENTS_DIR}/.env"

function log_event() {
  LOGGING_TIMESTAMP=$(date +"%F %T.%3N")
  echo "${LOGGING_TIMESTAMP} [    INFO]: ${1}"
}

function set_environment_variables() {
  if [[ -f ${DOT_ENV_FILE} ]]; then
    source ${DOT_ENV_FILE}
    log_event "Credentials set..."
  else
    log_event "Credentials not set... exiting"
    exit 1
  fi
}

set_environment_variables

function psql_check_database() {
  PGPASSWORD=${DATABASE_PASSWORD} \
    psql \
    --host="${DATABASE_HOST}" \
    --username="${DATABASE_USER}" \
    --dbname=${DATABASE_DB} \
    --command='\q'
}

function wait_for_database() {
  until $(psql_check_database); do
    log_event "Postgres Unavailable, Waiting..."
    sleep 3
  done
}

function psql_db_user() {
  PGPASSWORD=${DATABASE_PASSWORD} \
    psql \
    --host="${DATABASE_HOST}" \
    --username="${DATABASE_USER}" \
    --dbname=${DATABASE_DB} \
    --no-align \
    --tuples-only \
    --command "SELECT 1 FROM pg_roles WHERE rolname='${1}'"
}

POSTGRES_USER() {
  psql_db_user postgres
}

function handle_postgres_user() {
  if [[ $(POSTGRES_USER) != "1" ]]; then
    log_event "Creating postgres database user"
    PGPASSWORD=$DATABASE_PASSWORD \
      psql \
      --host="${DATABASE_HOST}" \
      --username="${DATABASE_USER}" \
      --dbname=${DATABASE_DB} \
      --command "CREATE ROLE postgres LOGIN PASSWORD '${DATABASE_PASSWORD}';"
  fi
}

function retry_endpoint() {
  curl \
    --fail \
    --silent \
    --connect-timeout 5 \
    --max-time 10 \
    --retry 5 \
    --retry-connrefused \
    --retry-delay 0 \
    --retry-max-time 60 \
    ${1} >/dev/null || exit 1
}
