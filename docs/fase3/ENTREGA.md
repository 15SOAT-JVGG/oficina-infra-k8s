# Entrega no Portal - Fase 3

[PDF único para enviar à instituição](../../output/pdf/fiap-fase3-entrega-portal.pdf).

O PDF reúne os links exigidos pelo enunciado: quatro repositórios, vídeo de até 15 minutos,
documentação arquitetural e confirmação do avaliador. Os documentos separados e o dossiê
continuam disponíveis para consulta; não é necessário anexar um ZIP.

## Vídeo

[FIAP - 16SOAT - Demonstração Fase 3](https://youtu.be/hgZPRw7hWeA), **13min29s**.
Acesso e duração conferidos nos metadados do YouTube. O autor confirmou que mostrou logs
e traces em execução. A [matriz](VALIDACAO.md) separa essa confirmação da evidência técnica dos workflows.

## Repositórios

1. [oficina-lambda-auth](https://github.com/15SOAT-JVGG/oficina-lambda-auth)
2. [oficina-infra-k8s](https://github.com/15SOAT-JVGG/oficina-infra-k8s)
3. [oficina-infra-db](https://github.com/15SOAT-JVGG/oficina-infra-db)
4. [oficina-app](https://github.com/15SOAT-JVGG/oficina-app)

## Acessos e comprovação

- [Documentos, diagramas, RFCs e ADRs](README.md).
- [Validação final e limites do Lab](VALIDACAO.md).
- [Roteiro com documentos, pipelines e demonstração de réplicas](ROTEIRO-VIDEO.md).
- [Coleção de 12 requisições e massas prontas](COMECE-AQUI.md).
- [PR de implementação com CI aprovado](https://github.com/15SOAT-JVGG/oficina-app/pull/90).
- [Deploy completo aprovado](https://github.com/15SOAT-JVGG/oficina-app/actions/runs/41254012718).
- [Auditoria final de observabilidade](https://github.com/15SOAT-JVGG/oficina-infra-k8s/actions/runs/41254775789).
- [Seed/carga/HPA](https://github.com/15SOAT-JVGG/oficina-app/actions/workflows/homolog-simulation.yml).

`soat-architecture` foi reconfirmado nos quatro repositórios via API do GitHub.
A homologação foi validada antes do encerramento do Learner Lab solicitado pelo responsável.
Swagger e Grafana dependem de infraestrutura ativa; vídeo, código, documentos e evidências permanecem no GitHub/YouTube.

## Regeneração

Editar [entrega-portal.json](entrega-portal.json) e executar
`python3 docs/fase3/gerar-entrega-portal.py` com ReportLab instalado.
Não incluir credenciais, tokens ou senhas no PDF.


## Ambiente encerrado

O destroy foi concluído após os testes. [Comprovação e detalhes](ENCERRAMENTO.md).
[Finalização aprovada](https://github.com/15SOAT-JVGG/oficina-infra-k8s/actions/runs/41258553104).
API, Swagger e Grafana estão desligados; enviar o PDF, o vídeo e os links dos repositórios conforme o enunciado.
