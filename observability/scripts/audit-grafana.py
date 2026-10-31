"""Read-only evidence collection; never emit credentials, log contents or trace IDs."""
import base64
import json
import os
import time
import urllib.parse
import urllib.request

base = os.environ['GRAFANA_URL'].rstrip('/')
auth = base64.b64encode(('admin:' + os.environ['GRAFANA_ADMIN_PASSWORD']).encode()).decode()

def get(path):
    request = urllib.request.Request(base + path, headers={'Authorization': 'Basic ' + auth})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)

def query(expression):
    result = get('/api/datasources/proxy/uid/prometheus/api/v1/query?' + urllib.parse.urlencode({'query': expression}))
    return result.get('data', {}).get('result', [])

dashboards=get('/api/search?type=dash-db')
print('dashboards', json.dumps([{k: d.get(k) for k in ('uid', 'title', 'folderTitle')} for d in dashboards], ensure_ascii=False))
if os.getenv('REQUIRE_SIMPLE') == 'true':
    assert {d['uid'] for d in dashboards} == {'oficina-api-jvm', 'oficina-kubernetes'}, 'Unexpected dashboard set'
    home=get('/api/dashboards/home')
    redirect = home.get('redirectUri', '')
    print('home_dashboard', json.dumps({'title':home.get('dashboard',{}).get('title'), 'redirect':redirect}))
    # Grafana assigns a synthetic UID to a home dashboard loaded from a JSON file.
    expected_home = '/observability/d/default-home-dashboard/01-oficina3a-visao-geral'
    assert home.get('dashboard',{}).get('uid') == 'oficina-api-jvm' or redirect == expected_home, 'Unexpected home dashboard'
print('datasources', json.dumps([{k:d.get(k) for k in ('uid', 'name', 'type')} for d in get('/api/datasources')]))
evidence={}
for name, expr in {
    'scrape_targets': 'count by(job) (up)',
    'healthy_targets': 'sum by(job) (up)',
    'app_target_namespaces': 'count by(namespace) (up{job="oficina-mecanica-management"})',
    'http_metric_names': 'count by(__name__) ({job="oficina-mecanica-management",__name__=~"http.*"})',
    'http_request_rate_5m': 'sum(rate(http_server_requests_seconds_count{job="oficina-mecanica-management",namespace="homolog"}[5m]))',
    'http_p95_5m': 'histogram_quantile(0.95, sum by(le) (rate(http_server_requests_seconds_bucket{job="oficina-mecanica-management",namespace="homolog"}[5m])))',
    'http_series': 'count(http_server_requests_seconds_count{namespace="homolog"})',
    'latency_histograms': 'count(http_server_requests_seconds_bucket{namespace="homolog"})',
    'business_series': 'count({__name__=~".*work.?order.*|.*workshop.*"})',
    'daily_work_orders': 'max(workshop_work_orders_opened_today{namespace="homolog"})',
    'stage_durations': 'max by(stage) (workshop_work_order_stage_duration_seconds{namespace="homolog"})',
    'integration_counters': 'sum by(integration,outcome) (workshop_integration_calls_total{namespace="homolog"})',
    'processing_failures': 'sum(workshop_work_order_processing_failures_total{namespace="homolog"})',
    'uptime_probes': 'sum(probe_success)',
}.items():
    evidence[name]=query(expr)
    print(name, json.dumps(evidence[name]))
rules = get('/api/datasources/proxy/uid/prometheus/api/v1/rules?type=alert')
print('alert_rules', json.dumps([{'name':r.get('name'), 'state':r.get('state')} for g in rules.get('data',{}).get('groups',[]) for r in g.get('rules',[]) if r.get('type')=='alerting']))
for kind, path in {
    'loki_services':'/api/datasources/proxy/uid/loki/loki/api/v1/label/service/values',
    'tempo_search':'/api/datasources/proxy/uid/tempo/api/search?' + urllib.parse.urlencode({'q':'{}','limit':5,'start':int(time.time())-86400,'end':int(time.time())}),
}.items():
    try:
        result=get(path)
        if kind=='tempo_search':
            print(kind, json.dumps({'count':len(result.get('traces',[])), 'services':sorted({t.get('rootServiceName','unknown') for t in result.get('traces',[])})}))
        else:
            print(kind, json.dumps(result.get('data',[])))
    except Exception as error:
        print(kind, 'unavailable', type(error).__name__)
try:
    path='/api/datasources/proxy/uid/loki/loki/api/v1/query_range?' + urllib.parse.urlencode({'query':'{environment="homolog"}', 'limit':100})
    result=get(path)
    lines=[v[1] for stream in result.get('data',{}).get('result',[]) for v in stream.get('values',[])]
    parsed=[]
    for line in lines:
        try: parsed.append(json.loads(line))
        except (ValueError,TypeError): pass
    print('log_evidence', json.dumps({'entries':len(lines),'json_entries':len(parsed),'correlated_entries':sum(bool(d.get('requestId') or d.get('mdc',{}).get('requestId')) for d in parsed),'traced_entries':sum(bool(d.get('traceId') or d.get('mdc',{}).get('traceId')) for d in parsed)}))
except Exception as error:
    print('log_evidence unavailable',type(error).__name__)

matched=0
# Confirm an actual trace is retrievable and has a matching application log, without exporting identifiers.
try:
    search=get('/api/datasources/proxy/uid/tempo/api/search?' + urllib.parse.urlencode({'q':'{ resource.service.name = "tech-challenge-fase-1" }','limit':20,'start':int(time.time())-3600,'end':int(time.time())}))
    traces=search.get('traces',[])
    matched=0
    for trace in traces:
        trace_id=trace.get('traceID','')
        if not trace_id: continue
        logs=get('/api/datasources/proxy/uid/loki/loki/api/v1/query_range?' + urllib.parse.urlencode({'query':'{environment="homolog"} |= "'+trace_id+'"','limit':1,'start':str((int(time.time())-3600)*1000000000),'end':str(int(time.time())*1000000000)}))
        if logs.get('data',{}).get('result'): matched+=1
    print('trace_log_correlation',json.dumps({'searched_application_traces':len(traces),'traces_with_matching_logs':matched}))
except Exception as error:
    print('trace_log_correlation unavailable',type(error).__name__)

if os.getenv('REQUIRE_PHASE3') == 'true':
    assert evidence['daily_work_orders'], 'Daily business metric missing'
    assert {r['metric']['stage'] for r in evidence['stage_durations']} == {'DIAGNOSIS','IN_PROGRESS','COMPLETED'}, 'Stage durations missing'
    assert evidence['integration_counters'] and evidence['processing_failures'], 'Failure instrumentation missing'
    alert_names={r.get('name') for g in rules.get('data',{}).get('groups',[]) for r in g.get('rules',[])}
    assert {'WorkOrderProcessingFailure','WorkOrderNotificationFailure'} <= alert_names, 'OS rules missing'
    assert matched > 0, 'No actual trace/log correlation found'
    print('phase3_observability_validation PASSED')
