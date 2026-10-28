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
    parser.add_argument("--source-kind", choices=("app", "lambda", "infra"), required=True)
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
            )
        ):
            routed_environments.add(environment)

    upstreams = {}
    authorizers = {}
    for environment in ENVIRONMENTS:
        base = args.contracts_dir / environment
        upstream_path = base / "upstream.json"
        authorizer_path = base / "authorizer.json"
        upstream_exists = upstream_path.is_file()
        authorizer_exists = authorizer_path.is_file()

        if not upstream_exists and not authorizer_exists:
            initial_infrastructure_apply = args.source_kind == "infra" and environment not in routed_environments
            if environment in routed_environments or (environment == args.environment and not initial_infrastructure_apply):
                fail(f"contratos upstream.json e authorizer.json obrigatórios para {environment}")
            continue
        if upstream_exists != authorizer_exists:
            fail(f"par de contratos incompleto para {environment}; publique upstream e authorizer juntos")

        upstream = load_contract(upstream_path, "upstream", environment, args.account_id, args.region)
        authorizer = load_contract(authorizer_path, "authorizer", environment, args.account_id, args.region)
        upstreams[environment] = upstream["upstream_url"]
        authorizers[environment] = authorizer["lambda_arn"]

        if environment == args.environment and args.source_kind != "infra":
            current = upstream if args.source_kind == "app" else authorizer
            if current["source_sha"] != args.source_sha:
                fail(f"source_sha de {args.source_kind} diverge do contrato de {environment}")

    args.output.write_text(
        json.dumps(
            {
                "app_upstream_urls": upstreams,
                "authorizer_arns": authorizers,
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
