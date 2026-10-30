# Subnets sem rota para o Internet Gateway: o VPC Link e os NLBs internos ficam
# alcançáveis pelo API Gateway e pelos serviços do VPC, não pela Internet.
data "aws_subnets" "all_vpc" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

data "aws_subnet" "all_vpc" {
  for_each = toset(data.aws_subnets.all_vpc.ids)
  id       = each.value
}

locals {
  gateway_private_azs = slice(var.availability_zones, 0, 2)

  gateway_candidate_cidrs = [
    for index in range(0, 16) : cidrsubnet(data.aws_vpc.default.cidr_block, 4, index)
  ]

  gateway_existing_cidrs = [
    for subnet in data.aws_subnet.all_vpc : subnet.cidr_block
    if !startswith(lookup(subnet.tags, "Name", ""), "oficina-gateway-private-")
  ]

  gateway_cidr_ranges = {
    for cidr in distinct(concat(local.gateway_candidate_cidrs, local.gateway_existing_cidrs)) : cidr => {
      start = sum([
        for octet_index, octet in split(".", cidrhost(cidr, 0)) :
        tonumber(octet) * pow(256, 3 - octet_index)
      ])
      end = sum([
        for octet_index, octet in split(".", cidrhost(cidr, 0)) :
        tonumber(octet) * pow(256, 3 - octet_index)
      ]) + pow(2, 32 - tonumber(split("/", cidr)[1])) - 1
    }
  }

  gateway_available_cidrs = [
    for candidate in local.gateway_candidate_cidrs : candidate
    if alltrue([
      for existing in local.gateway_existing_cidrs :
      local.gateway_cidr_ranges[candidate].end < local.gateway_cidr_ranges[existing].start ||
      local.gateway_cidr_ranges[existing].end < local.gateway_cidr_ranges[candidate].start
    ])
  ]
}

resource "aws_subnet" "gateway_private" {
  for_each = { for index, az in local.gateway_private_azs : az => index }

  vpc_id                  = data.aws_vpc.default.id
  availability_zone       = each.key
  cidr_block              = local.gateway_available_cidrs[each.value]
  map_public_ip_on_launch = false

  tags = {
    Name                                        = "oficina-gateway-private-${each.key}"
    "kubernetes.io/cluster/${var.cluster_name}" = "shared"
    "kubernetes.io/role/internal-elb"           = "1"
  }
}

resource "aws_route_table" "gateway_private" {
  for_each = aws_subnet.gateway_private

  vpc_id = data.aws_vpc.default.id

  tags = {
    Name = "oficina-gateway-private-${each.key}"
  }
}

resource "aws_route_table_association" "gateway_private" {
  for_each = aws_subnet.gateway_private

  subnet_id      = each.value.id
  route_table_id = aws_route_table.gateway_private[each.key].id
}

resource "aws_security_group" "api_gateway_vpc_link" {
  name_prefix = "oficina-api-gateway-vpc-link-"
  description = "Egress do VPC Link para NLBs internos da Oficina"
  vpc_id      = data.aws_vpc.default.id

  egress {
    description = "HTTP apenas para sub-redes da VPC que hospedam NLBs internos do Gateway"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    # O VPC Link usa as sub-redes privadas acima, mas o NLB interno da aplicação
    # pode resolver para endereços em outras sub-redes da mesma VPC. Limitar o
    # egress às sub-redes existentes evita abrir toda a VPC e permite alcançar
    # os endereços das interfaces do NLB.
    cidr_blocks = [for subnet in data.aws_subnet.all_vpc : subnet.cidr_block]
  }

  tags = {
    Name = "oficina-api-gateway-vpc-link"
  }
}

resource "aws_apigatewayv2_vpc_link" "cluster" {
  name               = "oficina-cluster-private-link"
  subnet_ids         = [for subnet in aws_subnet.gateway_private : subnet.id]
  security_group_ids = [aws_security_group.api_gateway_vpc_link.id]

  tags = {
    Name = "oficina-cluster-private-link"
  }

  lifecycle {
    prevent_destroy = true
  }
}
