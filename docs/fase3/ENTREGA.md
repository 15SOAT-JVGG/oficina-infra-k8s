# Entrega no Portal - preencher o vídeo antes do envio

[PDF único de entrega ao Portal (versão preliminar)](../../output/pdf/fiap-fase3-entrega-portal.pdf).

A fonte editável é [entrega-portal.json](entrega-portal.json); para gerar novamente:
`python3 docs/fase3/gerar-entrega-portal.py`. O PDF continua preliminar enquanto faltar
vídeo, confirmação do avaliador ou conclusão técnica. Vídeo deve ser YouTube/Vimeo
público ou não listado, com duração máxima de 900 segundos (15 minutos).

O dossiê técnico é material de consulta; o arquivo acima é o documento curto de links
para a instituição. O enunciado não exige incorporar todos os diagramas no PDF do Portal,
pois pede links das documentações. Os diagramas e textos completos permanecem nos repositórios.

**Estado: preparação. Ainda não é uma submissão final.** O usuário confirmou que gravará o
vídeo depois de concluir os requisitos técnicos. Não há link de vídeo atual da Fase 3.

## Repositórios

1. [oficina-lambda-auth](https://github.com/15SOAT-JVGG/oficina-lambda-auth)
2. [oficina-infra-k8s](https://github.com/15SOAT-JVGG/oficina-infra-k8s)
3. [oficina-infra-db](https://github.com/15SOAT-JVGG/oficina-infra-db)
4. [oficina-app](https://github.com/15SOAT-JVGG/oficina-app)

## Documentação

- Índice: [Abrir](https://github.com/15SOAT-JVGG/oficina-infra-k8s/tree/main/docs/fase3)
- Componentes, sequências, ER, RFCs, ADRs e validação: arquivos vinculados no índice.
- Swagger: [Abrir](https://dcs5hfax0e.execute-api.us-east-1.amazonaws.com/q/swagger-ui/)
- OpenAPI: [Abrir](https://dcs5hfax0e.execute-api.us-east-1.amazonaws.com/q/openapi?format=json)
- Grafana: [Abrir](https://dcs5hfax0e.execute-api.us-east-1.amazonaws.com/observability/)

Os links de homologação dependem da sessão/recursos do Learner Lab e devem ser conferidos
antes da entrega. Login do Grafana usa admin e secret protegido; a senha não integra o PDF.

## Execução guiada e evidências

- Guia detalhado de Postman, massas e links: [COMECE-AQUI.md](COMECE-AQUI.md).
- Action de seed: [Abrir](https://github.com/15SOAT-JVGG/oficina-app/actions/workflows/homolog-simulation.yml)
- PR integrado com CI aprovado: [Abrir](https://github.com/15SOAT-JVGG/oficina-app/pull/86)
- Deploy homolog aprovado: [Abrir](https://github.com/15SOAT-JVGG/oficina-app/actions/runs/41158248740)

## Acesso do avaliador

A consulta ao GitHub confirmou `soat-architecture` com acesso aos quatro repositórios em
31/10/2026 (BRT), reconfirmada nesta preparação com resposta 204 nos quatro.
Reconfirmar esse acesso antes de enviar o PDF no Portal do Aluno.

## Pendências finais

- Vídeo atual (YouTube/Vimeo, público ou não listado, até 15 minutos): **pendente de gravação pelo usuário**.
- Fechar pendências técnicas registradas na matriz de validação.
- Completar links dos READMEs e promover/documentar a revisão nos quatro repositórios.
- Incluir URL e duração do vídeo na fonte editável e gerar a revisão final do PDF único.

O dossiê arquitetural desta revisão pode apoiar a apresentação, mas não substitui o PDF
final enquanto o vídeo e as pendências de conformidade estiverem em aberto.
