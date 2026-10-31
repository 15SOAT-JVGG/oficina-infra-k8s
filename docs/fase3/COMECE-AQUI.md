# Comece aqui - demonstração da Fase 3

## Acessos rápidos

| Acesso | Link |
|---|---|
| Swagger | [Abrir](https://dcs5hfax0e.execute-api.us-east-1.amazonaws.com/q/swagger-ui/) |
| Grafana | [Abrir](https://dcs5hfax0e.execute-api.us-east-1.amazonaws.com/observability/) |
| Dashboard de infraestrutura / HPA | [Abrir](https://dcs5hfax0e.execute-api.us-east-1.amazonaws.com/observability/d/oficina-kubernetes) |
| Action de seed automático | [Abrir](https://github.com/15SOAT-JVGG/oficina-app/actions/workflows/homolog-simulation.yml) |
| Seed anterior aprovado | [Abrir](https://github.com/15SOAT-JVGG/oficina-app/actions/runs/41158958643) |
| Deploy aprovado com smokes | [Abrir](https://github.com/15SOAT-JVGG/oficina-app/actions/runs/41158248740) |
| PR integrado com CI aprovado | [Abrir](https://github.com/15SOAT-JVGG/oficina-app/pull/86) |
| PDFs individuais | [Abrir](https://github.com/15SOAT-JVGG/oficina-infra-k8s/tree/main/output/pdf/separados) |
| Roteiro | [Abrir](https://github.com/15SOAT-JVGG/oficina-infra-k8s/blob/main/docs/fase3/ROTEIRO-VIDEO.md) |

Endpoints dependem do Learner Lab ativo. Grafana usa usuário admin e a senha configurada
para ele. A senha da API é APP_SEED_ADMIN_PASSWORD de homolog; são acessos separados.

## A massa já é preparada pelo seed

Não é necessário cadastrar cliente, veículo ou peça no Postman. Antes da demonstração,
o seed automático cria um cliente ativo com CPF gerado para teste, um veículo, uma peça
com estoque e seis OS, uma em cada estado. Os dados são sintéticos e o e-mail usa
example.invalid. O SMTP é capturado pelo sandbox do Mailtrap.

O seed aprovado exporta FIAP-Massa-Pronta.postman_environment.json no artifact da Action.
Esse ambiente contém o CPF e os IDs sintéticos prontos para uso. Senha e tokens ficam vazios.
O Summary mantém apenas contagens. O modo load_only não gera massa. Cada seed cria novo
lote e deixa os registros em homologação; não execute novamente só para abrir outra OS.

## A massa desta revisão já está pronta

Importar diretamente o [ambiente preenchido](postman/FIAP-Massa-Pronta.postman_environment.json)
e a [collection curta](postman/FIAP-Fase3.postman_collection.json).
[Dados detalhados da massa e execução aprovada](MASSA-PRONTA.md). Basta preencher a senha.
O passo de seed abaixo só é necessário para renovar a massa.

## Preparar uma vez ou renovar a massa

1. Abrir a Action de seed, Run workflow, branch main, operation=seed_only e work_orders=6.
   Os campos de duração/concorrência não são usados nesse modo. Aguardar conclusão verde.
2. No fim da página da execução, abrir Artifacts e baixar homolog-simulation-<run_id>.
   Importar o arquivo FIAP-Massa-Pronta.postman_environment.json no Postman.
3. Importar a [collection de demonstração](postman/FIAP-Fase3.postman_collection.json).
   Selecionar o ambiente Massa Pronta e preencher apenas adminPassword localmente.
4. O ambiente desta revisão já está publicado [nesta pasta](postman/). Se o Lab/banco for recriado, substituir pelo artifact de um novo seed.

O seed anterior aprovado, vinculado na tabela, não exportava o ambiente Postman.
A [execução nova aprovada](https://github.com/15SOAT-JVGG/oficina-app/actions/runs/41212663163) já exporta o ambiente.

## Executar na gravação - somente 12 requests

No Runner: uma iteração, Delay=6000ms, sem CSV, sem paralelismo. Ou enviar manualmente
em ordem, esperando seis segundos entre as operações de OS. Não é teste de carga.

| Request | Demonstração | Esperado |
|---|---|---|
| 01 | Login do funcionário, salva adminToken | 200 |
| 02 | Abre OS com cliente/veículo do seed, salva workOrderId | 201 / RECEIVED |
| 03 | Inicia diagnóstico | 200 / DIAGNOSIS |
| 04 | Gera orçamento usando a peça do seed, salva estimateId | 201 / WAITING_APPROVAL |
| 05 | Login por CPF da massa, salva customerToken | 200 |
| 06 | Cliente consulta suas OS | 200 |
| 07 | Mesma consulta sem token | 401 |
| 08 | Cliente tenta rota operacional | 403 |
| 09 | Cliente aprova o orçamento | 200 / IN_PROGRESS |
| 10 | Funcionário conclui por valor final 50 | 200 / COMPLETED |
| 11 | Registra entrega | 200 / DELIVERED |
| 12 | Consulta a OS e verifica estado final | 200 / DELIVERED |

A collection salva IDs/tokens automaticamente e envia Content-Type application/json nos
PATCH, inclusive sem corpo. Pode repetir o ciclo sem recriar a massa: cada iteração abre
uma nova OS e usa uma unidade da peça. O seed cria estoque de work_orders+10 (16 no lote
padrão de seis OS), mas parte é reservada/consumida pelas próprias OS do seed; não é estoque
infinito. Se esgotar, preparar outro lote pela Action.

Em falha inesperada, o Runner para. Não há retry automático de escrita: um 503 pode ter
ocorrido depois de persistir a operação. Conferir o resultado antes de repetir. Tokens
expirados são renovados repetindo o login; senha/tokens não são publicados no repositório.

## Swagger e Postman

Swagger é o catálogo para explorar os endpoints da aplicação com Try it out. A collection
é o caminho curto para a apresentação, sem cadastros manuais. O login CPF /v1/auth/customer
é da Lambda e pode não aparecer no OpenAPI da aplicação; está incluído na collection.
A collection não pretende conter todo CRUD. Sua validação estática não substitui uma
execução real pelo usuário com a senha local.

## Seed e carga são coisas diferentes

O padrão da Action é seed_only: prepara dados, sem carga de CPU. Para demonstrar HPA,
selecionar load_only separadamente, duração 180 segundos, concorrência 2, teto global de
quatro requisições/s. O workflow observa o HPA, sem forçar escala. O perfil leve ainda
precisa de validação de estabilidade. Summary e hpa.csv registram as evidências.

Já houve escala 2 -> 4 -> 2, mas a carga anterior teve oito 503 em 211 tentativas. Não
apresentar esse teste como aprovado. A investigação permanece aberta. Traces, métricas
HTTP/negócio e alertas específicos de OS continuam com pendências na matriz.

O PR 86 mostra checks aprovados e merge de uma mudança pequena na main; não é deploy.
Para demonstrar entrega automatizada, usar o run homolog aprovado da tabela.

O Portal pede vídeo de até 15 minutos e PDF único com links. Os documentos e diagramas
individuais ficam neste repositório e não dependem de ZIP.

## Manutenção da massa e acesso local

[Action de manutenção: senha e limpeza de lote](https://github.com/15SOAT-JVGG/oficina-app/actions/workflows/homolog-maintenance.yml).

- preview_seed é o padrão: informar o batch FIAP-DEMO-xxxxxxxxxxxx da página Massa Pronta.
  Mostra contagens e não apaga nada.
- delete_seed exige batch e confirmation com exatamente o mesmo valor. Apaga somente
  aquele lote e suas dependências, em transação. Não existe opção de limpar todas as massas.
- Cliente do teste Authorizer, estoque/veículo referenciado fora do lote e dados que não
  correspondam à massa sintética bloqueiam a exclusão. Falhas causam rollback.
- Após excluir o lote usado no ambiente Postman, executar seed_only e importar o ambiente
  do lote novo. Os IDs antigos deixam de funcionar. Exclusão não possui backup automático.
- rotate_admin aplica ao administrador existente a senha da secret APP_SEED_ADMIN_PASSWORD
  do Environment homolog e verifica o login. Trocar somente a secret não troca senha já
  cadastrada no banco; o seed inicial preserva usuários existentes.

O arquivo pessoal de acesso e o ambiente com senha preenchida ficam somente na máquina
local do operador, fora do Git. Os arquivos publicados continuam com senha e tokens vazios.
