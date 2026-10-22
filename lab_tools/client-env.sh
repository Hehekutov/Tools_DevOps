#!/usr/bin/env bash
set -euo pipefail
RSYNC_DIR="$(cygpath -u "$LOCALAPPDATA")/CodexDevOps/rsync/bin"
export PATH="$RSYNC_DIR:$PATH"
export DEPLOY_SSH_BIN=/c/Windows/System32/OpenSSH/ssh.exe
export DEPLOY_CURL_BIN=/c/Windows/System32/curl.exe
export DEPLOY_CA_CERT="$(cygpath -m "$HOME/devops.crt")"
export DEPLOY_RESOLVE="${DEPLOY_RESOLVE:-devops.local:443:127.0.0.1}"
exec bash "$@"
