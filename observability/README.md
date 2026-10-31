# Observabilidade do EKS

Esta pasta mantém a stack compartilhada do cluster `oficina`. Ela é instalada uma vez no namespace
`observability`; namespaces de negócio `homolog` e `production` usam os mesmos Prometheus, Grafana,
Loki e Tempo. Labels de ambiente ajudam a filtrar os dados, mas não são uma barreira de autorização.

## Componentes e dados

- `kube-prometheus-stack`: Prometheus Operator, Grafana, Alertmanager, kube-state-metrics e node-exporter.
- Loki monolítico: uma réplica, filesystem em emptyDir e retenção de 72 horas para baixo volume acadêmico.
- Tempo: uma réplica, filesystem em emptyDir e retenção de 24 horas.
- Alloy: coleta stdout dos pods em `homolog`/`production` e recebe OTLP gRPC/HTTP internamente;
  métricas de Kubernetes continuam sendo coletadas pelo Prometheus.
- Blackbox Exporter: sondagem HTTP interna via CRD `Probe`.
- CloudWatch: datasource do Grafana usando a cadeia de credenciais do workload/nó; nenhuma chave é
  provisionada no browser ou no repositório.

Loki, Tempo, Alloy receiver, Prometheus e Alertmanager são Services ClusterIP e não têm Ingress ou
LoadBalancer nesta stack. Alloy é um DaemonSet e filtra pods pelo nó local para impedir ingestão
duplicada. Apenas `service`, `environment` e `level` são labels de log. `traceId`, `spanId`, request IDs
e demais campos estruturados permanecem no conteúdo do evento.

ClusterIP evita exposição externa, mas não restringe tráfego entre pods. A NetworkPolicy para o
endpoint de management da API ainda não foi aplicada: o enforcement pelo VPC CNI do cluster precisa
ser confirmado e habilitado antes de confiar em isolamento intra-cluster. O endpoint não deve ser
considerado acessível somente pelo Prometheus até essa validação.

Os tamanhos e réplicas são uma configuração inicial, não um sizing aprovado. O cluster usa nós
`t3.medium`; medir requests/limits e PVCs em homologação antes de confiar na retenção ou alertas.
No Learner Lab, a stack usa `emptyDir`: a política do Lab bloqueia criar a role
IAM dedicada do EBS CSI e alterar trust/permissões da LabRole. O add-on sem identidade
ficava em CREATE_FAILED e os PVCs nunca eram provisionados. O recurso Terraform do
add-on foi retirado; a recuperação controlada recusa remover o add-on se houver um
PVC de observabilidade com volume atribuído e permite somente sua remoção no plano.

**Histórico de métricas, logs, traces e alterações manuais no Grafana pode ser perdido
quando os pods forem recriados.** Dashboards e datasources versionados são reprovisionados.
Esta configuração serve à demonstração acadêmica, sem garantia de retenção durável.
Para persistência, configurar uma role EBS CSI com permissões adequadas antes de
reativar PVCs gp3. A StorageClass existente e PVCs pendentes são preservados na recuperação.

## Aplicação manual e serializada

O workflow `.github/workflows/observability.yml` é exclusivamente `workflow_dispatch` em `homolog`.
O cluster é compartilhado, por isso uma trava global serializa o apply. Configure no GitHub Environment
`homolog` os secrets temporários AWS e `GRAFANA_ADMIN_PASSWORD`; a senha é montada como Secret
Kubernetes. O workflow instala a stack, publica o contrato do NLB interno do Grafana no S3 e chama a
reconciliação do API Gateway para criar a rota pública somente depois que houver target saudável.

```shell
AWS_REGION=us-east-1 \
GRAFANA_ADMIN_PASSWORD='senha-admin-forte' \
observability/scripts/deploy.sh
```

O script instala charts com versões em `helm/versions.env`, espera os releases prontos e aplica as
regras e o dashboard. A versão do chart `kube-prometheus-stack` também fixa as versões transitivas
de Grafana, exporters e CRDs. Após o apply, conferir:

