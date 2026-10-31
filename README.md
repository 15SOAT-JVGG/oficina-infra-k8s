[PDF de entrega ao Portal - preliminar](output/pdf/fiap-fase3-entrega-portal.pdf)

[Fase 3: comece aqui - Postman, massas, PDFs, seed e demonstração](docs/fase3/COMECE-AQUI.md)

# oficina-infra-k8s

Infraestrutura Kubernetes da **Oficina Mecânica** (FIAP 16SOAT — Tech Challenge Fase 3), provisionada com
Terraform: cluster **Amazon EKS** com node group escalável, **ECR** para a imagem da aplicação e **metrics-server**
para o HPA, e um **API Gateway** por ambiente como porta de entrada da API.

## Tecnologias

- Terraform `>= 1.10` e provider AWS `~> 5.80`
- Amazon EKS (Kubernetes 1.34), node group `t3.medium` (mín. 2, máx. 4)
- Amazon ECR com scan on push e política de retenção
- Add-on `metrics-server` do EKS (necessário para o HPA)
- Amazon API Gateway (HTTP API) com log de acesso em JSON no CloudWatch
- State remoto em S3 com lock nativo (`use_lockfile`)
- GitHub Actions para validação, plan e apply

## Branches e ambientes

| Branch | Função |
|---|---|
| `main` | Integração. Protegida: merge somente via Pull Request. Em PR roda `fmt`, `validate` e `plan`. |
| `homolog` | Deploy automático (`terraform apply`) da infraestrutura em homologação. |
| `production` | Deploy automático (`terraform apply`) da infraestrutura em produção. |

### Um cluster, dois ambientes

Para reduzir custo no Learner Lab (cada cluster EKS cobra por hora), existe **um único cluster** compartilhado.
Homologação e produção são isolados por **namespaces** (`homolog` e `production`), criados pelos manifests do
repositório `oficina-app`, e por **bancos RDS separados** (`oficina-infra-db`). Por isso este repositório tem um
único state (`oficina-infra-k8s/terraform.tfstate`) e os pushes em `homolog` e `production` aplicam a mesma
configuração: a promoção entre branches funciona como esteira de aprovação da mudança de infraestrutura.

## Recursos criados

| Recurso | Descrição |
|---|---|
| `aws_eks_cluster` | Cluster `oficina`, na VPC padrão (a mesma do RDS), role `LabRole`. |
| `aws_eks_node_group` | Nós `t3.medium`, mínimo 2 e máximo 4. |
| `aws_eks_addon` (metrics-server) | Métricas de CPU/memória para o HPA. |
| `aws_ecr_repository` | `oficina-app`, mantém as 15 imagens mais recentes. |
| `aws_apigatewayv2_api` | `oficina-homolog` e `oficina-production`: HTTP API, uma por ambiente. |
| `aws_apigatewayv2_stage` | Estágio `$default` com auto deploy, throttling e log de acesso em JSON. |
| `aws_cloudwatch_log_group` | `/aws/apigateway/oficina-<ambiente>`, retenção de 7 dias. |
| `aws_apigatewayv2_integration` + rotas | Proxy HTTP para o Service, com rota curinga protegida e exceções públicas enumeradas por método e caminho. |
| `aws_apigatewayv2_authorizer` + `aws_lambda_permission` | Authorizer Lambda `REQUEST` (payload 2.0, resposta simples, sem cache) e permissão de invocação por ambiente. |

## API Gateway

É a porta de entrada pública da API. O cliente chama o gateway, e as rotas públicas seguem sem identidade enquanto o restante passa pelo Lambda Authorizer antes do encaminhamento ao cluster:

- `POST /v1/auth/customer` vai para a Lambda de autenticação por CPF, que emite o JWT. A rota é criada
  pelo repositório `oficina-lambda-auth`, que usa o id do gateway do seu ambiente (output `api_gateway_ids`).
- Sem Authorizer: `POST /v1/auth/login`, `POST /v1/worker/login`, links assinados de acompanhamento e decisão de orçamento e endpoints de health existentes.
- Com Authorizer: `ANY /` e `ANY /{proxy+}`. O Quarkus continua aplicando RBAC e isolamento das OS do cliente.
- OpenAPI e Swagger ficam privados por padrão. `public_api_docs_environments` permite habilitá-los apenas nos ambientes explicitamente escolhidos, usando caminhos listados no Terraform.
- O proxy define `overwrite:path = $request.path` para preservar o caminho completo; query string, corpo e headers seguem pela integração HTTP proxy.
- Os access logs usam `routeKey` (com parâmetros de rota mascarados) e não registram `$context.path`, que incluiria tokens assinados de acompanhamento ou orçamento.

O endereço do ELB e o ARN do Authorizer não são fixados no código. Os workflows consumidores publicam contratos sem segredos no bucket S3 usado pelo backend Terraform:

