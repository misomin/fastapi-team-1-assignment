#!/usr/bin/env bash
# Called over SSH by CD. Does not fetch a moving branch or create/drop a DB.
set -euo pipefail

if [[ $# != 4 ]]; then
  echo 'Usage: deploy.sh ARCHIVE COMMIT_SHA SOURCE_HASH CI_RUN_NUMBER' >&2
  exit 2
fi
archive=$(realpath -e "$1")
sha=$2
source_hash=$3
run_number=$4
[[ "$sha" =~ ^[0-9a-f]{40}$ && "$source_hash" =~ ^[0-9a-f]{64}$ ]]
[[ "$run_number" =~ ^[1-9][0-9]*$ && ${#run_number} -le 15 ]]

root=${WAPANG_ROOT:-/home/ubuntu/wapang}
uv=${UV_BIN:-/home/ubuntu/.local/bin/uv}
env_file="$root/shared/production.env"
test -r "$env_file"
test -x "$uv"
sudo -n true
mkdir -p "$root/releases"
exec 9> "$root/deploy.lock"
flock -w 600 9

# CI run_number belongs to the CI workflow, not to the later CD completion.
# Record attempts as well as successes: a failed newer migration may have
# partially changed MySQL, so an older release must not start afterwards.
if [[ -f "$root/last-attempt" ]]; then
  read -r previous_run previous_sha < "$root/last-attempt"
  [[ "$previous_run" =~ ^[1-9][0-9]*$ && ${#previous_run} -le 15 ]]
  if (( run_number < previous_run )); then
    echo "Skipping older CI run $run_number (latest attempt: $previous_run)."
    exit 3
  fi
  if (( run_number == previous_run )) && [[ "$sha" != "$previous_sha" ]]; then
    echo 'CI run number was reused for a different commit.' >&2
    exit 1
  fi
fi
printf '%s %s\n' "$run_number" "$sha" > "$root/last-attempt.next"
mv -f "$root/last-attempt.next" "$root/last-attempt"

# Each attempt gets its own virtualenv and immutable application directory.
release=$(mktemp -d "$root/releases/$sha.XXXXXX")
tar -xzf "$archive" -C "$release"
cd "$release"
test -f deploy/wapang.service
export ENV=prod
# uv gives inherited variables precedence over --env-file. Both migration and
# the service must use the shared production file, not a login shell's DB.
unset DB_DIALECT DB_DRIVER DB_HOST DB_PORT DB_USER DB_PASSWORD DB_DATABASE
unset ACCESS_TOKEN_SECRET REFRESH_TOKEN_SECRET SHORT_SESSION_LIFESPAN LONG_SESSION_LIFESPAN
unset UV_ENV_FILE UV_NO_ENV_FILE
"$uv" sync --frozen --python 3.12
run=("$uv" run --frozen --no-sync --env-file "$env_file")
"${run[@]}" python -m deploy.check_database
sudo -n install -m 644 deploy/wapang.service /etc/systemd/system/wapang.service
sudo -n systemctl daemon-reload
sudo -n systemctl stop wapang.service

# This assignment accepts downtime. Stop all old application processes before
# changing the schema, so revisions need not support the previous application.
legacy=$(sudo -n docker ps --filter 'name=^/fastapi-assignment-3$' --format '{{.Names}}')
if [[ "$legacy" == fastapi-assignment-3 ]]; then
  sudo -n docker update --restart=no fastapi-assignment-3
  sudo -n docker stop fastapi-assignment-3
fi

"${run[@]}" alembic upgrade head
sudo -n systemctl enable wapang.service
ln -s "$release" "$release.link"
mv -Tf "$release.link" "$root/current"
sudo -n systemctl restart wapang.service
"${run[@]}" python -m deploy.verify_health http://127.0.0.1/health "$source_hash"
"${run[@]}" python -m deploy.check_database
sudo -n systemctl is-active --quiet wapang.service
printf '%s %s %s\n' "$run_number" "$sha" "$source_hash" > "$root/last-deployed.next"
mv -f "$root/last-deployed.next" "$root/last-deployed"
echo "Deployed commit $sha (CI run $run_number)."
