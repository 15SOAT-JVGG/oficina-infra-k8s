from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from xml.sax.saxutils import escape
import subprocess,textwrap
root=Path('docs/fase3/diagramas')
common='graph [bgcolor="white",pad="0.25",nodesep="0.35",ranksep="0.5"]; node [fontname="DejaVu Sans",fontsize=15,shape=box,style="rounded,filled",fillcolor="#eef5fb",color="#829bb3",margin="0.18"]; edge [fontname="DejaVu Sans",fontsize=11,color="#4b647d",arrowsize=0.8];'
component='''digraph G {
'''+common+'''
rankdir=TB;
user[label="Cliente / funcionário",fillcolor="#e0f2ee"];
gw[label="API Gateway HTTP\nHTTPS / entrada pública",fillcolor="#dbeaf8"];
auth[label="Lambda customer-auth\nCPF -> cliente ativo -> JWT"];
jwt[label="Lambda jwt-authorizer\nAssinatura / issuer / expiração"];
link[label="VPC Link"];
subgraph cluster_vpc { label="VPC AWS / us-east-1"; fontname="DejaVu Sans";fontsize=18;color="#a9becf";style="rounded";
  db[label="RDS PostgreSQL 16\nprivado / TLS",shape=cylinder,fillcolor="#e0f2ee"];
  nlb[label="NLB interno / API"];
  ng[label="NLB interno / Grafana"];
  subgraph cluster_eks {label="EKS oficina";color="#cedce8";style="rounded";
    api[label="API Quarkus\n8080 + management 9000"];
    grafana[label="Grafana\nlogin próprio",fillcolor="#ffedcf"];
    prom[label="Prometheus"];
    alloy[label="Alloy\nlogs + OTLP"];
    loki[label="Loki"];
    tempo[label="Tempo"];
    bb[label="Blackbox\nuptime público"];
  }
}
cw[label="CloudWatch\nlogs Lambda / Gateway",fillcolor="#f0f0f0"];
user->gw[label="HTTPS"];
gw->auth[label="POST CPF"];
gw->jwt[label="JWT protegido"];
gw->link;link->nlb;link->ng;nlb->api;ng->grafana;
auth->db[label="consulta status"];
api->db[label="persistência"];
grafana->prom;grafana->loki;grafana->tempo;
prom->api[label="scrape 9000",style=dashed];prom->bb[style=dashed];bb->gw[label="sondagem",style=dashed,constraint=false];
api->alloy[label="OTLP / logs",style=dashed];alloy->loki;alloy->tempo;
auth->cw[style=dashed];jwt->cw[style=dashed];
{rank=same;auth;jwt;link;}
}
'''
# Escape newlines inside Graphviz strings.
component=component.replace('\nprivado','\\nprivado').replace('\nHTTPS','\\nHTTPS').replace('\nCPF','\\nCPF').replace('\nAssinatura','\\nAssinatura').replace('\n8080','\\n8080').replace('\nlogin','\\nlogin').replace('\nlogs','\\nlogs').replace('\nuptime','\\nuptime')
(root/'componentes.dot').write_text(component)
entities={
'customer':['customer_id PK','document UNIQUE','active'],
'vehicle':['vehicle_id PK','customer_id (opcional)','license_plate UNIQUE'],
'worker':['worker_id PK','email UNIQUE / profile','active'],
'work_order':['work_order_id PK','customer_id / vehicle_id','assigned_worker_id (opcional)','status / opened_at','closed_at / cancelled_at'],
'work_order_history':['work_order_history_id PK','work_order_id','previous_status / new_status','changed_at'],
'estimate':['estimate_id PK','work_order_id','status / total_amount'],
'estimate_item':['estimate_item_id PK','estimate_id / part_id','quantity / unit_price'],
'parts':['part_id PK','stock_quantity','version (@Version)'],
'service_item':['service_item_id PK','base_price','active'],
'work_order_service':['work_order_service_id PK','work_order_id','service_item_id (opcional)','price / description'],
'estimate_decision_token':['estimate_decision_token_id PK','work_order_id / estimate_id (UUID)','expires_at / consumed_at'],
'app_users':['id PK (numérico)','username UNIQUE / role','active / credencial (não exibida)']}
er='digraph ER {\n'+common+'\nrankdir=TB;node [shape=record,fontsize=13,fillcolor="#f3f7fb"];\n'
for name,fields in entities.items():er+=name+' [label="{'+name.upper()+'|'+'\\l'.join(fields)+'\\l}"];\n'
for a,b,label in [('customer','vehicle','0..1 -> 0..N'),('customer','work_order','1 -> 0..N'),('vehicle','work_order','1 -> 0..N'),('worker','work_order','0..1 -> 0..N'),('work_order','work_order_history','1 -> 0..N'),('work_order','estimate','1 -> 0..N'),('estimate','estimate_item','1 -> 0..N'),('parts','estimate_item','1 -> 0..N'),('work_order','work_order_service','1 -> 0..N'),('service_item','work_order_service','0..1 -> 0..N')]:er+=f'{a}->{b} [label="{label}"];\n'
er+='work_order->estimate_decision_token [style=dashed,label="UUID lógico",constraint=false];estimate->estimate_decision_token [style=dashed,label="UUID lógico"];\n{rank=same;customer;worker;app_users;}\n}'
(root/'modelo-er.dot').write_text(er)
for name in ['componentes','modelo-er']:
 for fmt in ['svg','png']:
  subprocess.run(['dot',f'-T{fmt}','-Gdpi=160',str(root/f'{name}.dot'),'-o',str(root/f'{name}.{fmt}')],check=True)
