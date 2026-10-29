# Operação e recuperação — AWS Academy Learner Lab

Registro da recuperação de homologação realizada em 29/10/2026. Os identificadores e estados abaixo são evidências dessa sessão, não uma garantia do estado atual. Nunca registre valores de credenciais, tokens, senhas ou conteúdo do Terraform state neste documento.

## Arquitetura

| Projeto | Responsabilidade | State |
| --- | --- | --- |
| `oficina-infra-k8s` | EKS compartilhado, node group, ECR, API Gateway e rotas | `oficina-infra-k8s/terraform.tfstate` |
| `oficina-infra-db` | PostgreSQL RDS por ambiente | `oficina-infra-db/<ambiente>/terraform.tfstate` |
| `oficina-lambda-auth` | Autenticação por CPF e authorizer, com integração ao gateway | `oficina-lambda-auth/<ambiente>/terraform.tfstate` |
| `oficina-app` | Build/testes, imagem ECR, deploy Kubernetes, contrato de upstream e smoke test | consome os states do banco e EKS |

O cluster e seu state são compartilhados entre ambientes; os bancos, namespaces, rotas e secrets são separados. O fluxo validado foi **homologação**; isso não comprova produção.

## Diagnóstico e correção de 29/10/2026

1. A AWS mostrou o EKS ativo e as EC2 ligadas, mas `kubectl get nodes` não retornava nós. O `nodeadm-config` das AMIs AL2023 tentou `ec2:DescribeInstances` para descobrir o DNS privado e recebeu uma negação explícita da SCP do Lab na sessão da `LabRole`.
2. A correção incorporada ao Terraform usa `scripts/node-user-data.mime`: `InstanceIdNodeName` evita a chamada bloqueada durante a configuração inicial. No `cloud-init`, o DNS privado é lido de IMDSv2 e passado ao kubelet via configuração `nodeadm`, preservando a entrada de acesso `EC2_LINUX` que espera `system:node:{{EC2PrivateDNSName}}`. Isso não altera a SCP nem amplia a `LabRole`.
3. Foi criado um grupo de teste com um nó, que ficou `Ready` com CNI, CoreDNS e metrics-server operacionais. Depois, o Terraform criou o grupo definitivo com dois nós antes de remover o grupo antigo. O grupo e o launch template temporários foram removidos. A solução depende do comportamento e da ordem dos serviços da AMI; valide novamente ao alterar AMI ou Kubernetes.
4. O RDS de homologação estava `available`; as Lambdas e os API Gateways existiam. Foi criado no novo cluster o acesso `github-deployer` no namespace `homolog`, com token persistente no secret `KUBE_CONFIG_B64` do GitHub Environment da aplicação, após autorização do usuário.
5. As credenciais temporárias AWS foram atualizadas nos Environments `homolog` dos quatro repositórios. A variável `TF_STATE_BUCKET` do repositório foi corrigida também nos consumidores de workflow reutilizável, que não recebem automaticamente o contexto do Environment chamador na expressão de entrada.
6. A permissão do API Gateway para a Lambda Authorizer foi corrigida para suportar versões: statement distinto por ARN, `create_before_destroy` e `qualifier` separado do ARN não qualificado no provider. As referências do workflow reutilizável na aplicação e na Lambda foram atualizadas para o mesmo SHA de infraestrutura em `uses` e `infra_ref`.
7. O Terraform de infraestrutura, a pipeline da Lambda e o deploy da aplicação passaram. O smoke test pelo gateway passou; readiness e liveness retornaram HTTP 200. A imagem em execução correspondia ao SHA da pipeline. Esses resultados foram observados naquela sessão e devem ser repetidos após qualquer reativação.

