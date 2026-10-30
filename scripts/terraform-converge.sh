#!/usr/bin/env bash
# Recalculate the shared-state plan after contention or a stale-plan error.
set -euo pipefail
: "${TF_STATE_BUCKET:?}" "${AWS_REGION:?}" "${CONTRACT_ENVIRONMENT:?}" "${CONTRACT_SOURCE_KIND:?}" "${CONTRACT_SOURCE_SHA:?}"
mode="${1:?expected infra or reconcile}"
[[ "$mode" == infra || "$mode" == reconcile ]] || exit 2
[[ "$CONTRACT_ENVIRONMENT" == homolog || "$CONTRACT_ENVIRONMENT" == production ]] || exit 2
[[ "$CONTRACT_SOURCE_SHA" =~ ^[0-9a-f]{40}$ ]] || exit 2
[[ "$mode" != infra || "$CONTRACT_SOURCE_KIND" == infra ]] || exit 2
[[ "$mode" != reconcile || "$CONTRACT_SOURCE_KIND" == app || "$CONTRACT_SOURCE_KIND" == lambda || "$CONTRACT_SOURCE_KIND" == observability ]] || exit 2
umask 077
workdir=$(mktemp -d)
trap 'rm -rf "$workdir"' EXIT
account_id=$(aws sts get-caller-identity --query Account --output text)
read_contracts() {
  local target="$1" env kind key
  mkdir -p "$target"
  for env in homolog production; do
    mkdir -p "$target/$env"
    for kind in upstream authorizer grafana; do
      key="oficina/config/v1/$env/$kind.json"
      if aws s3api head-object --bucket "$TF_STATE_BUCKET" --key "$key" > /dev/null 2>"$workdir/head.err"; then
        aws s3 cp "s3://$TF_STATE_BUCKET/$key" "$target/$env/$kind.json" --only-show-errors
      elif grep -Eq '404|Not Found|NoSuchKey' "$workdir/head.err"; then
        :
      else
        cat "$workdir/head.err" >&2
        return 1
      fi
    done
  done
}
retryable() {
  grep -Eqi 'saved plan is stale|saved plan does not match|error acquiring the state lock|failed to acquire state lock' "$1"
}
max_attempts=4
for ((attempt=1; attempt<=max_attempts; attempt++)); do
  echo "Terraform: tentativa $attempt/$max_attempts ($mode, $CONTRACT_ENVIRONMENT)."
  rm -rf "$workdir/contracts" "$workdir/current"
  if ! terraform state list > "$workdir/resources" 2> "$workdir/state.err"; then
    if grep -q 'No state file was found' "$workdir/state.err"; then
      : > "$workdir/resources"
    else
      cat "$workdir/state.err" >&2; exit 1
    fi
  fi
  read_contracts "$workdir/contracts"
  python3 scripts/contracts-to-tfvars.py --contracts-dir "$workdir/contracts" \
    --account-id "$account_id" --region "$AWS_REGION" --environment "$CONTRACT_ENVIRONMENT" \
    --source-kind "$CONTRACT_SOURCE_KIND" --source-sha "$CONTRACT_SOURCE_SHA" \
    --state-resources-file "$workdir/resources" --output "$workdir/gateway.tfvars.json"
  if ! terraform plan -input=false -lock-timeout=15m -no-color \
      -var-file="$workdir/gateway.tfvars.json" -out="$workdir/plan" 2>&1 | tee "$workdir/plan.log"; then
    if retryable "$workdir/plan.log" && ((attempt < max_attempts)); then continue; fi
    exit 1
  fi
  if [[ "$mode" == reconcile ]]; then
    terraform show -json "$workdir/plan" > "$workdir/plan.json"
    python3 scripts/reconcile-plan-guard.py "$workdir/plan.json" "$CONTRACT_ENVIRONMENT"
  fi
  read_contracts "$workdir/current"
  if ! diff -qr "$workdir/contracts" "$workdir/current" > /dev/null; then
    echo 'Contratos mudaram durante o plano; refazendo a leitura.' >&2
    ((attempt < max_attempts)) || exit 1
    continue
  fi
  if terraform apply -input=false -lock-timeout=15m -no-color "$workdir/plan" 2>&1 | tee "$workdir/apply.log"; then
    rm -rf "$workdir/current"
    read_contracts "$workdir/current"
    if diff -qr "$workdir/contracts" "$workdir/current" > /dev/null; then
      exit 0
    fi
    echo 'Contratos mudaram durante o apply; verificando novamente.' >&2
    ((attempt < max_attempts)) || exit 1
    continue
  fi
  if retryable "$workdir/apply.log" && ((attempt < max_attempts)); then
    echo 'Estado mudou ou está ocupado; recalculando o plano e os contratos.' >&2
    continue
  fi
  exit 1
done
exit 1
