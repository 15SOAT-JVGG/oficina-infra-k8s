"""Exercise retry and fail-closed behavior without AWS or Terraform."""
import json
import os
import pathlib
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SHA = "a" * 40

AWS = '''#!/usr/bin/env python3
import os, pathlib, shutil, sys
a=sys.argv[1:]; root=pathlib.Path(os.environ["FAKE_ROOT"])
if a[:2]==["sts","get-caller-identity"]: print("123456789012")
elif a[:2]==["s3api","head-object"]:
    key=a[a.index("--key")+1]; p=root/"objects"/key
    if not p.exists(): print("404 Not Found",file=sys.stderr); sys.exit(1)
elif a[:2]==["s3","cp"]:
    key=a[2].split("/",3)[3]; shutil.copyfile(root/"objects"/key,a[3])
else: sys.exit(8)
'''
TF = '''#!/usr/bin/env python3
import json, os, pathlib, sys
root=pathlib.Path(os.environ["FAKE_ROOT"]); a=sys.argv[1:]
def inc(name):
 p=root/name; n=int(p.read_text())+1 if p.exists() else 1; p.write_text(str(n)); return n
if a[:2]==["state","list"]: print('aws_apigatewayv2_route.root["homolog"]')
elif a[0]=="plan":
 n=inc("plans")
 if os.environ.get("LOCK")=="1" and n==1: print("Error acquiring the state lock"); sys.exit(1)
 pathlib.Path(next(x[5:] for x in a if x.startswith("-out="))).write_text("plan")
 if os.environ.get("CHANGE_CONTRACT")=="1" and n==1:
  p=root/"objects/oficina/config/v1/homolog/upstream.json"; j=json.loads(p.read_text()); j["upstream_url"]="http://new.example"; p.write_text(json.dumps(j))
elif a[0]=="show":
 address='aws_eks_node_group.main' if os.environ.get("FORBID")=="1" else 'aws_apigatewayv2_route.root["homolog"]'
 print(json.dumps({"resource_changes":[{"address":address,"change":{"actions":["update"]}}]}))
elif a[0]=="apply":
 n=inc("applies")
 if os.environ.get("CHANGE_DURING_APPLY")=="1" and n==1:
  p=root/"objects/oficina/config/v1/homolog/upstream.json"; j=json.loads(p.read_text()); j["upstream_url"]="http://new.example"; p.write_text(json.dumps(j))
 if os.environ.get("STALE")=="1" and n==1: print("Error: Saved plan is stale"); sys.exit(1)
 if os.environ.get("OTHER_ERROR")=="1": print("AccessDenied"); sys.exit(1)
else: sys.exit(9)
'''


class ConvergeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)
        bindir = self.root / "bin"
        bindir.mkdir()
        for name, content in (("aws", AWS), ("terraform", TF)):
            path = bindir / name
            path.write_text(content)
            path.chmod(0o755)
        d = self.root / "objects/oficina/config/v1/homolog"
        d.mkdir(parents=True)
        common = {"contract_version": 1, "account_id": "123456789012", "region": "us-east-1", "environment": "homolog", "cluster_name": "oficina", "source_sha": SHA}
        (d / "upstream.json").write_text(json.dumps({
            **common,
            "upstream_url": "http://old.example",
            "integration_listener_arn": "arn:aws:elasticloadbalancing:us-east-1:123456789012:listener/net/app/abc/def",
        }))
        (d / "authorizer.json").write_text(json.dumps({**common, "lambda_arn": "arn:aws:lambda:us-east-1:123456789012:function:auth:1"}))
        (d / "grafana.json").write_text(json.dumps({
            **common,
            "listener_arn": "arn:aws:elasticloadbalancing:us-east-1:123456789012:listener/net/grafana/abc/def",
        }))
        self.env = {**os.environ, "PATH": f"{bindir}:{os.environ['PATH']}", "FAKE_ROOT": str(self.root), "TF_STATE_BUCKET": "bucket", "AWS_REGION": "us-east-1", "CONTRACT_ENVIRONMENT": "homolog", "CONTRACT_SOURCE_KIND": "infra", "CONTRACT_SOURCE_SHA": SHA}

    def run_script(self, mode="infra", source_kind=None, **flags):
        env = {**self.env, **flags}
        if mode == "reconcile": env["CONTRACT_SOURCE_KIND"] = source_kind or "app"
        return subprocess.run(["bash", "scripts/terraform-converge.sh", mode], cwd=ROOT, env=env, capture_output=True, text=True)

    def count(self, name):
        p = self.root / name
        return int(p.read_text()) if p.exists() else 0

    def test_stale_plan_replans_before_retry(self):
        result = self.run_script(STALE="1")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.count("plans"), self.count("applies")), (2, 2))

    def test_contract_changed_after_plan_forces_new_plan(self):
        result = self.run_script(CHANGE_CONTRACT="1")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.count("plans"), self.count("applies")), (2, 1))

    def test_lock_contention_retries_plan(self):
        result = self.run_script(LOCK="1")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.count("plans"), self.count("applies")), (2, 1))

    def test_unrelated_resource_is_never_applied(self):
        result = self.run_script("reconcile", FORBID="1")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.count("applies"), 0)

    def test_observability_contract_reconciles_grafana_route(self):
        result = self.run_script("reconcile", source_kind="observability")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.count("plans"), self.count("applies")), (1, 1))

    def test_contract_changed_during_apply_is_reconciled_again(self):
        result = self.run_script(CHANGE_DURING_APPLY="1")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.count("plans"), self.count("applies")), (2, 2))

    def test_access_denied_is_not_retried(self):
        result = self.run_script(OTHER_ERROR="1")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.count("applies"), 1)


if __name__ == "__main__":
    unittest.main()
