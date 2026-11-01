# Encerramento do Learner Lab

A Fase 3 foi validada e os documentos foram publicados antes da remoção da infraestrutura,
na ordem solicitada pelo responsável. O vídeo e os quatro repositórios permanecem disponíveis.

## Evidências

- [Deploy e smokes finais](https://github.com/15SOAT-JVGG/oficina-app/actions/runs/41254012718).
- [Carga final: 654 tentativas, zero erros e HPA 2 -> 5 -> 2](https://github.com/15SOAT-JVGG/oficina-app/actions/runs/41254582460).
- [Métricas de negócio, alertas e correlação real de logs/traces](https://github.com/15SOAT-JVGG/oficina-infra-k8s/actions/runs/41254775789).
- [Alerta SMTP resolvido e auditoria novamente aprovada](https://github.com/15SOAT-JVGG/oficina-infra-k8s/actions/runs/41255043752).
- [Workflow de encerramento](https://github.com/15SOAT-JVGG/oficina-infra-k8s/actions/runs/41255474426).

## Estado após o encerramento

As três stacks ficaram com **zero recursos gerenciados**. A AWS confirmou ausência de EKS,
nós EC2, RDS, Lambdas, API Gateways, ECR e volumes do projeto. Balanceadores,
interfaces e security groups do projeto também foram removidos.

A limpeza do bucket dedicado de state e contratos terminou na
[finalização aprovada](https://github.com/15SOAT-JVGG/oficina-infra-k8s/actions/runs/41258553104).
A execução principal terminou com erro de interpretação da resposta vazia do S3 após
concluir a remoção dos recursos; o [PR 49](https://github.com/15SOAT-JVGG/oficina-infra-k8s/pull/49)
corrigiu esse tratamento e permitiu finalizar somente o bucket, com nova verificação independente da AWS.

Encerramento confirmado em **31/10/2026 (BRT)**. API, Swagger e Grafana estão desligados.

Os endpoints do API Gateway, Swagger e Grafana pertencem à demonstração gravada e deixam de
funcionar após a remoção. Os identificadores da massa são históricos: será necessário
reimplantar o ambiente e executar o seed novamente para repetir as chamadas.

A remoção é limitada aos recursos FIAP identificados nos estados e aos recursos derivados
do cluster. A VPC padrão, sub-redes padrão e roles compartilhadas do AWS Academy são preservadas.
Não foram incluídos dados, senhas, tokens, credenciais ou valores de CPF neste registro.

## Entrega à instituição

Enviar o [PDF único de links](../../output/pdf/fiap-fase3-entrega-portal.pdf).
O [vídeo de 13min29s](https://youtu.be/hgZPRw7hWeA), o código e a documentação
permitem consultar a entrega sem manter o Learner Lab ligado.
