"""Explicit FIAP lab teardown; state values and plans stay private on the runner."""
import json
import os
import pathlib
import subprocess
import tempfile
import time

ACCOUNT = '630266487412'
BUCKET = 'fiap16soat-oficina-tfstate-' + ACCOUNT
STATES = {
    'oficina-lambda-auth/homolog/terraform.tfstate': {
        'aws_apigatewayv2_integration.auth', 'aws_apigatewayv2_route.auth',
        'aws_cloudwatch_log_group.authorizer', 'aws_cloudwatch_log_group.function',
        'aws_lambda_function.auth', 'aws_lambda_function.authorizer',
        'aws_lambda_permission.api_gateway', 'aws_lambda_permission.api_gateway_authorizer',
        'aws_s3_object.authorizer_contract', 'aws_security_group.function',
        'aws_vpc_security_group_egress_rule.postgres'},
    'oficina-infra-db/homolog/terraform.tfstate': {
        'aws_db_instance.database', 'aws_db_subnet_group.database',
        'aws_security_group.database', 'aws_vpc_security_group_ingress_rule.postgres_from_vpc'},
    'oficina-infra-k8s/terraform.tfstate': {
        'aws_apigatewayv2_api.main', 'aws_apigatewayv2_authorizer.jwt',
        'aws_apigatewayv2_integration.cluster', 'aws_apigatewayv2_integration.grafana',
        'aws_apigatewayv2_route.cluster', 'aws_apigatewayv2_route.grafana',
        'aws_apigatewayv2_route.public', 'aws_apigatewayv2_route.root',
        'aws_apigatewayv2_stage.default', 'aws_apigatewayv2_vpc_link.cluster',
        'aws_cloudwatch_log_group.api_gateway_access', 'aws_ecr_lifecycle_policy.app',
        'aws_ecr_repository.app', 'aws_eks_addon.metrics_server', 'aws_eks_cluster.main',
        'aws_eks_node_group.main', 'aws_lambda_permission.gateway_authorizer',
        'aws_launch_template.nodes', 'aws_route_table.gateway_private',
        'aws_route_table_association.gateway_private', 'aws_security_group.api_gateway_vpc_link',
        'aws_subnet.gateway_private'}
}


def run(args, cwd=None):
    result = subprocess.run(args, cwd=cwd, text=True, capture_output=True)
    if result.returncode:
        # Do not dump Terraform diagnostics: they may contain state values.
        raise RuntimeError(f'Command failed: {args[0]} {args[1]}; exit={result.returncode}')
    return result.stdout


def aws(*args):
    return json.loads(run(['aws', *args, '--output', 'json']))


def inventory():
    states = {}
    for key, allowed in STATES.items():
        state = json.loads(run(['aws', 's3', 'cp', f's3://{BUCKET}/{key}', '-', '--only-show-errors']))
        managed = [r for r in state.get('resources', []) if r.get('mode') == 'managed']
        assert all(not r.get('module') for r in managed), 'Unexpected module scope'
        assert all(r['type']+'.'+r['name'] in allowed for r in managed), 'Unexpected state address'
        assert all(r['provider'] == 'provider["registry.terraform.io/hashicorp/aws"]' for r in managed)
        if key.startswith('oficina-infra-db'):
            for resource in managed:
                if resource['type'] == 'aws_db_instance':
                    for instance in resource['instances']:
                        attrs = instance['attributes']
                        assert attrs['identifier'] == 'oficina-homolog'
                        assert attrs['skip_final_snapshot'] and not attrs['deletion_protection']
        states[key] = state
        print(json.dumps({'state': key, 'managed_instances': sum(len(r['instances']) for r in managed)}), flush=True)
    # Production must not be silently omitted.
    for key in ['oficina-infra-db/production/terraform.tfstate', 'oficina-lambda-auth/production/terraform.tfstate']:
        result = subprocess.run(['aws', 's3api', 'head-object', '--bucket', BUCKET, '--key', key], capture_output=True, text=True)
        assert result.returncode != 0, 'Production state found: inventory must be extended before teardown'
        assert '(404)' in result.stderr or 'Not Found' in result.stderr, 'Cannot establish absence of production state'
    return states


