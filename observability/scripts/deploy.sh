#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
observability_dir="$(cd -- "$script_dir/.." && pwd)"
source "$observability_dir/helm/versions.env"

: "${AWS_REGION:?AWS_REGION is required}"
: "${GRAFANA_ADMIN_PASSWORD:?Set the protected GRAFANA_ADMIN_PASSWORD GitHub Environment secret}"
cluster_name="${EKS_CLUSTER_NAME:-oficina}"
[[ "$cluster_name" =~ ^[a-zA-Z0-9_-]+$ ]] || { echo "Invalid cluster name" >&2; exit 2; }

# The script intentionally installs the cluster-wide stack once, independent of app environment.
aws eks update-kubeconfig --name "$cluster_name" --region "$AWS_REGION"
kubectl create namespace observability --dry-run=client -o yaml | kubectl apply -f -
kubectl create secret generic oficina-grafana-admin \
  --namespace observability \
  --from-literal=admin-user=admin \
  --from-literal=admin-password="$GRAFANA_ADMIN_PASSWORD" \
  --dry-run=client -o yaml | kubectl apply -f -

helm repo add prometheus-community https://prometheus-community.github.io/helm-charts --force-update
helm repo add grafana-community https://grafana-community.github.io/helm-charts --force-update
helm repo add grafana https://grafana.github.io/helm-charts --force-update
helm repo update

# A Helm timeout otherwise hides whether the operator, Grafana, Prometheus, or
# storage is preventing the release from becoming ready. Keep failure diagnostics
# read-only and limited to workload status and events; never print Secret data.
diagnose_observability_failure() {
  local exit_code=$?
  trap - ERR
  echo "Observability deployment failed; collecting workload diagnostics." >&2
  helm list --namespace observability --output table || true
  kubectl get pods,deployments,statefulsets,daemonsets,services,persistentvolumeclaims \
    --namespace observability --output wide || true
  kubectl get events --namespace observability \
    --sort-by=.metadata.creationTimestamp | tail -n 40 || true
  exit "$exit_code"
}
trap diagnose_observability_failure ERR

kubectl apply --filename "$observability_dir/storage/gp3.yaml"

# Install Prometheus Operator first because later app/rule manifests use its CRDs.
helm upgrade --install oficina-monitoring prometheus-community/kube-prometheus-stack \
  --version "$KUBE_PROMETHEUS_STACK_VERSION" \
  --namespace observability \
  --values "$observability_dir/helm/kube-prometheus-stack-values.yaml" \
  --wait --timeout 15m --history-max 10

kubectl wait --for=condition=Established --timeout=120s \
  crd/servicemonitors.monitoring.coreos.com \
  crd/prometheusrules.monitoring.coreos.com

helm upgrade --install loki grafana-community/loki \
  --version "$LOKI_VERSION" \
  --namespace observability \
  --values "$observability_dir/helm/loki-values.yaml" \
  --wait --timeout 15m --history-max 10

helm upgrade --install tempo grafana-community/tempo \
  --version "$TEMPO_VERSION" \
  --namespace observability \
  --values "$observability_dir/helm/tempo-values.yaml" \
  --wait --timeout 15m --history-max 10

helm upgrade --install alloy grafana/alloy \
  --version "$ALLOY_VERSION" \
  --namespace observability \
  --values "$observability_dir/helm/alloy-values.yaml" \
  --wait --timeout 10m --history-max 10

helm upgrade --install oficina-blackbox prometheus-community/prometheus-blackbox-exporter \
  --version "$BLACKBOX_EXPORTER_VERSION" \
  --namespace observability \
  --values "$observability_dir/helm/blackbox-values.yaml" \
  --wait --timeout 10m --history-max 10

kubectl apply -f "$observability_dir/rules/cluster-alerts.yaml"
kubectl create configmap oficina-cluster-overview-dashboard \
  --namespace observability \
  --from-file=cluster-overview.json="$observability_dir/dashboards/cluster-overview.json" \
  --dry-run=client -o yaml \
  | kubectl label --local -f - grafana_dashboard=1 -o yaml \
  | kubectl apply -f -
kubectl create configmap oficina-api-overview-dashboard \
  --namespace observability \
  --from-file=api-overview.json="$observability_dir/dashboards/api-overview.json" \
  --dry-run=client -o yaml \
  | kubectl label --local -f - grafana_dashboard=1 -o yaml \
  | kubectl apply -f -

echo "Observability releases reconciled. Verify targets, PVCs, and Grafana access before relying on alerts."
