# Porta de entrada única da API, uma por ambiente. HTTP API, e não REST API, porque cobre o que o
# projeto precisa (rota por método e caminho, proxy HTTP, integração Lambda, throttling e log de
# acesso) com latência e custo menores, e sem o deploy explícito de estágio do REST API.
#
# O cluster é compartilhado e o state é único, então os dois gateways nascem juntos. Custa
# praticamente nada manter o de production: o API Gateway cobra por requisição.
#
# A rota POST /v1/auth/customer, que leva à função de autenticação por CPF, não é criada aqui:
# ela pertence ao repositório oficina-lambda-auth, que só precisa do id do gateway do ambiente
# (output api_gateway_ids). O resto do tráfego segue para o cluster.
locals {
  environments = toset(["homolog", "production"])
}

resource "aws_apigatewayv2_api" "main" {
  for_each = local.environments

  name          = "oficina-${each.key}"
  protocol_type = "HTTP"
  description   = "Entrada da API da oficina (${each.key}): autenticação por CPF e proxy para o cluster"
}

resource "aws_cloudwatch_log_group" "api_gateway_access" {
  for_each = local.environments

  name              = "/aws/apigateway/oficina-${each.key}"
  retention_in_days = var.log_retention_days
}

# O estágio $default publica cada mudança de rota sem um deploy à parte. O log de acesso em JSON
# dá latência por rota, status e o requestId que correlaciona a chamada com o log da função e da
# aplicação.
resource "aws_apigatewayv2_stage" "default" {
  for_each = local.environments

  api_id      = aws_apigatewayv2_api.main[each.key].id
  name        = "$default"
  auto_deploy = true

  default_route_settings {
    throttling_burst_limit = var.api_throttling_burst_limit
    throttling_rate_limit  = var.api_throttling_rate_limit
  }

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gateway_access[each.key].arn
    format = jsonencode({
      requestId          = "$context.requestId"
      ip                 = "$context.identity.sourceIp"
      httpMethod         = "$context.httpMethod"
      routeKey           = "$context.routeKey"
      path               = "$context.path"
      status             = "$context.status"
      responseLength     = "$context.responseLength"
      latencyMs          = "$context.responseLatency"
      integrationLatency = "$context.integrationLatency"
      integrationStatus  = "$context.integrationStatus"
      integrationError   = "$context.integration.error"
      requestTime        = "$context.requestTime"
    })
  }
}

# O ELB nasce do Service do Kubernetes, não do Terraform, então o endereço só existe depois do
# primeiro deploy da aplicação no ambiente. Ambiente sem endereço em app_upstream_urls fica sem o
# proxy; preenchê-lo e aplicar de novo liga a rota.
locals {
  upstream_urls = {
    for environment, url in var.app_upstream_urls : environment => trimsuffix(url, "/")
    if contains(local.environments, environment) && url != ""
  }
}

resource "aws_apigatewayv2_integration" "cluster" {
  for_each = local.upstream_urls

  api_id             = aws_apigatewayv2_api.main[each.key].id
  integration_type   = "HTTP_PROXY"
  integration_method = "ANY"
  integration_uri    = "${each.value}/{proxy}"

  # O cluster responde em até 29s, o teto do HTTP API; acima disso o gateway devolve 504 antes da
  # aplicação, e o access log registra integrationError.
  timeout_milliseconds = 29000
}

resource "aws_apigatewayv2_route" "cluster" {
  for_each = local.upstream_urls

  api_id    = aws_apigatewayv2_api.main[each.key].id
  route_key = "ANY /{proxy+}"
  target    = "integrations/${aws_apigatewayv2_integration.cluster[each.key].id}"
}
