# Endereço do Service da aplicação por ambiente. O ELB nasce do Kubernetes, não do Terraform:
#   kubectl get svc oficina-mecanica -n <ambiente> -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'
# Ambiente sem entrada aqui fica com o gateway criado, mas sem o proxy para o cluster.
app_upstream_urls = {
  homolog = "http://a91cd8488edce44949bd133f97254db1-66988585.us-east-1.elb.amazonaws.com"
}
