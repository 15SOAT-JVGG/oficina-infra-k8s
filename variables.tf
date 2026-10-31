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
  description = "URL pública legada do upstream por ambiente, mantida até o contrato publicar listener NLB interno."
  type        = map(string)
  default     = {}

  validation {
    condition = alltrue([
      for environment, url in var.app_upstream_urls :
      !contains(["homolog", "production"], environment) || url == "" || try(can(regex("^https?://[^/]+$", url)), false)
    ])
    error_message = "Cada upstream legado deve ser uma URL HTTP(S) sem caminho de homolog ou production."
  }
}

variable "app_upstream_listener_arns" {
  description = "ARN do listener NLB interno da aplicação por ambiente, quando o contrato já foi migrado."
  type        = map(string)
  default     = {}

  validation {
    condition = alltrue([
      for environment, arn in var.app_upstream_listener_arns :
      !contains(["homolog", "production"], environment) || arn == "" || can(regex("^arn:[^:]+:elasticloadbalancing:[^:]+:[0-9]{12}:listener/net/.+$", arn))
    ])
    error_message = "Cada listener de upstream deve ser um ARN NLB válido de homolog ou production."
  }
}

variable "grafana_listener_arns" {
  description = "ARN do listener NLB interno do Grafana para os ambientes autorizados, vindo do contrato S3 de observabilidade."
  type        = map(string)
  default     = {}

  validation {
    condition = alltrue([
      for environment, arn in var.grafana_listener_arns :
      !contains(["homolog", "production"], environment) || arn == "" || can(regex("^arn:[^:]+:elasticloadbalancing:[^:]+:[0-9]{12}:listener/net/.+$", arn))
    ])
    error_message = "O Grafana deve usar ARN de listener NLB válido em homolog ou production."
  }
}

variable "authorizer_arns" {
  description = "ARN da Lambda Authorizer por ambiente, lido do contrato S3 de authorizer."
  type        = map(string)
  default     = {}

  validation {
    condition = alltrue([
      for environment, arn in var.authorizer_arns :
      !contains(["homolog", "production"], environment) || arn == "" || can(regex("^arn:[^:]+:lambda:[^:]+:[0-9]{12}:function:.+$", arn))
      ]) && alltrue([
      for environment, url in var.app_upstream_urls :
      url == "" || try(var.authorizer_arns[environment] != "", false)
    ])
    error_message = "Cada upstream deve ter um ARN Lambda Authorizer válido correspondente."
  }
}

variable "public_api_docs_environments" {
  description = "Ambientes em que OpenAPI e Swagger UI ficam públicos para demonstrações."
  type        = set(string)
  default     = ["homolog"]

  validation {
    condition = alltrue([
      for environment in var.public_api_docs_environments :
      contains(["homolog", "production"], environment)
    ])
    error_message = "public_api_docs_environments aceita apenas homolog e production."
  }
}

variable "gateway_contract_account_id" {
  description = "Conta AWS dos contratos S3 de upstream e Authorizer; impede aplicar artefatos de outra conta."
  type        = string
  default     = ""

  validation {
    condition     = var.gateway_contract_account_id == "" || can(regex("^[0-9]{12}$", var.gateway_contract_account_id))
    error_message = "gateway_contract_account_id deve conter 12 dígitos."
  }
}

variable "gateway_contract_region" {
  description = "Região AWS registrada nos contratos S3 do Gateway."
  type        = string
  default     = ""

  validation {
    condition     = var.gateway_contract_region == "" || var.gateway_contract_region == var.aws_region
    error_message = "A região dos contratos precisa coincidir com aws_region."
  }
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
