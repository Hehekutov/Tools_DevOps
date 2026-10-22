#!/usr/bin/env bash
set -euo pipefail
RSYNC_DIR="$(cygpath -u "$LOCALAPPDATA")/CodexDevOps/rsync/bin"
export PATH="$RSYNC_DIR:$PATH"
export DEPLOY_SSH_BIN=C:/Windows/System32/OpenSSH/ssh.exe
export DEPLOY_CURL_BIN=C:/Windows/System32/curl.exe
export DEPLOY_CA_CERT="$(cygpath -m "$HOME/devops.crt")"
exec bash "$@"
