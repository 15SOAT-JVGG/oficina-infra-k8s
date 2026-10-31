#!/usr/bin/env python3
"""Create public API Probe resources without committing environment-specific URLs."""

import json
import os
import re
import subprocess
import sys
from urllib.parse import urlsplit


def make_probe(environment: str, url: str) -> dict:
    parsed = urlsplit(url)
    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError(f"{environment} URL must be an HTTPS URL")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError(f"{environment} URL must not contain credentials, query, or fragment")
    if parsed.path not in ("", "/"):
        raise ValueError(f"{environment} URL must be the API Gateway base URL")
    if not re.fullmatch(r"[A-Za-z0-9.-]+", parsed.hostname):
        raise ValueError(f"{environment} hostname contains unsupported characters")

    return {
        "apiVersion": "monitoring.coreos.com/v1",
        "kind": "Probe",
        "metadata": {
            "name": f"oficina-public-api-{environment}",
            "namespace": "observability",
            "labels": {"release": "oficina-monitoring"},
        },
        "spec": {
            "jobName": f"oficina-public-api-{environment}",
            "interval": "30s",
            "module": "http_2xx",
            "prober": {
                "url": "oficina-blackbox-prometheus-blackbox-exporter.observability.svc.cluster.local:9115",
                "scheme": "http",
                "path": "/probe",
            },
            "targets": {
                "staticConfig": {
                    # Health/OpenAPI are on the private management interface. The
                    # public Swagger UI route is explicitly unauthenticated in API Gateway.
                    "static": [f"{url.rstrip('/')}/q/swagger-ui/"],
                    "labels": {"environment": environment},
                }
            },
        },
    }


def main() -> int:
    probes = []
    for environment in ("homolog", "production"):
        value = os.getenv(f"{environment.upper()}_API_BASE_URL", "")
        if value:
            probes.append(make_probe(environment, value))
    if not probes:
        print("Set HOMOLOG_API_BASE_URL and/or PRODUCTION_API_BASE_URL", file=sys.stderr)
        return 2

    manifest = "\n---\n".join(json.dumps(probe) for probe in probes)
    subprocess.run(["kubectl", "apply", "-f", "-"], input=manifest, text=True, check=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, subprocess.CalledProcessError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1) from error
