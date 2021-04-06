#!/usr/bin/env bash

set -e
COMMAND="${@}"

# CAPTURE THE ROOT OF THE DATASCIENCE DIR TO ASSIST WITH SCRIPTS / CLEANUP
SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
source ${SCRIPTS_DIR}/bash_utils.sh

log_event "Checking API status"

retry_endpoint "http://${ADJUFTMENTS_API_HOST}:5000/api/1.0/admin/health"

log_event "API is connected, proceeding"

exec ${COMMAND}
