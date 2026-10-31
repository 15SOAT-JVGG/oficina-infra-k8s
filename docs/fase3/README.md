# Fase 3 - documentação da Oficina

Pacote arquitetural e roteiro de homologação. Revisão: 30/10/2026 (BRT).
O estado descrito é o ambiente acadêmico implantado. A matriz de validação diferencia
implementação, evidência observada e pendências; documentação não substitui um teste operacional.

## Leitura e apresentação

1. [Arquitetura, componentes e fronteiras](ARQUITETURA.md).
2. [Sequências de autenticação e abertura de OS](SEQUENCIAS.md).
3. [Modelo relacional, justificativa e evolução](MODELO-DE-DADOS.md).
4. [Matriz dos requisitos e evidências](VALIDACAO.md).
5. [Roteiro do vídeo de até 15 minutos](ROTEIRO-VIDEO.md).
6. [Folha de entrega e links](ENTREGA.md).

## Decisões

| Documento | Tema |
|---|---|
| [RFC-001](rfc/001-cloud-gerenciada.md) | AWS, EKS e serviços gerenciados no Learner Lab |
| [RFC-002](rfc/002-postgresql.md) | Escolha formal do PostgreSQL e consistência |
| [RFC-003](rfc/003-autenticacao.md) | CPF, JWT RS256, Gateway e RBAC |
| [ADR-001](adr/001-comunicacao-e-fronteiras.md) | HTTP síncrono e fronteiras de acesso |
| [ADR-002](adr/002-hpa.md) | HPA e diferença entre pods e nós |
| [ADR-003](adr/003-observabilidade-no-lab.md) | Stack compartilhada, dois dashboards e armazenamento efêmero |

Os RFCs formalizam a justificativa da solução existente e registram os pontos em aberto.
Os ADRs documentam decisões materializadas no código; não simulam aprovação histórica da equipe.
Os ADRs existentes da aplicação continuam válidos nos respectivos escopos.

## Fontes e propriedade

- [Aplicação](https://github.com/15SOAT-JVGG/oficina-app): Quarkus, domínio, REST, migrations e manifests da aplicação.
- [Autenticação](https://github.com/15SOAT-JVGG/oficina-lambda-auth): funções Go e Terraform correspondente.
- [Kubernetes](https://github.com/15SOAT-JVGG/oficina-infra-k8s): EKS, Gateway, VPC Link e observabilidade.
- [Banco](https://github.com/15SOAT-JVGG/oficina-infra-db): RDS e controles de rede do banco.

Diagramas Mermaid estão versionados em `diagramas/*.mmd`; as imagens SVG/PNG permitem
apresentação fora do GitHub. O modelo foi confrontado com entidades/migrations, sem consultar
tabelas nem dados de clientes. Nenhuma credencial ou dado de cliente integra este pacote.

## Dossiê para leitura offline

[PDF técnico desta revisão](../../output/pdf/fiap-fase3-dossie-tecnico.pdf).
Os textos usam A4; os quatro diagramas usam páginas A3 para preservar a legibilidade.
O PDF é um dossiê pré-entrega: o vídeo e as lacunas técnicas continuam pendentes.

Para reproduzir a partir da raiz do repositório, usar Python com Pillow/ReportLab e Graphviz:
`python3 docs/fase3/gerar-diagramas.py` e `python3 docs/fase3/gerar-dossie.py`.

## Arquivos separados

Os PDFs individuais ficam em `output/pdf/separados/`, gerados por
`python3 docs/fase3/gerar-separados.py`. Incluem arquitetura, sequências, modelo de dados,
cada RFC/ADR, matriz, roteiro simples e folha de entrega. Diagramas PNG/SVG e fontes Mermaid
continuam em `docs/fase3/diagramas/`. O pacote ZIP reúne os PDFs e as fontes editáveis.
O enunciado continua exigindo vídeo e PDF único de links para o Portal.
