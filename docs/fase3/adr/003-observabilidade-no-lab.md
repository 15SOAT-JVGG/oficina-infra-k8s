# ADR-003 - Observabilidade compartilhada no Learner Lab

Status: estado implementado documentado nesta revisão.

## Contexto

O requisito permite escolha livre de ferramenta. O cluster precisa expor sinais técnicos,
logs e traces sem abrir publicamente o management. O EBS CSI ficou CREATE_FAILED porque
não conseguia obter credenciais; simulação IAM negou alterar trust/permissões da LabRole.

## Decisão registrada

Prometheus/Grafana para métricas; Alloy/Loki para JSON; Alloy/Tempo para tracing; Blackbox
para a sondagem pública; logs Lambda/Gateway no CloudWatch. A stack vive em observability.
Somente Grafana é roteado publicamente pelo Gateway/NLB interno com login obrigatório.
Dois dashboards versionados na pasta FIAP substituem os genéricos; a visão geral é a home.

No Lab, usar emptyDir e retirar o add-on EBS defeituoso após plano controlado que confirmou
PVCs Pending sem volume. Dashboards/configurações são reprovisionados do Git; histórico e
alterações manuais no Grafana podem ser perdidos quando os pods forem recriados.

## Consequências e limites

A decisão viabiliza a demonstração, sem garantia de retenção durável. Não se declara que
uma configuração de retenção em horas/dias garante sobrevivência a recriação de pod.
Produção comercial deve reavaliar armazenamento e IAM dedicado. A Lambda tem tracing
opcional; o caminho privado/exportação não foi demonstrado nesta revisão.

O deploy reconcilia ServiceMonitor da aplicação, pois o primeiro deploy pode ocorrer antes
do CRD, e aplica a Probe após o Blackbox. Dados de negócio exigem instrumentação/agregação
própria; gráficos de HTTP/JVM não equivalem a volume diário e tempo médio de cada etapa da OS.

## Verificação

Workflow de publicação, login/banco Grafana HTTP 200, dois dashboards, séries API/uptime,
logs JSON e traces reais. Testar alertas específicos de OS e a entrega/notificação antes
de declarar encerrada a conformidade de monitoramento.
