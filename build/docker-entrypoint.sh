#!/usr/bin/env bash

set -e
COMMAND="${@}"

# CAPTURE THE ROOT OF THE DATASCIENCE DIR TO ASSIST WITH SCRIPTS / CLEANUP
BUILD_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
ADJUFTMENTS_DIR=$(dirname ${BUILD_DIR})
source ${ADJUFTMENTS_DIR}/scripts/bash_utils.sh

# WAIT FOR THE DATABASE TO BE READY
wait_for_database

log_event "Postgres is Ready, Beginning..."
exec ${COMMAND}
