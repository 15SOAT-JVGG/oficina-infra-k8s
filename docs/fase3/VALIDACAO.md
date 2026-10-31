# Matriz de atendimento - Fase 3

Revisão: 30/10/2026 (BRT). Base: enunciado fornecido pelo usuário, páginas 2-5,
branches homolog e evidência de execução. O usuário confirmou que ainda não produziu
vídeo nem PDF final de entrega. Os documentos e diagramas deste pacote foram preparados
nesta revisão. **O projeto ainda não está integralmente pronto para a entrega.**

Estados: **Comprovado** = evidência observada; **Implementado** = fonte/configuração existente,
sem demonstração completa; **Parcial** = cobertura incompleta; **Pendente** = item ainda faltante.

## Infraestrutura, segurança e CI/CD

| Requisito | Estado | Evidência e limite |
|---|---|---|
| API Gateway de entrada | Comprovado | API pública em HTTPS, integrações privadas e Swagger/OpenAPI acessíveis |
| Função serverless autentica CPF | Comprovado | Cliente sintético ativo confirmado; login 200; fonte consulta status no RDS |
| JWT e proteção de rotas sensíveis | Comprovado | CUSTOMER 200; sem token 401; Bearer inválido/alterado e RBAC 403 |
| CPF inválido/inativo | Implementado | Validação e checagem active no código/testes; não foi desativado cliente para teste de runtime nesta revisão |
| Quatro repositórios separados | Comprovado | app, lambda-auth, infra-k8s e infra-db existentes e públicos |
| CI/CD funcional dos quatro | Comprovado em homolog | Runs de entrega concluídos dos quatro; o DB não foi reaplicado com a sessão atual |
| main exige PR | Comprovado | Regras ativas de rulesets nos quatro; a API antiga de branch protection sozinha não refletia essas regras |
| Deploy automático homolog/production | Implementado | Triggers por branch nos quatro workflows; nenhuma execução em production encontrada |
| Banco gerenciado | Comprovado | RDS PostgreSQL provisionado e consumido por aplicação/autenticação; sem inspeção SQL nesta revisão |
| Kubernetes e escalabilidade | Implementado | EKS, Metrics Server e HPA 1-6 réplicas; teste atual de carga/subida/descida ainda deve ser gravado |
| Provisionamento Terraform | Comprovado | Applies homolog e reconciliação com plano/lock; stack Helm é etapa separada |
| Dockerfile quando aplicável | Implementado | Aplicação tem Dockerfile; Lambdas são binários ZIP; repositórios Terraform não necessitam container de runtime |
| Avaliador soat-architecture | Comprovado | Acesso confirmado nos quatro repositórios via API do GitHub |

## Observabilidade

| Requisito | Estado | Evidência e limite |
|---|---|---|
| Integração com ferramenta de observabilidade | Comprovado | Stack Prometheus/Grafana/Loki/Tempo/Alloy/Blackbox publicada |
| Grafana simples e acessível | Comprovado | 31 dashboards reduzidos a 2 na pasta FIAP; home aponta para a visão geral; login e banco HTTP 200 |
| CPU e memória Kubernetes | Comprovado | Exporters/targets disponíveis e dashboard de recursos versionado |
| Coleta da API | Comprovado | 2 targets oficina-mecanica-management em homolog, ambos UP após reaplicar ServiceMonitor |
| Latência e tráfego HTTP | Parcial | Painéis e filtro de histogramas existem; auditoria real não encontrou http_server_requests_seconds_count/bucket. Existem métricas de conexões/bytes, que não substituem latência p95 |
| Healthchecks/uptime | Comprovado com limite | Probe pública com sucesso=1, readiness/liveness nos manifests. Probe mede Swagger; não representa todas as operações/integrações |
| Alertas de falha no processamento de OS | Pendente | Existem alertas técnicos genéricos; faltam sinal/regra específica de OS, demonstração firing/resolved e evidência do destino de notificação |
| Logs JSON | Comprovado | Amostra Loki contém somente entradas JSON; nenhum conteúdo foi exportado para este documento |
| Correlação entre requisições | Parcial | Filtro X-Request-ID/MDC existe; amostra teve traceId, mas não requestId. Falta evidenciar um fluxo correlacionado real |
| Traces em execução | Pendente de evidência | Tempo consultado sem traces; presença de traceId no log não comprova exportação/consulta do trace. Lambda OTLP é opcional e não foi comprovado |
| Volume diário de OS | Pendente | Nenhuma série/agregação de negócio correspondente nos dashboards/auditoria |
| Tempo médio por etapa | Pendente | Endpoint atual mede abertura->fechamento, sem separar Diagnóstico/Execução/Finalização no Grafana |
| Erros/falhas de integrações | Parcial | Há sinal HTTP 5xx e logs, sem painel/métrica dedicada das integrações como SMTP/DB/autenticação |