fontpath='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
fontbold='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
def sequence(name,title,actors,events,footer):
 w=1500;h=260+len(events)*80
 im=Image.new('RGB',(w,h),'white');d=ImageDraw.Draw(im);svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}"><rect width="100%" height="100%" fill="white"/>']
 def text(x,y,t,size=20,bold=False,center=True,color='#17324d'):
  font=ImageFont.truetype(fontbold if bold else fontpath,size)
  for i,line in enumerate(t.split('\n')):
   xx=x-d.textlength(line,font=font)/2 if center else x
   d.text((xx,y+i*(size+5)),line,font=font,fill=color)
   svg.append(f'<text x="{x}" y="{y+size+i*(size+5)}" text-anchor="{"middle" if center else "start"}" font-family="DejaVu Sans,sans-serif" font-size="{size}" font-weight="{"bold" if bold else "normal"}" fill="{color}">{escape(line)}</text>')
 def line(x1,y1,x2,y2,color='#526b82',dash=False,width=2):
  if dash:
   for yy in range(int(y1),int(y2),12):d.line((x1,yy,x2,min(yy+6,y2)),fill=color,width=width)
  else:d.line((x1,y1,x2,y2),fill=color,width=width)
  svg.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}"'+(' stroke-dasharray="6 6"' if dash else '')+'/>')
 text(w/2,25,title,27,True)
 xs=[130+i*(1240/(len(actors)-1)) for i in range(len(actors))]
 for x,a in zip(xs,actors):
  d.rounded_rectangle((x-112,85,x+112,154),radius=9,fill='#e8f1f9',outline='#829bb3',width=2)
  svg.append(f'<rect x="{x-112}" y="85" width="224" height="69" rx="9" fill="#e8f1f9" stroke="#829bb3"/>')
  text(x,97,a,18,True);line(x,158,x,h-90,dash=True,color='#b3c2cf')
 for i,(a,b,msg) in enumerate(events):
  y=215+i*80;x1,x2=xs[a],xs[b]
  label='\n'.join(textwrap.wrap(f'{i+1}. {msg}',width=max(22,int(abs(x2-x1)/10))))
  labely=y-(label.count('\n')+1)*24-7
  width=max(d.textlength(t,font=ImageFont.truetype(fontpath,18)) for t in label.split('\n'))+14
  mid=(x1+x2)/2
  d.rectangle((mid-width/2,labely-2,mid+width/2,y-4),fill='white')
  svg.append(f'<rect x="{mid-width/2}" y="{labely-2}" width="{width}" height="{y-labely-2}" fill="white"/>')
  text(mid,labely,label,18)
  line(x1,y,x2,y,color='#245a86')
  direction=1 if x2>x1 else -1
  pts=[(x2,y),(x2-direction*12,y-6),(x2-direction*12,y+6)]
  d.polygon(pts,fill='#245a86');svg.append('<polygon points="'+' '.join(f'{x},{yy}' for x,yy in pts)+'" fill="#245a86"/>')
 text(w/2,h-64,footer,17)
 svg.append('</svg>');(root/f'{name}.svg').write_text('\n'.join(svg));im.save(root/f'{name}.png')
sequence('autenticacao','Autenticação por CPF e consumo protegido',['Cliente','API Gateway','Lambda\ncustomer-auth','RDS\nPostgreSQL','Lambda\njwt-authorizer','API Quarkus'],[
(0,1,'POST /v1/auth/customer: CPF'),(1,2,'Integração pública'),(2,3,'Consultar cliente e active'),(3,2,'Existência e status'),(2,0,'Cliente ativo: 200 + JWT CUSTOMER'),(0,1,'GET /v1/me/work-orders + Bearer'),(1,4,'Validar assinatura / issuer / expiração'),(4,1,'Permitir ou negar'),(1,5,'Encaminhar; API aplica RBAC e propriedade'),(5,0,'Resposta do recurso autorizado')], 'CPF inválido/ausente/inativo: sem token. Ausência de Bearer pode ser recusada no Gateway com 401.')
sequence('abertura-os','Abertura de OS: JWT de funcionário ADMIN / MECHANIC',['Funcionário','API Gateway','JWT\nAuthorizer','API /\nWorkOrderService','RDS\nPostgreSQL','Adaptador\nSMTP'],[
(0,1,'POST /v1/work-orders + Bearer'),(1,2,'Validar JWT'),(2,1,'Permitir ou negar'),(1,3,'Encaminhar; validar RBAC e DTO'),(3,4,'Transação: consultar referências'),(4,3,'Cliente / veículo / funcionário opcional'),(3,4,'Persistir OS RECEIVED e itens opcionais'),(3,5,'Solicitar notificação de acompanhamento'),(5,3,'Entrega ou falha tratada'),(3,4,'Confirmar transação'),(3,0,'201 Created + Location')], 'Pré-condição: login do funcionário. Falha transacional exige rollback; CUSTOMER não autoriza este POST.')
print('Four diagrams exported as PNG/SVG; Mermaid sources retained.')