def prepare(root, key):
    folder = root / key.split('/')[0]
    folder.mkdir()
    # A dedicated destruction configuration deliberately removes runtime prevent_destroy guards.
    # The canonical provisioning configuration is preserved. Only inventoried state addresses are allowed.
    (folder / 'main.tf').write_text('''terraform {
  required_version = "= 1.10.5"
  backend "s3" {}
  required_providers {
    aws = { source = "hashicorp/aws", version = "= 5.100.0" }
  }
}
provider "aws" {
  region = "us-east-1"
  allowed_account_ids = ["630266487412"]
}
''')
    run(['terraform', 'init', '-input=false', '-no-color', '-backend-config=bucket='+BUCKET,
         '-backend-config=key='+key, '-backend-config=region=us-east-1',
         '-backend-config=encrypt=true', '-backend-config=use_lockfile=true'], folder)
    return folder


def plan(folder):
    run(['terraform', 'plan', '-destroy', '-input=false', '-no-color', '-lock-timeout=5m', '-out=destroy.tfplan'], folder)
    data = json.loads(run(['terraform', 'show', '-json', 'destroy.tfplan'], folder))
    changes = data.get('resource_changes', [])
    assert all(r['change']['actions'] in [['delete'], ['no-op'], ['read']] for r in changes)
    print(json.dumps({'plan': folder.name, 'deletions': [r['address'] for r in changes if r['change']['actions'] == ['delete']]}), flush=True)


def remove_load_balancers():
    if 'oficina' not in aws('eks', 'list-clusters')['clusters']:
        print('Project EKS already absent; no Kubernetes cleanup repeated', flush=True)
        return
    run(['aws', 'eks', 'update-kubeconfig', '--name', 'oficina', '--region', 'us-east-1'])
    services = json.loads(run(['kubectl', 'get', 'services', '-A', '-o', 'json']))['items']
    owned = [s for s in services if s['spec']['type'] == 'LoadBalancer'
             and s['metadata']['namespace'] in ['homolog', 'production', 'observability']]
    arns = []
    for service in owned:
        namespace, name = service['metadata']['namespace'], service['metadata']['name']
        assert name in ['oficina-mecanica-gateway', 'oficina-monitoring-grafana'], 'Unexpected LoadBalancer Service'
        hostnames = {x.get('hostname') for x in service.get('status', {}).get('loadBalancer', {}).get('ingress', [])}
        lbs = aws('elbv2', 'describe-load-balancers')['LoadBalancers']
        arns += [lb['LoadBalancerArn'] for lb in lbs if lb['DNSName'] in hostnames]
        run(['kubectl', 'delete', 'service', name, '-n', namespace, '--wait=true', '--timeout=300s'])
    for _ in range(60):
        remaining = {lb['LoadBalancerArn'] for lb in aws('elbv2', 'describe-load-balancers')['LoadBalancers']} & set(arns)
        if not remaining:
            print('Project LoadBalancer Services and NLBs removed', flush=True)
            return
        time.sleep(5)
    raise RuntimeError('NLB deletion incomplete; cluster preserved for controller reconciliation')


