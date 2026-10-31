# RFC-002 - PostgreSQL gerenciado e evolução de dados

Status: justificativa técnica da implementação existente, aberta à revisão da equipe.

## Decisão e critérios

Adotar PostgreSQL 16 em Amazon RDS. As operações do domínio requerem transações,
relacionamentos e agregações; a stack já utiliza Hibernate Reactive, JDBC/Flyway e pgx.
RDS atende ao requisito explícito de banco gerenciado. Ver [modelo e justificativa](../MODELO-DE-DADOS.md).

## Alternativas

MySQL gerenciado é funcionalmente possível, porém acrescenta migração de dialeto/driver e
não há evidência de ganho neste sistema. NoSQL não elimina a necessidade de consistência
entre OS, orçamento e estoque, e exigiria redesenho do modelo. Banco em container não
atende à intenção de serviço gerenciado nem transfere operação/backups à nuvem.

## Integridade e operação

Preservar UUIDs do domínio, decimal para dinheiro, unicidade onde mapeada, estados
canônicos e transações do caso de uso. O banco é privado, com transporte TLS. Backups
seguem Terraform de cada ambiente; Multi-AZ é desativado no Lab. Schema e credenciais
não devem ser colocados em artefatos públicos.

## Pontos em aberto

DDL ainda combina Flyway e schema-management=update. A baseline completa e a validação
exclusiva por migrations são uma evolução planejada. Índices devem ser justificados por
consulta/plano medido; esta revisão não fez acesso SQL. Definir métricas diárias e duração
por etapa a partir do histórico antes de afirmar conformidade integral de observabilidade.
