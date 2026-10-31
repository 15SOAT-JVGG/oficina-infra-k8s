#!/usr/bin/env bash
# Remove only the failed, unused EBS CSI add-on; retain all other infrastructure.
set -euo pipefail
: "${AWS_REGION:?}" "${TF_STATE_BUCKET:?}" "${GITHUB_SHA:?}"
umask 077
workdir=$(mktemp -d)
trap 'rm -rf "$workdir"' EXIT
account_id=$(aws sts get-caller-identity --query Account --output text)
[[ "$account_id" == 630266487412 ]] || { echo 'Unexpected AWS account'; exit 1; }
aws eks update-kubeconfig --name oficina --region "$AWS_REGION" >/dev/null
kubectl get pvc --namespace observability -o json > "$workdir/pvc.json"
jq '[.items[] | {name:.metadata.name,phase:.status.phase,volumeAssigned:((.spec.volumeName // "") != "")}]' "$workdir/pvc.json"
jq -e 'all(.items[]; (.spec.volumeName // "") == "" and .status.phase == "Pending")' "$workdir/pvc.json" >/dev/null || {
  echo 'Recovery refused: an observability PVC has storage or is not Pending.'; exit 1;
}
terraform init -input=false -no-color \
  -backend-config="bucket=$TF_STATE_BUCKET" \
  -backend-config='key=oficina-infra-k8s/terraform.tfstate' \
  -backend-config="region=$AWS_REGION" -backend-config='use_lockfile=true' >/dev/null
terraform state list > "$workdir/resources"
for environment in homolog production; do
  mkdir -p "$workdir/contracts/$environment"
  for kind in upstream authorizer grafana; do
    key="oficina/config/v1/$environment/$kind.json"
    if aws s3api head-object --bucket "$TF_STATE_BUCKET" --key "$key" >/dev/null 2>"$workdir/head.err"; then
      aws s3 cp "s3://$TF_STATE_BUCKET/$key" "$workdir/contracts/$environment/$kind.json" --only-show-errors
    elif ! grep -Eq '404|Not Found|NoSuchKey' "$workdir/head.err"; then
      cat "$workdir/head.err" >&2; exit 1
    fi
  done
done
python3 scripts/contracts-to-tfvars.py --contracts-dir "$workdir/contracts" \
  --account-id "$account_id" --region "$AWS_REGION" --environment homolog \
  --source-kind infra --source-sha "$GITHUB_SHA" \
  --state-resources-file "$workdir/resources" --output "$workdir/inputs.json"
if ! terraform plan -input=false -lock-timeout=5m -no-color -var-file="$workdir/inputs.json" \
    -out="$workdir/plan" > "$workdir/plan.log" 2>&1; then
  cat "$workdir/plan.log"; exit 1
fi
terraform show -json "$workdir/plan" > "$workdir/plan.json"
python3 - "$workdir/plan.json" <<'PY'
import json, sys
plan = json.load(open(sys.argv[1]))
for item in plan.get('resource_changes', []):
    actions = item['change']['actions']
    if item.get('mode') == 'data' or actions == ['no-op']:
        continue
    print(item['address'], actions)
    if item['address'] != 'aws_eks_addon.ebs_csi_driver' or actions != ['delete']:
        sys.exit('Recovery refused: plan changes resources beyond deletion of the unused EBS CSI add-on.')
print('Recovery plan passed: no application, Gateway, database, IAM or node changes.')
PY
if [[ "${EXECUTE_RECOVERY:-false}" == true ]]; then
  terraform apply -input=false -lock-timeout=5m -no-color "$workdir/plan"
else
  echo 'Plan only. No state or AWS resource changed.'
fi
