# Massa pronta - criada automaticamente

Seed aprovado em 31/10/2026, às 11h30 (America/Sao_Paulo).
[Execução e artifact](https://github.com/15SOAT-JVGG/oficina-app/actions/runs/41210273412).

A massa já existe em homologação. Não cadastrar cliente, veículo ou peça na gravação.
Importar a [collection](postman/FIAP-Fase3.postman_collection.json) e o
[ambiente preenchido](postman/FIAP-Massa-Pronta.postman_environment.json), selecionar o
ambiente no Postman e preencher apenas adminPassword localmente.

## Dados sintéticos disponíveis

| Campo | Valor |
|---|---|
| demoName | FIAP-DEMO-07a312f83b62 |
| demoCpf | 29440648279 |
| customerId | c17c30d2-1ef3-43a1-8193-f5b0028b9286 |
| vehicleId | 1044b85a-b517-4eaa-91a9-0160c9bbba87 |
| partId | 38d2e5ef-c372-4123-8849-74142def6411 |

Esses valores pertencem somente ao lote de demonstração criado pelo seed. O CPF foi gerado
para teste e o e-mail usa example.invalid. IDs são referências para a collection, não segredos.
Nenhuma senha, token JWT ou credencial AWS foi incluída.

## O que o seed confirmou

- Um cliente, um veículo, uma peça e seis OS criados.
- Uma OS em cada estado: RECEIVED, DIAGNOSIS, WAITING_APPROVAL, IN_PROGRESS, COMPLETED e DELIVERED.
- Vinte respostas HTTP 200 e treze HTTP 201; nenhum 503 nesta execução.
- O estoque inicial da peça foi 16; as OS do seed já reservam/consomem parte dele.

As seis OS existentes servem para explorar os estados. A collection curta abre outra OS
com os mesmos cadastros e percorre todo o ciclo, salvando workOrderId e estimateId.
Não é necessário copiar os IDs manualmente: já estão no ambiente importável.
Se o banco/Lab for recriado ou a massa removida, rodar seed_only novamente e importar
o ambiente do novo artifact. Os registros não são apagados automaticamente.

## Acessos de demonstração

API: adminUsername=admin; adminPassword deve receber a senha APP_SEED_ADMIN_PASSWORD
do ambiente homolog no seu Postman. O login do cliente usa demoCpf e recebe um JWT
automaticamente. Para Grafana, usuário admin e sua senha própria.

Esta execução comprova o seed. Não comprova que os 503 de carga foram resolvidos nem
que os indicadores de negócio/traces/alertas pendentes já estejam implementados.
