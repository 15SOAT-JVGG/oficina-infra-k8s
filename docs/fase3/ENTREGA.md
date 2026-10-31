# Entrega no Portal - vídeo incluído

[PDF único de entrega ao Portal (versão preliminar)](../../output/pdf/fiap-fase3-entrega-portal.pdf).

Fonte editável: [entrega-portal.json](entrega-portal.json). Para gerar novamente:
`python3 docs/fase3/gerar-entrega-portal.py`. O arquivo do Portal reúne os links;
o dossiê técnico e os PDFs separados são materiais de consulta.

**Estado: vídeo incluído; revisão técnica ainda pendente.**

Vídeo: [FIAP - 16SOAT - Demonstração Fase 3](https://youtu.be/hgZPRw7hWeA).
Duração conferida nos metadados do YouTube: **13min29s (809 segundos)**. A consulta sem
login retornou HTTP 200 e playabilityStatus=OK em 31/10/2026. Isso confirma acesso e duração,
sem substituir revisão do conteúdo nem comprovar os requisitos técnicos pendentes.

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

- Vídeo atual: **incluído**, 13min29s; conferir novamente o acesso antes do envio.
- Fechar pendências técnicas registradas na matriz de validação.
- Completar links dos READMEs e promover/documentar a revisão nos quatro repositórios.
- Conferir a revisão técnica e gerar a versão de envio após fechar as pendências da matriz.

O dossiê arquitetural desta revisão pode apoiar a apresentação, mas não substitui o PDF
final enquanto as pendências de conformidade estiverem em aberto. O vídeo já está incluído.
