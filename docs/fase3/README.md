# Fase 3 - documentação da Oficina

> **Ambiente encerrado:** a homologação foi validada e os recursos AWS foram removidos a pedido do responsável. Os links de API/Grafana e os IDs da massa são referências da demonstração. Veja o [registro de encerramento](ENCERRAMENTO.md); para repetir as chamadas, reimplante o ambiente e execute o seed novamente.


Pacote arquitetural e roteiro de homologação. Revisão: 31/10/2026 (BRT).
O estado descrito é o ambiente acadêmico implantado. A matriz de validação diferencia
implementação, evidência observada e pendências; documentação não substitui um teste operacional.

## PDF para enviar à instituição

[Documento único de entrega ao Portal](../../output/pdf/fiap-fase3-entrega-portal.pdf):
versão para submissão, com os quatro repositórios, documentação, confirmação do
avaliador e vídeo de 13min29s. A [matriz de validação](VALIDACAO.md) apresenta os testes e limites observados.
[Como atualizar a entrega](ENTREGA.md).

## Acesso rápido

[Comece aqui: Postman, massas, seed, Grafana, PR e deploy](COMECE-AQUI.md).

[Baixar PDFs individuais](../../output/pdf/separados/) e consultar diagramas em [diagramas](diagramas/). Não é necessário baixar ZIP.

[Massa já cadastrada e ambiente Postman](MASSA-PRONTA.md).

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
O dossiê complementa o PDF único de links exigido para o Portal; o vídeo já está incluído na entrega.

Para reproduzir a partir da raiz do repositório, usar Python com Pillow/ReportLab e Graphviz:
`python3 docs/fase3/gerar-diagramas.py` e `python3 docs/fase3/gerar-dossie.py`.

## Arquivos separados

Os PDFs individuais ficam em `output/pdf/separados/`, gerados por
`python3 docs/fase3/gerar-separados.py`. Incluem arquitetura, sequências, modelo de dados,
cada RFC/ADR, matriz, roteiro simples e folha de entrega. Diagramas PNG/SVG e fontes Mermaid
continuam em `docs/fase3/diagramas/`. Os PDFs e fontes editáveis estão publicados individualmente neste repositório.
O enunciado continua exigindo vídeo e PDF único de links para o Portal.
