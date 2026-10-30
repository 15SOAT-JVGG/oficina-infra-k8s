# Um único cluster atende os dois ambientes: homologação e produção ficam em namespaces
# distintos (`homolog` e `production`), criados pelos manifests do repositório oficina-app.
# Essa topologia reduz o custo do Learner Lab, já que cada cluster EKS cobra por hora.

data "aws_iam_role" "lab" {
  name = var.lab_role_name
}

# A VPC padrão é a mesma onde o RDS (oficina-infra-db) foi criado, então pods e banco se enxergam
# sem peering. As subnets padrão são públicas, o que dispensa NAT Gateway (custo extra).
data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "cluster" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }

  # As sub-redes privadas criadas para o VPC Link não podem mudar o conjunto já usado
  # pelo EKS/node group nem provocar a substituição do cluster.
  filter {
    name   = "map-public-ip-on-launch"
    values = ["true"]
  }

  filter {
    name   = "availability-zone"
    values = var.availability_zones
  }
}

resource "aws_eks_cluster" "main" {
  name     = var.cluster_name
  version  = var.kubernetes_version
  role_arn = data.aws_iam_role.lab.arn

  vpc_config {
    subnet_ids              = data.aws_subnets.cluster.ids
    endpoint_public_access  = true
    endpoint_private_access = true
  }

  # Access entries: quem cria o cluster (LabRole via credenciais do pipeline) vira administrador,
  # permitindo que o pipeline da aplicação use kubectl com as mesmas credenciais.
  access_config {
    authentication_mode                         = "API_AND_CONFIG_MAP"
    bootstrap_cluster_creator_admin_permissions = true
  }
}

resource "aws_eks_node_group" "main" {
  cluster_name    = aws_eks_cluster.main.name
  node_group_name = "${var.cluster_name}-nodes"
  node_role_arn   = data.aws_iam_role.lab.arn
  subnet_ids      = data.aws_subnets.cluster.ids

  instance_types = var.node_instance_types
  ami_type       = "AL2023_x86_64_STANDARD"
  capacity_type  = "ON_DEMAND"

  scaling_config {
    min_size     = var.node_min_size
    desired_size = var.node_desired_size
    max_size     = var.node_max_size
  }

  update_config {
    max_unavailable = 1
  }

  # O HPA da aplicação cria pods; o número de nós só muda por este recurso.
  lifecycle {
    ignore_changes = [scaling_config[0].desired_size]
  }
}

# Fornece as métricas de CPU/memória consumidas pelo HPA (`kubectl top` e autoscaling/v2).
resource "aws_eks_addon" "metrics_server" {
  cluster_name = aws_eks_cluster.main.name
  addon_name   = "metrics-server"

  depends_on = [aws_eks_node_group.main]
}

resource "aws_ecr_repository" "app" {
  name                 = var.ecr_repository_name
  image_tag_mutability = "MUTABLE"
  force_delete         = true

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_ecr_lifecycle_policy" "app" {
  repository = aws_ecr_repository.app.name

  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Mantém apenas as ${var.ecr_images_to_keep} imagens mais recentes"
      selection = {
        tagStatus   = "any"
        countType   = "imageCountMoreThan"
        countNumber = var.ecr_images_to_keep
      }
      action = {
        type = "expire"
      }
    }]
  })
}
