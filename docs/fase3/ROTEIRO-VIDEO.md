# Roteiro simples - demonstração da Fase 3

[Vídeo gravado](https://youtu.be/hgZPRw7hWeA): 13min29s. Este roteiro permanece como guia
de apresentação e consulta; o conteúdo do vídeo ainda não foi revisado nesta atualização.

Meta de referência: 12 a 14 minutos. Limite do enunciado: 15 minutos. Consultar a matriz antes
da submissão; não apresentar painel vazio como indicador atendido.

## Preparação

- Abrir o diagrama de componentes, os quatro repositórios e uma execução de deploy concluída.
- Abrir Swagger, cliente HTTP e os dois dashboards do Grafana.
- Usar apenas dados sintéticos. Ocultar CPF, senha e JWT no enquadramento.
- Fazer o seed automático antes da gravação: seed_only, 6 OS. Importar no Postman
  o ambiente Massa Pronta exportado pela Action; não cadastrar cliente, veículo ou peça manualmente. A carga é separada: load_only,
  180 segundos, concorrência 2. Esses valores menores ainda precisam de validação de carga.
- Não executar carga junto com rollout. Não repetir seed para gerar pressão: cada lote permanece.

Acesso rápido: [guia com links e Postman](COMECE-AQUI.md). A massa é preparada antes
da gravação; no vídeo não é necessário mostrar cadastros de cliente, veículo ou peça.

## 1. Apresentação e arquitetura - 1 minuto

Fala sugerida: “Esta é a aplicação da oficina. Organizamos a solução em quatro repositórios:
aplicação, autenticação serverless, infraestrutura Kubernetes e banco gerenciado.”
Mostrar o diagrama e apontar Gateway, Lambda, EKS, PostgreSQL e observabilidade.

## 2. Pipeline e deploy - 2 minutos

Mostrar um PR, proteção da main, checks e uma execução concluída em homologação.
Apontar teste, publicação da imagem, rollout e smoke pelo Gateway. Mostrar também os
workflows dos outros três repositórios. Dizer que produção tem triggers configurados,
mas sua execução ainda não está comprovada nesta homologação.

## 3. Autenticação e API protegida - 2 minutos

Fazer login com CPF sintético ativo sem revelar seu valor nem o JWT. Mostrar apenas HTTP 200.
Consumir uma rota CUSTOMER com sucesso. Repetir sem token (401) e tentar uma rota
operacional como CUSTOMER (403). Explicar que a Lambda verifica cadastro/status e emite JWT.

## 4. Ordem de serviço - 2 minutos

Fala sugerida: “A massa sintética já foi criada automaticamente pelo seed antes da gravação.
Agora vou usar esse cliente, veículo e peça para demonstrar apenas o ciclo da OS.”

No Postman, executar a collection curta: login, abertura, diagnóstico, orçamento, login CPF,
consulta permitida, testes 401/403, aprovação, conclusão, entrega e consulta final.
Como funcionário, abrir uma OS e mostrar sua consulta. Usar o lote preparado para mostrar
Recebida, Diagnóstico, Aguardando aprovação, Em execução, Concluída e Entregue.
Explicar o orçamento e a reserva de estoque, sem expor dados pessoais.

## 5. Monitoramento e escala - 3 minutos

No Grafana, abrir Visão geral e Infraestrutura. Mostrar uptime, CPU, memória e réplicas.
Iniciar uma carga leve separada do seed, observar o HPA e sua recuperação. Não prometer
atingir seis pods. Se ocorrer 503, interromper e registrar a falha; não esconder o resultado.
Mostrar os painéis HTTP de tráfego, erros e latência, cuja coleta foi validada após a correção
dos histogramas. O p95 precisa de requisições na janela selecionada. Volume diário de OS,
tempo médio por etapa e falhas de integrações ainda dependem de implementação/validação.

## 6. Logs, traces e alertas - 2 minutos

Selecionar uma requisição de teste, mostrar log JSON e o trace correspondente no Tempo.
Demonstrar alerta de falha de OS disparando e resolvendo. Esses exemplos precisam estar
validados antes da gravação final: logs com traceId, sozinhos, não comprovam trace exportado.

## 7. Documentação e encerramento - 1 minuto

Mostrar componentes, as duas sequências, ER, RFCs e ADRs nos arquivos separados.
Encerrar com links dos quatro repositórios e confirmação de acesso do avaliador.

## Depois da gravação

Publicar no YouTube/Vimeo como público ou não listado, conferir acesso e duração de até
15 minutos e incluir o link na folha de entrega. O Portal pede um PDF único com links dos
repositórios, vídeo, documentação e confirmação do avaliador. Os arquivos separados são
material complementar; não substituem o vídeo nem o PDF único.

## Links dos documentos e fala sugerida

Não precisa ler cada arquivo inteiro no vídeo. Abra o documento, mostre o trecho indicado
por 10 a 20 segundos e use estas frases como apoio, adaptando para o que está demonstrado.

| Documento | O que mostrar / falar |
|---|---|
| [Comece aqui](COMECE-AQUI.md) | “Este é o índice de execução: reúne os acessos, a collection curta, o seed e as evidências das pipelines.” |
| [Massa pronta](MASSA-PRONTA.md) | “A massa foi criada automaticamente antes da gravação. Cliente, veículo e peça já existem; no Postman vou demonstrar somente login e o ciclo da OS.” |
| [Arquitetura](ARQUITETURA.md) e [diagrama de componentes](diagramas/componentes.png) | “O Gateway é a entrada HTTPS. A Lambda autentica o cliente e autoriza o JWT; a aplicação está no EKS e persiste no PostgreSQL gerenciado. O Grafana reúne métricas e logs.” |
| [Sequências](SEQUENCIAS.md), [autenticação](diagramas/autenticacao.png) e [abertura de OS](diagramas/abertura-os.png) | “Aqui mostramos a ordem das chamadas: CPF e token primeiro; depois o acesso autorizado e a transação de abertura da OS.” |
| [Modelo de dados](MODELO-DE-DADOS.md) e [ER](diagramas/modelo-er.png) | “Cliente e veículo se relacionam às OS; orçamento, itens e estoque mantêm a consistência do atendimento. O documento explica os relacionamentos e a evolução do modelo.” |
| [RFC-001: nuvem](rfc/001-cloud-gerenciada.md) | “A escolha de AWS e serviços gerenciados reduz a operação manual no laboratório. O documento registra alternativas e limitações do Learner Lab.” |
| [RFC-002: PostgreSQL](rfc/002-postgresql.md) | “O banco relacional foi escolhido pelas transações e integridade entre OS, orçamento e estoque. A evolução do schema também está documentada.” |
| [RFC-003: autenticação](rfc/003-autenticacao.md) | “A função valida CPF e cadastro ativo, emite JWT e o Authorizer protege as rotas. A aplicação aplica RBAC; CPF sozinho é uma limitação deste fluxo acadêmico.” |
| [ADR-001: comunicação](adr/001-comunicacao-e-fronteiras.md) | “Usamos HTTP síncrono no atendimento, com responsabilidades separadas para Gateway, autenticação e aplicação.” |
| [ADR-002: HPA](adr/002-hpa.md) | “O HPA muda a quantidade de pods conforme CPU e memória. Isso é diferente de aumentar o número de nós.” |
| [ADR-003: observabilidade](adr/003-observabilidade-no-lab.md) | “A stack é compartilhada e há somente dois dashboards. No Lab o histórico é efêmero; um reinício pode reduzir a janela de dados disponível.” |
| [Matriz de validação](VALIDACAO.md) | “Esta matriz distingue requisito comprovado, implementação e pendência. Uma pipeline verde não comprova sozinha todos os requisitos funcionais.” |
| [Investigação de 503](INVESTIGACAO-503.md) | “Registramos as falhas de carga e as hipóteses sem esconder resultados. Um seed aprovado não comprova estabilidade sob carga.” |
| [Folha de entrega](ENTREGA.md) | “Ao concluir a gravação, este documento reúne os quatro repositórios, o vídeo, a documentação e o acesso do avaliador.” |

## Links das pipelines dos quatro repositórios

| Repositório / pipeline | O que faz | Fala sugerida |
|---|---|---|
| [App: CI](https://github.com/15SOAT-JVGG/oficina-app/actions/workflows/ci.yml) | Build e testes Java/Quarkus, qualidade/cobertura, segurança e validação dos manifestos | “O PR passa pelos testes e verificações antes da entrega.” |
| [App: deploy](https://github.com/15SOAT-JVGG/oficina-app/actions/workflows/deploy.yml) | Em homolog/production, valida, publica imagem no ECR, aplica no cluster, espera readiness e testa Gateway/Authorizer/docs | “Aqui a imagem é identificada pelo commit e o rollout termina com testes pelo endereço público.” |
| [Lambda: CI](https://github.com/15SOAT-JVGG/oficina-lambda-auth/actions/workflows/ci.yml) | Formatação, go vet, testes unitários e de integração Go | “A função tem verificação própria, independente da aplicação.” |
| [Lambda: Terraform / deploy](https://github.com/15SOAT-JVGG/oficina-lambda-auth/actions/workflows/terraform.yml) | Compila autenticação e Authorizer, valida/plana/aplica Terraform e reconcilia o Gateway | “A publicação da função também atualiza os contratos usados pelo Gateway.” |
| [Lambda: validação pelo Gateway](https://github.com/15SOAT-JVGG/oficina-lambda-auth/actions/workflows/validate-authorizer-gateway.yml) | Exercita login CPF, JWT e negativas de autorização via API pública | “Validamos autorização no caminho real, com respostas permitidas e negadas.” |
| [Kubernetes: Terraform](https://github.com/15SOAT-JVGG/oficina-infra-k8s/actions/workflows/terraform.yml) | Valida Terraform e testes de convergência; aplica infraestrutura nas branches de ambiente | “O cluster e seus recursos de infraestrutura são versionados neste repositório.” |
| [Kubernetes: reconciliação Gateway](https://github.com/15SOAT-JVGG/oficina-infra-k8s/actions/workflows/reconcile.yml) | Consome contratos publicados e reconcilia as integrações do Gateway | “Este passo mantém aplicação e autenticação conectadas ao Gateway.” |
| [Kubernetes: observabilidade](https://github.com/15SOAT-JVGG/oficina-infra-k8s/actions/workflows/observability.yml) | Instala/reconcilia a stack de monitoramento e publica a rota privada do Grafana | “O monitoramento é provisionado separadamente da imagem da aplicação.” |
| [Kubernetes: dashboards](https://github.com/15SOAT-JVGG/oficina-infra-k8s/actions/workflows/publish-dashboards.yml) | Atualiza somente os ConfigMaps dos dois dashboards e verifica a configuração salva | “Podemos melhorar os painéis sem reinstalar a stack nem executar Terraform apply.” |
| [Banco: Terraform](https://github.com/15SOAT-JVGG/oficina-infra-db/actions/workflows/terraform.yml) | Formatação/validação, plano e apply do RDS e da rede do banco por ambiente | “O banco gerenciado tem infraestrutura e pipeline próprias. As migrations da aplicação são outro mecanismo.” |

### Exemplos prontos para abrir na gravação

- [PR aprovado com a massa exportável](https://github.com/15SOAT-JVGG/oficina-app/pull/87).
- [Deploy da aplicação aprovado com smokes](https://github.com/15SOAT-JVGG/oficina-app/actions/runs/41158248740).
- [Deploy da Lambda aprovado](https://github.com/15SOAT-JVGG/oficina-lambda-auth/actions/runs/40991742239).
- [Apply do banco aprovado](https://github.com/15SOAT-JVGG/oficina-infra-db/actions/runs/40980315346).
- [Seed aprovado desta massa](https://github.com/15SOAT-JVGG/oficina-app/actions/runs/41212663163).

Mostrar execução concluída e sua branch/commit. Não disparar apply de banco ou cluster
somente para preencher tempo de vídeo. Os exemplos são de homologação; não afirmar
execução comprovada de produção quando houver apenas configuração do gatilho.

## Action para demonstrar aumento de réplicas

[Abrir Homolog - seed and HPA simulation](https://github.com/15SOAT-JVGG/oficina-app/actions/workflows/homolog-simulation.yml).

1. Run workflow, branch main.
2. operation=load_only: a massa já está pronta; não precisa criar outro lote.
3. duration_seconds=180, concurrency=2. work_orders é ignorado nesse modo.
4. Abrir o [dashboard Infraestrutura](https://dcs5hfax0e.execute-api.us-east-1.amazonaws.com/observability/d/oficina-kubernetes)
   e acompanhar CPU, memória e réplicas desejadas/disponíveis. Depois esperar a recuperação.

Fala: “Esta action gera logins válidos com carga gradual. O HPA observa o consumo e decide
se precisa criar mais pods. Ao final, a carga para e acompanhamos a redução. Não estamos
alterando réplicas manualmente.”

O perfil leve tem limite global de quatro requisições/s. Aumentar pods não é garantido com
qualquer carga: depende da utilização e do estado inicial. Não elevar agressivamente os
valores para forçar uma cena. Se ocorrer 503 ou falha no orçamento de erros, interromper
a demonstração e consultar o resumo. Não apresentar a execução reprovada como sucesso.

### Como ler os painéis durante a apresentação

- Memória está em MB e CPU em millicores. Réplicas desejadas mostram a decisão do HPA;
  disponíveis indicam pods efetivamente prontos.
- A seção de logs começa recolhida. Abrir pela seta, ler horário/nível/mensagem e clicar
  na linha quando precisar dos campos técnicos. Explore mantém acesso à consulta original.
- Os histogramas HTTP foram corrigidos e a coleta foi validada. Se não houver tráfego
  recente, gerar poucas chamadas da collection e aguardar o intervalo de coleta; não
  chamar um p95 vazio de zero. Erros rejeitados no Gateway/Authorizer são outro salto e
  não devem ser confundidos com respostas 5xx emitidas pela aplicação.


## Evidências disponíveis ao concluir a gravação

- [Vídeo final, 13min29s](https://youtu.be/hgZPRw7hWeA).
- [Deploy completo e smokes](https://github.com/15SOAT-JVGG/oficina-app/actions/runs/41254012718).
- [Auditoria obrigatória de métricas, regras e correlação log/trace](https://github.com/15SOAT-JVGG/oficina-infra-k8s/actions/runs/41254775789).
- [Carga de 704 tentativas sem erro, HPA 2 -> 5 -> 2](https://github.com/15SOAT-JVGG/oficina-app/actions/runs/41250722643).

Ao explicar os novos painéis: “O volume diário vem do banco, e não da memória do pod.
As durações usam o histórico de etapas encerradas; cancelamentos são excluídos.
Falhas SMTP aparecem como falhas da integração e geram alerta sem desfazer a OS.”
O ambiente é encerrado depois da validação, conforme solicitado; os links de runtime dependem de AWS ativa.

Revalidação da versão final: [654 tentativas sem erro e HPA 2 -> 5 -> 2](https://github.com/15SOAT-JVGG/oficina-app/actions/runs/41254582460).
O alerta SMTP foi observado disparando e depois [resolvendo](https://github.com/15SOAT-JVGG/oficina-infra-k8s/actions/runs/41255043752), sem derrubar o ciclo da OS.