```text
oficina/config/v1/<homolog|production>/upstream.json
oficina/config/v1/<homolog|production>/authorizer.json
```

O contrato `upstream.json` inclui `contract_version`, `account_id`, `region`, `environment`, `cluster_name`, `upstream_url` e `source_sha`. `authorizer.json` inclui os mesmos campos de contexto, `lambda_arn` e `source_sha`. Para o ambiente solicitado, os dois contratos são obrigatórios e o SHA do serviço que iniciou a chamada precisa coincidir. O par do outro ambiente é opcional somente quando o state confirma que ainda não há recursos de roteamento provisionados nele; se já houver recursos, os dois contratos são obrigatórios. Um par incompleto ou inválido interrompe o workflow. Recursos de rota, integração e Authorizer existentes também têm `prevent_destroy`, como proteção contra perda de state ou contrato.

### Bootstrap e promoção entre ambientes

1. Preserve o state existente e configure bucket, region e credenciais do Learner Lab nos GitHub Environments. Não remova recursos do state para contornar uma validação de contrato.
2. Publique o Authorizer de homologação pela pipeline Lambda. Se o upstream ainda não existir, publique o contrato de Authorizer e deixe a integração marcada como pendente; não chame a reconciliação ainda.
3. Implante a aplicação em homologação. Depois de readiness, publique `upstream.json`; com os dois contratos disponíveis, chame `reconcile.yml` para homologação.
4. Produção pode permanecer sem contratos enquanto não tiver rotas no state. Promova banco, Lambda e aplicação para produção; a reconciliação de produção exige os dois contratos de produção.
5. Se um ambiente já tiver qualquer recurso de roteamento no state, ausência do par de contratos desse ambiente bloqueia também as execuções do outro ambiente. Isso preserva o mapa completo sem presumir valores antigos.

O workflow lê `terraform state list` antes de montar os mapas. Se o state mudar entre essa leitura e o plano, `prevent_destroy` bloqueia qualquer tentativa de remover Authorizer, integração ou rota protegida. O plano de reconciliação segue limitado aos recursos de roteamento do ambiente solicitado.

O endereço do Service é um ELB criado pelo Kubernetes, não pelo Terraform. A aplicação descobre o
hostname após readiness e publica `upstream.json`; não mantenha cópias desse hostname no repositório.
Para conferência manual:

```shell
kubectl get svc oficina-mecanica -n homolog -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'
```

As URLs públicas saem dos outputs `api_gateway_urls`.

## Pré-requisitos

Os mesmos do `oficina-infra-db`:

- Bucket S3 do state e variável `TF_STATE_BUCKET`; variável `AWS_REGION`.
- Secrets `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` e `AWS_SESSION_TOKEN` (Learner Lab, expiram em ~4h).

## Execução local

```shell
export AWS_ACCESS_KEY_ID=... AWS_SECRET_ACCESS_KEY=... AWS_SESSION_TOKEN=...

terraform init \
  -backend-config="bucket=<bucket>" \
  -backend-config="key=oficina-infra-k8s/terraform.tfstate" \
  -backend-config="region=us-east-1"
terraform plan
```

Depois do apply, configure o `kubectl`:

```shell
aws eks update-kubeconfig --name oficina --region us-east-1
kubectl get nodes
kubectl top nodes
```

## Pipelines

`.github/workflows/terraform.yml`:

- **Pull Request**: `terraform fmt -check` e `validate`, sem credenciais AWS ou state remoto.
- **Push ou execução manual em `homolog`/`production`**: lê o state, valida os contratos exigidos para os ambientes já provisionados, cria um plano salvo e aplica esse plano no state compartilhado. O workflow manual serve para recuperação após renovar as credenciais do Learner Lab.
- `.github/workflows/reconcile.yml`: workflow reutilizável chamado pelos repositórios da aplicação e da Lambda. Lê os contratos obrigatórios do ambiente solicitado e preserva o par de outro ambiente quando já houver recursos no state; usa o lock S3 e bloqueia qualquer plano que altere EKS, ECR ou roteamento de ambiente não solicitado.

O bucket `TF_STATE_BUCKET` precisa manter acesso restrito, criptografia e versionamento. Ele contém o state e os contratos `oficina/config/v1/`; os contratos não contêm secrets. Planos e state não são publicados como artifact ou summary. A concorrência do GitHub serializa este repositório, e o lock S3 coordena as execuções que vêm de outros repositórios.

A criação do cluster leva cerca de 15 minutos.

## Próximos passos

- `oficina-app`: Dockerfile, manifests (Deployment, Service `LoadBalancer` com NLB, HPA) e pipeline de push no ECR e deploy.
- `oficina-lambda-auth`: Terraform e pipeline da Lambda, registrando `POST /v1/auth/customer` e publicando o contrato do Authorizer.
- Decidir com o time se o cluster passa a ser privado (Ingress, ou NLB interno com VPC Link) em vez de expor o ELB.
