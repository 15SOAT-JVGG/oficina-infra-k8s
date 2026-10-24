output "cluster_name" {
  description = "Nome do cluster EKS."
  value       = aws_eks_cluster.main.name
}

output "cluster_endpoint" {
  description = "Endpoint da API do Kubernetes."
  value       = aws_eks_cluster.main.endpoint
}

output "cluster_security_group_id" {
  description = "Security group do cluster (criado pelo EKS)."
  value       = aws_eks_cluster.main.vpc_config[0].cluster_security_group_id
}

output "ecr_repository_url" {
  description = "URL do repositório ECR da aplicação."
  value       = aws_ecr_repository.app.repository_url
}

output "vpc_id" {
  description = "VPC do cluster (a mesma do RDS)."
  value       = data.aws_vpc.default.id
}

output "subnet_ids" {
  description = "Subnets do cluster."
  value       = data.aws_subnets.cluster.ids
}

output "update_kubeconfig_command" {
  description = "Comando para configurar o kubectl local."
  value       = "aws eks update-kubeconfig --name ${aws_eks_cluster.main.name} --region ${var.aws_region}"
}

output "api_gateway_ids" {
  description = "Id do API Gateway de cada ambiente. O oficina-lambda-auth usa o do seu ambiente para registrar a rota de autenticação."
  value       = { for environment, api in aws_apigatewayv2_api.main : environment => api.id }
}

output "api_gateway_execution_arns" {
  description = "ARN de execução do API Gateway de cada ambiente, usado para autorizar o gateway a invocar a Lambda."
  value       = { for environment, api in aws_apigatewayv2_api.main : environment => api.execution_arn }
}

output "api_gateway_urls" {
  description = "URL pública do API Gateway de cada ambiente."
  value       = { for environment, api in aws_apigatewayv2_api.main : environment => api.api_endpoint }
}