```shell
kubectl get pods,pvc -n observability
kubectl get servicemonitors,prometheusrules,probes -A
kubectl port-forward -n observability svc/oficina-monitoring-grafana 3000:80
```

Acesse o Grafana por `https://<api-gateway-homolog>/observability/`. A API Gateway termina TLS e usa
VPC Link para alcançar o NLB interno do Grafana; o login `admin` continua obrigatório. Port-forward
continua disponível para diagnóstico. Prometheus, Alertmanager, Loki, Tempo e o receiver OTLP seguem
internos; a rota pública encaminha somente à interface web do Grafana.

## Sondagens públicas

Depois que os endpoints estáveis do API Gateway e a rota pública de readiness estiverem confirmados,
crie Probe para cada ambiente (script não grava URLs em arquivos):

```shell
HOMOLOG_API_BASE_URL='https://<api-gateway-homolog>' \
PRODUCTION_API_BASE_URL='https://<api-gateway-production>' \
observability/scripts/apply-probes.py
```

O script monitora `GET /q/swagger-ui/` a cada 30 segundos. O Terraform configura a exceção pública de
Swagger/OpenAPI no API Gateway de `homolog`; até a próxima reconciliação, o Gateway atual continua
exigindo JWT nessas rotas. O Load Balancer direto da aplicação já responde a esses caminhos sem TLS,
então use o endpoint HTTPS do Gateway depois da reconciliação, não o endereço HTTP do ELB. A sonda
externa confirma Gateway e resposta HTTP da API; readiness interna verifica as dependências. Probe
não deve conter token/cookie, query string ou qualquer identificador privado. A regra
`PublicApiProbeFailed` dispara após dois minutos de falhas; sem Probe configurada, ausência de amostra
não significa saúde.

## Alertas e recepção

Os dashboards versionados cobrem cluster/pods e latência p95, erros HTTP, volume por rota e heap/GC
da API/JVM. As regras locais cobrem 5xx, p95 alto, targets ausentes, disponibilidade de réplicas,
OOM, reinícios, sondagem pública e HPA saturado. O Alertmanager fica operacional, mas canal e
destinatários ainda não foram definidos:
alertas ficam visíveis em Prometheus/Alertmanager e não são encaminhados externamente. Não considerar
notificação validada antes de escolher o canal e demonstrar firing/resolved.

O dashboard inicial cobre saúde do cluster, CPU/memória de pods e réplicas. Dashboards de latência,
erros e negócio dependem da instrumentação e dos nomes finais das métricas no `oficina-app`. CloudWatch
depende das permissões read-only da `LabRole`; valide logs do API Gateway, Lambda e RDS após instalar.
Credenciais expiradas do Learner Lab interrompem consulta CloudWatch.

## Rollback e limites

`helm history <release> -n observability` e `helm rollback <release> <revision> -n observability`
permitem voltar release por release. Não desinstale os charts nem remova PVCs como primeira ação.
CRDs persistem além da release do chart. Monólitos e volumes locais podem interromper ou perder acesso
à telemetria durante falha do cluster; a sondagem externa independente ainda depende da infraestrutura
e das URLs públicas do Gateway.

## Versões fixadas

As versões foram fixadas a partir dos repositórios oficiais dos charts em 25/10/2026. Revisar changelog,
compatibilidade com Kubernetes 1.34 e alterações de CRD antes de atualizar pins:

- [kube-prometheus-stack](https://github.com/prometheus-community/helm-charts/tree/main/charts/kube-prometheus-stack)
- [Grafana Community Helm charts: Loki e Tempo](https://github.com/grafana-community/helm-charts)
- [Grafana Alloy chart](https://github.com/grafana/alloy/tree/main/operations/helm/charts/alloy)
- [Blackbox Exporter chart](https://github.com/prometheus-community/helm-charts/tree/main/charts/prometheus-blackbox-exporter)
