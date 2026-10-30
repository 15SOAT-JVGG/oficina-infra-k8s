# Porta de entrada única da API, uma por ambiente. HTTP API, e não REST API, porque cobre o que o
# projeto precisa (rota por método e caminho, proxy HTTP, integração Lambda, throttling e log de
# acesso) com latência e custo menores, e sem o deploy explícito de estágio do REST API.
#
# O cluster é compartilhado e o state é único, então os dois gateways nascem juntos. Custa
# praticamente nada manter o de production: o API Gateway cobra por requisição.
#
# A rota POST /v1/auth/customer continua sob responsabilidade de oficina-lambda-auth. As rotas
# encaminhadas ao cluster são divididas entre exceções públicas e o proxy autenticado.
locals {
  upstream_urls = {
    for environment, url in var.app_upstream_urls : environment => trimsuffix(url, "/")
    if contains(local.environments, environment) && url != ""
  }

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

# Os listeners NLB internos e o Authorizer são publicados como contratos no S3. O workflow
# reutilizável os injeta nos mapas; um upstream sem Authorizer é inválido.
locals {
  upstream_listener_arns = {
    for environment, arn in var.app_upstream_listener_arns : environment => arn
    if contains(local.environments, environment) && arn != ""
  }

  authorizer_arns = {
    for environment, arn in var.authorizer_arns : environment => arn
    if contains(local.environments, environment) && arn != ""
  }

  grafana_listener_arns = {
    for environment, arn in var.grafana_listener_arns : environment => arn
    if contains(local.environments, environment) && arn != ""
  }

  public_route_keys = toset(flatten([
    for environment in keys(local.upstream_urls) : [
      for route_key in concat(
        [
          "POST /v1/auth/login",
          "POST /v1/worker/login",
          "GET /v1/public/work-orders/tracking/{token}",
          "POST /v1/public/work-orders/estimate-decisions/{token}",
          "GET /q/health",
          "GET /q/health/live",
          "GET /q/health/ready",
        ],
        contains(var.public_api_docs_environments, environment) ? [
          "GET /q/openapi",
          "GET /q/swagger-ui",
          "GET /q/swagger-ui/{proxy+}",
        ] : []
      ) : "${environment}|${route_key}"
    ]
  ]))

  grafana_route_keys = toset(flatten([
    for environment in keys(local.grafana_listener_arns) : [
      "${environment}|ANY /observability",
      "${environment}|ANY /observability/{proxy+}",
    ]
  ]))
}

resource "aws_apigatewayv2_authorizer" "jwt" {
  for_each = local.authorizer_arns

  api_id                            = aws_apigatewayv2_api.main[each.key].id
  name                              = "oficina-${each.key}-jwt"
  authorizer_type                   = "REQUEST"
  authorizer_uri                    = "arn:aws:apigateway:${var.aws_region}:lambda:path/2015-03-31/functions/${each.value}/invocations"
  identity_sources                  = ["$request.header.Authorization"]
  authorizer_payload_format_version = "2.0"
  enable_simple_responses           = true
  authorizer_result_ttl_in_seconds  = 0

  # Ausência de contrato não pode remover um Authorizer já provisionado.
  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_lambda_permission" "gateway_authorizer" {
  for_each = local.authorizer_arns

  # Cada versão precisa de um statement diferente para permitir sobreposição
  # durante a troca do authorizer, antes de retirar a permissão anterior.
  statement_id = "AllowOficinaGateway-${each.key}-${substr(sha1(each.value), 0, 12)}"
  action       = "lambda:InvokeFunction"
  # O provider armazena a versão separadamente; usar o ARN qualificado inteiro
  # aqui causa substituições repetidas após cada refresh do state.
  function_name = join(":", slice(split(":", each.value), 0, 7))
  qualifier     = try(split(":", each.value)[7], null)
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main[each.key].execution_arn}/*/*"

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_apigatewayv2_integration" "cluster" {
  for_each = local.upstream_urls

  api_id             = aws_apigatewayv2_api.main[each.key].id
  integration_type   = "HTTP_PROXY"
  integration_method = "ANY"
  integration_uri    = lookup(local.upstream_listener_arns, each.key, each.value)
  connection_type    = contains(keys(local.upstream_listener_arns), each.key) ? "VPC_LINK" : "INTERNET"
  connection_id      = contains(keys(local.upstream_listener_arns), each.key) ? aws_apigatewayv2_vpc_link.cluster.id : null
  request_parameters = {
    "overwrite:path" = "$request.path"
  }

  # O cluster responde em até 29s, o teto do HTTP API; acima disso o gateway devolve 504 antes da
  # aplicação, e o access log registra integrationError.
  timeout_milliseconds = 29000

  # Remover o contrato não pode desconectar um ambiente que já tinha upstream.
  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_apigatewayv2_route" "cluster" {
  for_each = local.upstream_urls

  api_id             = aws_apigatewayv2_api.main[each.key].id
  route_key          = "ANY /{proxy+}"
  target             = "integrations/${aws_apigatewayv2_integration.cluster[each.key].id}"
  authorization_type = "CUSTOM"
  authorizer_id      = aws_apigatewayv2_authorizer.jwt[each.key].id
  depends_on         = [aws_lambda_permission.gateway_authorizer]

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_apigatewayv2_route" "root" {
  for_each = local.upstream_urls

  api_id             = aws_apigatewayv2_api.main[each.key].id
  route_key          = "ANY /"
  target             = "integrations/${aws_apigatewayv2_integration.cluster[each.key].id}"
  authorization_type = "CUSTOM"
  authorizer_id      = aws_apigatewayv2_authorizer.jwt[each.key].id
  depends_on         = [aws_lambda_permission.gateway_authorizer]

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_apigatewayv2_route" "public" {
  for_each = local.public_route_keys

  api_id             = aws_apigatewayv2_api.main[split("|", each.key)[0]].id
  route_key          = split("|", each.key)[1]
  target             = "integrations/${aws_apigatewayv2_integration.cluster[split("|", each.key)[0]].id}"
  authorization_type = "NONE"
}

resource "aws_apigatewayv2_integration" "grafana" {
  for_each = local.grafana_listener_arns

  api_id             = aws_apigatewayv2_api.main[each.key].id
  integration_type   = "HTTP_PROXY"
  integration_method = "ANY"
  integration_uri    = each.value
  connection_type    = "VPC_LINK"
  connection_id      = aws_apigatewayv2_vpc_link.cluster.id
  request_parameters = {
    "overwrite:path" = "$request.path"
  }

  timeout_milliseconds = 29000

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_apigatewayv2_route" "grafana" {
  for_each = local.grafana_route_keys

  api_id             = aws_apigatewayv2_api.main[split("|", each.key)[0]].id
  route_key          = split("|", each.key)[1]
  target             = "integrations/${aws_apigatewayv2_integration.grafana[split("|", each.key)[0]].id}"
  authorization_type = "NONE"
}
