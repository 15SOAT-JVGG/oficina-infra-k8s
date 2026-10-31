"""Verify dashboard configuration without logging user logs or credentials."""
import base64
import json
import os
import time
import urllib.request

url='https://dcs5hfax0e.execute-api.us-east-1.amazonaws.com/observability'
auth=base64.b64encode(('admin:'+os.environ['GRAFANA_ADMIN_PASSWORD']).encode()).decode()
def get(uid):
    request=urllib.request.Request(url+'/api/dashboards/uid/'+uid,headers={'Authorization':'Basic '+auth})
    with urllib.request.urlopen(request,timeout=15) as response:
        return json.load(response)['dashboard']
for attempt in range(18):
    try:
        api=get('oficina-api-jvm')
        infra=get('oficina-kubernetes')
        row=next(p for p in api['panels'] if p['type']=='row')
        memory=next(p for p in infra['panels'] if p['id']==4)
        assert row['collapsed'] is True
        assert '| line_format' in row['panels'][0]['targets'][0]['expr']
        assert row['panels'][0]['options']['enableLogDetails'] is True
        assert row['panels'][0]['options']['wrapLogMessage'] is False
        assert '/ 1000000' in memory['targets'][0]['expr']
        assert memory['fieldConfig']['defaults']['unit']=='suffix: MB'
        print('Dashboards verified: collapsed logs, concise lines, expandable details, memory in MB.')
        break
    except Exception:
        if attempt==17:
            raise SystemExit('Dashboard readability verification failed; credentials and response contents suppressed.')
        time.sleep(5)
