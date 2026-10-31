#!/usr/bin/env python3
"""Validate versioned S3 gateway contracts and emit Terraform input JSON."""

import argparse
import json
import re
import sys
from pathlib import Path


ENVIRONMENTS = ("homolog", "production")
SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")
ARN_PATTERN = re.compile(r"^arn:[^:]+:lambda:[^:]+:[0-9]{12}:function:.+$")
URL_PATTERN = re.compile(r"^https?://[^/]+$")
LISTENER_ARN_PATTERN = re.compile(
    r"^arn:[^:]+:elasticloadbalancing:[^:]+:[0-9]{12}:listener/net/.+$"
)


def fail(message: str) -> "NoReturn":
    print(f"Contrato do API Gateway inválido: {message}", file=sys.stderr)
    raise SystemExit(1)


def load_contract(path: Path, kind: str, environment: str, account_id: str, region: str) -> dict:
    if not path.is_file():
        fail(f"arquivo obrigatório ausente: {path.name}")

    try:
        contract = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        fail(f"não foi possível ler {path.name}: {error.__class__.__name__}")

    if not isinstance(contract, dict):
        fail(f"{path.name} precisa conter um objeto JSON")
    expected = {
        "contract_version": 1,
        "account_id": account_id,
        "region": region,
        "environment": environment,
    }
    for key, value in expected.items():
        if contract.get(key) != value:
            fail(f"{path.name}: campo {key} ausente ou incompatível")
    if contract.get("cluster_name") != "oficina":
        fail(f"{path.name}: cluster_name incompatível")

    source_sha = contract.get("source_sha")
    if not isinstance(source_sha, str) or not SHA_PATTERN.fullmatch(source_sha):
        fail(f"{path.name}: source_sha deve ser um SHA Git completo de 40 caracteres")

    if kind == "upstream":
        if not isinstance(contract.get("upstream_url"), str) or not URL_PATTERN.fullmatch(
            contract["upstream_url"]
        ):
            fail(f"{path.name}: upstream_url precisa ser uma URL HTTP(S) sem caminho")
        listener_arn = contract.get("integration_listener_arn")
        if listener_arn is not None and (
            not isinstance(listener_arn, str) or not LISTENER_ARN_PATTERN.fullmatch(listener_arn)
        ):
            fail(f"{path.name}: integration_listener_arn precisa ser um listener NLB interno")
    elif kind == "grafana":
        if not isinstance(contract.get("listener_arn"), str) or not LISTENER_ARN_PATTERN.fullmatch(
            contract["listener_arn"]
        ):
            fail(f"{path.name}: listener_arn precisa ser um listener NLB interno")
    else:
        if not isinstance(contract.get("lambda_arn"), str) or not ARN_PATTERN.fullmatch(
            contract["lambda_arn"]
        ):
            fail(f"{path.name}: lambda_arn precisa ser um ARN Lambda válido")

    return contract


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contracts-dir", type=Path, required=True)
    parser.add_argument("--account-id", required=True)
    parser.add_argument("--region", required=True)
    parser.add_argument("--environment", choices=ENVIRONMENTS, required=True)
    parser.add_argument("--source-kind", choices=("app", "lambda", "infra", "observability"), required=True)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--state-resources-file", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    if not SHA_PATTERN.fullmatch(args.source_sha):
        fail("source_sha informado pelo workflow não é um SHA Git completo")

    state_resources = set(args.state_resources_file.read_text(encoding="utf-8").splitlines())
    routed_environments = set()
    for environment in ENVIRONMENTS:
        if any(
            address.startswith(prefix) and (f'["{environment}"]' in address or f'["{environment}|' in address)
            for address in state_resources
            for prefix in (
                "aws_apigatewayv2_integration.cluster",
                "aws_apigatewayv2_route.cluster",
                "aws_apigatewayv2_route.root",
                "aws_apigatewayv2_route.public",
                "aws_apigatewayv2_authorizer.jwt",
                "aws_lambda_permission.gateway_authorizer",
                "aws_apigatewayv2_integration.grafana",
                "aws_apigatewayv2_route.grafana",
            )
        ):
            routed_environments.add(environment)

    upstreams = {}
    upstream_listener_arns = {}
    authorizers = {}
    grafana_listeners = {}
    for environment in ENVIRONMENTS:
        base = args.contracts_dir / environment
        upstream_path = base / "upstream.json"
        authorizer_path = base / "authorizer.json"
        grafana_path = base / "grafana.json"
        upstream_exists = upstream_path.is_file()
        authorizer_exists = authorizer_path.is_file()
        grafana_exists = grafana_path.is_file()

        if not upstream_exists and not authorizer_exists:
            initial_infrastructure_apply = args.source_kind == "infra" and environment not in routed_environments
            if grafana_exists:
                fail(f"contrato grafana.json sem o par upstream.json/authorizer.json de {environment}")
            if environment in routed_environments or (environment == args.environment and not initial_infrastructure_apply):
                fail(f"contratos upstream.json e authorizer.json obrigatórios para {environment}")
            continue
        if upstream_exists != authorizer_exists:
            fail(f"par de contratos incompleto para {environment}; publique upstream e authorizer juntos")

        upstream = load_contract(upstream_path, "upstream", environment, args.account_id, args.region)
        authorizer = load_contract(authorizer_path, "authorizer", environment, args.account_id, args.region)
        upstreams[environment] = upstream["upstream_url"]
        authorizers[environment] = authorizer["lambda_arn"]
        if upstream.get("integration_listener_arn"):
            upstream_listener_arns[environment] = upstream["integration_listener_arn"]

        if grafana_exists:
            grafana = load_contract(grafana_path, "grafana", environment, args.account_id, args.region)
            grafana_listeners[environment] = grafana["listener_arn"]

        if environment == args.environment and args.source_kind != "infra":
            if args.source_kind in ("app", "observability") and environment not in upstream_listener_arns:
                fail(f"upstream.json de {environment} ainda não aponta para um listener NLB interno")
            current = {
                "app": upstream,
                "lambda": authorizer,
                "observability": grafana if grafana_exists else {},
            }.get(args.source_kind, upstream)
            if not current:
                fail(f"contrato grafana.json ausente para {environment}")
            if current["source_sha"] != args.source_sha:
                fail(f"source_sha de {args.source_kind} diverge do contrato de {environment}")

    args.output.write_text(
        json.dumps(
            {
                "app_upstream_urls": upstreams,
                "app_upstream_listener_arns": upstream_listener_arns,
                "authorizer_arns": authorizers,
                "grafana_listener_arns": grafana_listeners,
                "gateway_contract_account_id": args.account_id,
                "gateway_contract_region": args.region,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
