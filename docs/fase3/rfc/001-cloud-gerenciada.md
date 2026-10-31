# RFC-001 - AWS e serviços gerenciados

Status: justificativa técnica da implementação existente, aberta à revisão da equipe.

## Problema

O desafio exige Gateway, função serverless, Kubernetes escalável, banco gerenciado e IaC.
O Learner Lab limita IAM e oferece credenciais temporárias. A solução precisa ser demonstrável
sem esconder essas restrições nem criar dependência de acesso administrativo não disponível.

## Solução adotada

AWS API Gateway HTTP, Lambda Go, EKS, ECR, RDS PostgreSQL, S3 para state e CloudWatch.
Terraform provisiona recursos AWS; Helm instala observabilidade depois que o cluster está
acessível. Quatro repositórios mantêm fronteiras de entrega e workflows por ambiente.

## Alternativas e critérios

| Alternativa | Avaliação |
|---|---|
| EKS + RDS + Lambda | Alinha os requisitos e aproveita o Lab; exige gerir compatibilidade Kubernetes e limites IAM |
| Kubernetes autogerido + banco em VM | Aumenta operação e banco em VM não atende diretamente o requisito de banco gerenciado |
| Gateway/autenticação no pod | Possível tecnologicamente, mas mantém acoplamento de disponibilidade e não substitui a função serverless exigida |
| Outra nuvem | Viável pelo enunciado; exigiria reprovisionamento e credenciais fora do ambiente disponibilizado |

## Consequências

Roles preexistentes do Lab restringem privilégio fino. Homolog e produção compartilham EKS;
RDS é por ambiente. O ambiente não promete tolerância a falha de região/AZ. Custos dependem
principalmente de EKS, nós, RDS e dois NLBs internos; não foi efetuado cálculo de custo mensal.

Critérios de aceitação: apply revisado, workloads prontos, tráfego via Gateway, testes de
negação de acesso e evidência de monitoramento. Evolução comercial exige IAM dedicado,
isolamento e HA dimensionados por requisitos medidos.
