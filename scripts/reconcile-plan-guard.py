#!/usr/bin/env python3
"""Reject changes outside the selected environment's gateway resources."""
import json
import sys


def validate(plan, environment):
    allowed = {
        f'aws_apigatewayv2_integration.cluster["{environment}"]',
        f'aws_apigatewayv2_integration.grafana["{environment}"]',
        f'aws_apigatewayv2_route.cluster["{environment}"]',
        f'aws_apigatewayv2_route.root["{environment}"]',
        f'aws_apigatewayv2_authorizer.jwt["{environment}"]',
        f'aws_lambda_permission.gateway_authorizer["{environment}"]',
    }
    invalid = []
    for change in plan.get("resource_changes", []):
        address = change["address"]
        actions = change["change"]["actions"]
        if actions == ["no-op"]:
            continue
        if address.startswith(f'aws_apigatewayv2_route.public["{environment}|'):
            continue
        if address.startswith(f'aws_apigatewayv2_route.grafana["{environment}|'):
            continue
        if address not in allowed:
            invalid.append(f"{address}: {','.join(actions)}")
    if invalid:
        raise ValueError("Plano recusado: alteração fora do ambiente solicitado:\n" + "\n".join(invalid))


def main():
    if len(sys.argv) != 3 or sys.argv[2] not in ("homolog", "production"):
        sys.exit("Uso: reconcile-plan-guard.py <plano.json> <homolog|production>")
    with open(sys.argv[1], encoding="utf-8") as plan:
        try:
            validate(json.load(plan), sys.argv[2])
        except ValueError as error:
            sys.exit(str(error))


if __name__ == "__main__":
    main()
