#!/usr/bin/env bash
set -euo pipefail
RSYNC_DIR="$(cygpath -u "$LOCALAPPDATA")/CodexDevOps/rsync/bin"
export PATH="$RSYNC_DIR:$PATH"
export DEPLOY_SSH_BIN="$(cygpath -m "$RSYNC_DIR/ssh.exe") -F $(cygpath -m "$HOME/.ssh/config") -o UserKnownHostsFile=$(cygpath -m "$HOME/.ssh/known_hosts") -i $(cygpath -m "$HOME/.ssh/devops_vm")"
export DEPLOY_CURL_BIN=C:/Windows/System32/curl.exe
export DEPLOY_CA_CERT="$(cygpath -m "$HOME/devops.crt")"
exec bash "$@"