## Documentação e entrega

| Requisito | Estado | Evidência e limite |
|---|---|---|
| Diagrama de componentes completo | Documentado | ARQUITETURA.md + componentes PNG/SVG/Mermaid |
| Sequência de CPF e abertura de OS | Documentado | SEQUENCIAS.md + dois diagramas exportáveis/editáveis |
| RFCs | Documentado | RFCs cloud, PostgreSQL e autenticação, com justificativas e limites |
| ADRs | Documentado | Comunicação, HPA e observabilidade; complementam os ADRs existentes da aplicação |
| Justificativa do banco / ER / relacionamentos | Documentado | MODELO-DE-DADOS.md + ER atualizado, inclusive active, app_users e tokens de decisão |
| README de cada repo com propósito/stack/deploy/diagrama | Parcial | Existem os quatro; faltam alinhamento/link explícito de Swagger/deploy/documentação em alguns e atualização da referência ao vídeo antigo |
| Vídeo atual <=15 min | Pendente do usuário | Roteiro preparado; usuário gravará após concluir as lacunas técnicas |
| PDF único para o Portal | Pendente do vídeo | Folha de entrega preparada; dossiê técnico não é submissão final enquanto faltar vídeo e conformidade |

## Evidências reproduzíveis

- [Publicação do Grafana simplificado e reconciliação](https://github.com/15SOAT-JVGG/oficina-infra-k8s/actions/runs/41150666377).
- [Auditoria: dois dashboards, home, API targets, métricas, uptime, logs e Tempo](https://github.com/15SOAT-JVGG/oficina-infra-k8s/actions/runs/41151717405).
- [Matriz HTTP real do Authorizer](https://github.com/15SOAT-JVGG/oficina-lambda-auth/actions/runs/41149042492).
- [Confirmação da conta sintética ativa](https://github.com/15SOAT-JVGG/oficina-app/actions/runs/41148875214).
- [Deploy da aplicação em homolog](https://github.com/15SOAT-JVGG/oficina-app/actions/runs/41072488615).
- [Deploy da Lambda em homolog](https://github.com/15SOAT-JVGG/oficina-lambda-auth/actions/runs/40991742239).
- [Apply de banco em homolog](https://github.com/15SOAT-JVGG/oficina-infra-db/actions/runs/40980315346).

## Ordem para fechar a fase

1. Restabelecer as séries HTTP/histogramas e demonstrar trace real no Tempo, correlacionado ao log.
2. Implementar as agregações persistentes de volume diário e duração por etapa; definir a semântica de Finalização/cancelamentos.
3. Instrumentar falhas de OS/integrações e demonstrar alerta disparando e resolvendo.
4. Atualizar links/READMEs dos quatro repositórios e registrar evidência de HPA/pipelines. Conferir credenciais do DB respeitando a restrição atual de secrets a três repositórios; não ampliar esse escopo automaticamente.
5. Usuário grava o vídeo; conferir acesso/duração, preencher folha e gerar o PDF final de submissão.

A política do Lab impediu o uso de EBS CSI com a identidade necessária. emptyDir permitiu a
homologação, mas histórico de telemetria é volátil. O enunciado não determina EBS, Multi-AZ
ou um fornecedor específico de monitoramento: essas limitações não são transformadas aqui
em exigências inventadas, mas devem ficar claras na apresentação.

## Atualização operacional - 31/10/2026 (BRT)

- Deploy homolog concluído: https://github.com/15SOAT-JVGG/oficina-app/actions/runs/41158248740
- Seed espaçado aprovado: seis OS, uma por estado; HTTP 200/201, sem 503 nesta execução:
  https://github.com/15SOAT-JVGG/oficina-app/actions/runs/41158958643
- Carga separada: 211 tentativas, oito 503; teste reprovado corretamente:
  https://github.com/15SOAT-JVGG/oficina-app/actions/runs/41158493007
- Réplicas Ready passaram de duas para quatro durante a carga e retornaram a duas
  nas amostras do seed posterior. Isso comprova reação do HPA, sem comprovar estabilidade.
- NLB cross-zone habilitado, mas 503 persistiu. Há também falhas SMTP por limite de envio;
  elas não explicam os 503 da carga de login, que não envia e-mail. Causa ainda aberta.
- Indicadores de negócio, histogramas HTTP, traces e alertas específicos continuam pendentes.
