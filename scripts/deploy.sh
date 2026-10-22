#!/usr/bin/env bash
set -euo pipefail
ROOT="$(git -C "$(dirname -- "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)"
ROOT="$(cd -- "$ROOT" && pwd -P)"
REMOTE="${DEPLOY_REMOTE:-devops}"
REMOTE_DIR="${DEPLOY_DIR:-/var/www/devops-site/}"
SITE_URL="${DEPLOY_URL:-https://devops.local}"
CA_CERT="${DEPLOY_CA_CERT:-$HOME/devops.crt}"
SSH_BIN="${DEPLOY_SSH_BIN:-ssh}"
CURL_BIN="${DEPLOY_CURL_BIN:-curl}"
resolve_args=()
[[ -z "${DEPLOY_RESOLVE:-}" ]] || resolve_args=(--resolve "$DEPLOY_RESOLVE")
dry=()
case "${1:-}" in
  '') [[ $# -eq 0 ]] || { echo 'Unexpected arguments' >&2; exit 1; };;
  --dry-run) [[ $# -eq 1 ]] || exit 1; dry=(--dry-run);;
  *) echo 'Usage: deploy.sh [--dry-run]' >&2; exit 1;;
esac
[[ -f "$ROOT/site/index.html" ]] || { echo 'site/index.html is missing' >&2; exit 1; }
[[ -z "$(git -C "$ROOT" status --porcelain)" ]] || { echo 'Uncommitted changes in repository' >&2; exit 1; }
rsync -avz --delete --chmod=D755,F644 "${dry[@]}" \
  -e "$SSH_BIN -o BatchMode=yes -o ConnectTimeout=5" "$ROOT/site/" "$REMOTE:$REMOTE_DIR"
[[ ${#dry[@]} -eq 0 ]] || { echo 'Dry run complete'; exit 0; }
"$CURL_BIN" "${resolve_args[@]}" --noproxy '*' --fail --silent --show-error --connect-timeout 5 --max-time 15 \
  --cacert "$CA_CERT" "$SITE_URL" >/dev/null || { echo 'HTTPS verification failed' >&2; exit 1; }
printf 'Deployed commit %s\n' "$(git -C "$ROOT" rev-parse --short HEAD)"
