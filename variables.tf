variable "aws_region" {
  description = "Região AWS onde os recursos são criados."
  type        = string
  default     = "us-east-1"
}

variable "cluster_name" {
  description = "Nome do cluster EKS."
  type        = string
  default     = "oficina"
}

variable "kubernetes_version" {
  description = "Versão do Kubernetes do cluster EKS."
  type        = string
  default     = "1.34"
}

variable "availability_zones" {
  description = "AZs usadas pelo cluster. Evita us-east-1e, que não suporta o control plane do EKS."
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b", "us-east-1c"]
}

variable "node_instance_types" {
  description = "Tipos de instância do node group (o Learner Lab permite até large)."
  type        = list(string)
  default     = ["t3.medium"]
}

variable "node_min_size" {
  description = "Mínimo de nós do node group."
  type        = number
  default     = 2
}

variable "node_desired_size" {
  description = "Quantidade desejada de nós."
  type        = number
  default     = 2
}

variable "node_max_size" {
  description = "Máximo de nós (limite do escalonamento do cluster)."
  type        = number
  default     = 4
}

variable "ecr_repository_name" {
  description = "Nome do repositório ECR da aplicação."
  type        = string
  default     = "oficina-app"
}

variable "ecr_images_to_keep" {
  description = "Quantidade de imagens mantidas no ECR (as mais recentes)."
  type        = number
  default     = 15
}

variable "lab_role_name" {
  description = "Role pré-existente do AWS Academy usada pelo cluster e pelos nós (não é possível criar IAM no Learner Lab)."
  type        = string
  default     = "LabRole"
}

variable "app_upstream_urls" {
  description = "Endereço do Service da aplicação por ambiente (http://<hostname-do-ELB>). Ambiente ausente ou vazio fica sem o proxy para o cluster."
  type        = map(string)
  default     = {}
}

variable "log_retention_days" {
  description = "Dias de retenção dos logs de acesso do API Gateway no CloudWatch."
  type        = number
  default     = 7
}

variable "api_throttling_burst_limit" {
  description = "Limite de rajada de requisições do API Gateway."
  type        = number
  default     = 100
}

variable "api_throttling_rate_limit" {
  description = "Limite de requisições por segundo do API Gateway."
  type        = number
  default     = 50
}