Referências de execução: [infraestrutura](https://github.com/15SOAT-JVGG/oficina-infra-k8s/actions/runs/40878346906), [Lambda](https://github.com/15SOAT-JVGG/oficina-lambda-auth/actions/runs/40878783845) e [aplicação](https://github.com/15SOAT-JVGG/oficina-app/actions/runs/40879423018).

## Iniciar ou retomar uma sessão

1. Inicie o Lab na AWS Academy e aguarde o estado **Ready**. Confira conta, região, tempo restante e orçamento no painel. Os recursos podem persistir, parar ou precisar de recuperação conforme o encerramento anterior; verifique em vez de pressupor.
2. Atualize os três secrets `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` e `AWS_SESSION_TOKEN` no Environment `homolog` de **cada** repositório: `oficina-infra-k8s`, `oficina-infra-db`, `oficina-lambda-auth` e `oficina-app`. Use GitHub Environments/secrets; não coloque credenciais em variáveis públicas, commits, logs, mensagens ou artefatos. As credenciais de sessão expiram: confirme a validade antes de uma execução longa.
3. Confirme `AWS_REGION` e `TF_STATE_BUCKET` nos Environments e, onde o workflow reutilizável recebe `vars.TF_STATE_BUCKET` fora de um job vinculado a Environment, também no nível do repositório. Em 29/10 foram usados `us-east-1` e `fiap16soat-oficina-tfstate-630266487412`; confirme a conta atual antes de reutilizar o bucket.
4. Execute/valide na ordem: banco e infraestrutura compartilhada; Lambda e authorizer; aplicação e contrato de upstream; reconciliação do gateway; smoke test. Quando o state já existe, não recrie recursos sem examinar o plano. Se um contrato estiver incompleto ou o SHA divergir, corrija a origem ou conclua o deploy que o publica; não remova rotas ou state para forçar o apply.
5. Se o cluster foi **recriado**, o kubeconfig da ServiceAccount anterior não serve para o novo endpoint/CA. Com acesso administrativo, utilize o script versionado `oficina-app/infra/scripts/create-deploy-kubeconfig.sh homolog` e atualize o secret `KUBE_CONFIG_B64` do Environment. O token desse script não expira automaticamente; restrinja o acesso ao secret e revogue-o quando não for mais necessário. Se apenas a credencial AWS girou e o cluster permaneceu o mesmo, não é necessário recriar esse acesso por padrão.

## Verificação operacional

```shell
aws sts get-caller-identity
aws eks update-kubeconfig --name oficina --region us-east-1
kubectl get nodes -o wide
kubectl get pods -A
kubectl get deploy,svc,hpa -n homolog
kubectl rollout status deployment/oficina-mecanica -n homolog --timeout=10m
kubectl top nodes
```

Consulte os outputs do Terraform para o gateway atual; não trate uma URL de uma sessão como permanente. Confira os endpoints de health e o smoke test da pipeline, o digest ou SHA da imagem aplicada, o RDS e o estado das funções Lambda. Uma pipeline verde, isoladamente, não prova que os serviços estão prontos.

## Concorrência, recuperação e limites

A concorrência do GitHub Actions é limitada ao repositório chamador; grupos com o mesmo nome em repositórios diferentes **não** constituem um mutex global. O backend S3 protege cada operação Terraform com lock, mas o lock é liberado entre `plan` e `apply`: o estado ou contratos podem mudar nesse intervalo. A rotina de convergência deste repositório aguarda lock por até 15 minutos por operação, valida os contratos, rejeita mudanças fora do gateway solicitado e recalcula o plano em caso de plano desatualizado ou lock indisponível, com até quatro tentativas. Ela também volta a conferir os contratos antes e depois do apply. Isso reduz falhas e detecta mudanças, mas não cria uma transação atômica entre contratos S3 e Terraform; use execuções sequenciais em mudanças coordenadas e investigue falhas persistentes.

Não remova um lock, edite o state ou execute `destroy` para desbloquear uma pipeline sem antes identificar a execução proprietária e confirmar que ela terminou. Preserve as versões do bucket S3 e a configuração anterior como rollback; restaurar o grupo AL2023 antigo sem o bootstrap corrigido reproduziria a falha. Em uma falha de deploy, mantenha o serviço anterior quando possível, analise eventos e logs do namespace e confirme o resultado antes de reenviar.

O Service da aplicação usa `LoadBalancer`; o ELB é um upstream HTTP acessível pela rede conforme as regras AWS criadas, além do gateway público. Valide a exposição e as regras de segurança conforme o ambiente. O Lab possui orçamento limitado e os recursos ativos podem gerar consumo mesmo fora de uma execução de pipeline.