def verify_and_remove_backend(states):
    attributes = [(r['type'], i['attributes']) for state in states.values()
                  for r in state.get('resources', []) if r.get('mode') == 'managed'
                  for i in r.get('instances', [])]
    expected_functions = {a['function_name'] for t, a in attributes if t == 'aws_lambda_function'}
    expected_apis = {a['id'] for t, a in attributes if t == 'aws_apigatewayv2_api'}
    expected_databases = {a['identifier'] for t, a in attributes if t == 'aws_db_instance'}
    expected_repositories = {a['name'] for t, a in attributes if t == 'aws_ecr_repository'}
    assert 'oficina' not in aws('eks', 'list-clusters')['clusters']
    assert not expected_functions & {f['FunctionName'] for f in aws('lambda', 'list-functions')['Functions']}
    assert not expected_apis & {a['ApiId'] for a in aws('apigatewayv2', 'get-apis')['Items']}
    assert not expected_databases & {d['DBInstanceIdentifier'] for d in aws('rds', 'describe-db-instances')['DBInstances']}
    assert not expected_repositories & {r['repositoryName'] for r in aws('ecr', 'describe-repositories')['repositories']}
    nodes = aws('ec2', 'describe-instances', '--filters', 'Name=tag:eks:cluster-name,Values=oficina',
                'Name=instance-state-name,Values=pending,running,stopping,stopped')['Reservations']
    assert not nodes, 'Project node instances remain'
    volumes = aws('ec2', 'describe-volumes', '--filters', 'Name=tag:kubernetes.io/cluster/oficina,Values=owned')['Volumes']
    assert not volumes, 'Project volumes remain; inspect before deleting any data'
    cluster_groups = {v['cluster_security_group_id'] for t, a in attributes if t == 'aws_eks_cluster'
                      for v in a.get('vpc_config', []) if v.get('cluster_security_group_id')}
    groups = aws('ec2', 'describe-security-groups')['SecurityGroups']
    for group in groups:
        if group['GroupId'] not in cluster_groups:
            continue
        assert group['GroupName'].startswith('eks-cluster-sg-oficina-'), 'Unexpected cluster security group'
        attachments = aws('ec2', 'describe-network-interfaces', '--filters',
                          'Name=group-id,Values='+group['GroupId'])['NetworkInterfaces']
        assert not attachments, 'Cluster security group still attached: preserve until ENIs are released'
        run(['aws', 'ec2', 'delete-security-group', '--group-id', group['GroupId']])
    print('AWS verification passed: EKS, nodes, RDS, Lambdas, Gateway, ECR and project volumes absent', flush=True)
    versions = aws('s3api', 'list-object-versions', '--bucket', BUCKET)
    objects = versions.get('Versions', []) + versions.get('DeleteMarkers', [])
    prefixes = ('oficina-infra-k8s/', 'oficina-infra-db/', 'oficina-lambda-auth/', 'oficina/config/')
    assert all(o['Key'].startswith(prefixes) for o in objects), 'Unexpected backend content: bucket preserved'
    for offset in range(0, len(objects), 1000):
        payload = {'Objects': [{'Key': o['Key'], 'VersionId': o['VersionId']} for o in objects[offset:offset+1000]], 'Quiet': True}
        result = aws('s3api', 'delete-objects', '--bucket', BUCKET, '--delete', json.dumps(payload))
        assert not result.get('Errors'), 'Backend object deletion incomplete'
    run(['aws', 's3api', 'delete-bucket', '--bucket', BUCKET])
    print('Dedicated FIAP state/contract bucket removed after all runtime stacks were verified absent', flush=True)


def main():
    os.umask(0o077)
    assert aws('sts', 'get-caller-identity')['Account'] == ACCOUNT
    operation = os.environ.get('TEARDOWN_OPERATION', 'plan')
    assert operation in ['plan', 'destroy']
    states = inventory()
    with tempfile.TemporaryDirectory(prefix='fiap-teardown-') as directory:
        root = pathlib.Path(directory)
        folders = {key: prepare(root, key) for key in states}
        for folder in folders.values():
            plan(folder)
        if operation == 'plan':
            print('Plans reviewed: no resources changed', flush=True)
            return
        assert os.environ.get('TEARDOWN_CONFIRMATION') == 'DESTROY-FIAP-630266487412'
        delivery = json.loads(pathlib.Path('docs/fase3/entrega-portal.json').read_text())
        assert delivery['pendencias_tecnicas'] is False, 'Finish Phase 3 validation first'
        remove_load_balancers()
        for key, folder in folders.items():
            # Refresh after controller cleanup and after each dependent stack has been destroyed.
            plan(folder)
            run(['terraform', 'apply', '-input=false', '-no-color', 'destroy.tfplan'], folder)
            state = json.loads(run(['terraform', 'state', 'pull'], folder))
            assert not [r for r in state.get('resources', []) if r.get('mode') == 'managed']
            print(json.dumps({'destroyed_state': key, 'managed_resources_remaining': 0}), flush=True)
        verify_and_remove_backend(states)


if __name__ == '__main__':
    main()
