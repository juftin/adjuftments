#!/usr/bin/env bash

set -e
COMMAND="${@}"

# CAPTURE THE ROOT OF THE SCRIPTS DIR TO ASSIST WITH PATHS
SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
source ${SCRIPTS_DIR}/bash_utils.sh

handle_postgres_user

exec ${COMMAND}
