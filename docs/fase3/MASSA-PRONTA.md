# Massa pronta - criada automaticamente

> **Ambiente encerrado:** a homologação foi validada e os recursos AWS foram removidos a pedido do responsável. Os links de API/Grafana e os IDs da massa são referências da demonstração. Veja o [registro de encerramento](ENCERRAMENTO.md); para repetir as chamadas, reimplante o ambiente e execute o seed novamente.


Seed aprovado em 31/10/2026, às 12h02 (America/Sao_Paulo).
[Execução e artifact](https://github.com/15SOAT-JVGG/oficina-app/actions/runs/41212663163).

A massa já existe em homologação. Não cadastrar cliente, veículo ou peça na gravação.
Importar a [collection](postman/FIAP-Fase3.postman_collection.json) e o
[ambiente preenchido](postman/FIAP-Massa-Pronta.postman_environment.json), selecionar o
ambiente no Postman e preencher apenas adminPassword localmente.

## Dados sintéticos disponíveis

| Campo | Valor |
|---|---|
| demoName | FIAP-DEMO-3dd67630cefa |
| demoCpf | 56723007158 |
| customerId | d8177e01-df1c-4903-b713-f92a78c6ba85 |
| vehicleId | ff8d6372-8db3-4c13-9492-eba80470a6fa |
| partId | dcfffbd1-b8a9-4fc5-aac6-8190ffdecbba |

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

Esta execução comprova o seed. A validação posterior de carga, indicadores de negócio,
traces e alertas está na [matriz atualizada](VALIDACAO.md).
