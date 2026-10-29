#!/usr/bin/env bash
# Verifica a Authorizer e as rotas públicas pelo Gateway real sem imprimir tokens,
# CPFs ou corpos de resposta.
set -euo pipefail
umask 077

BASE_URL="${1:?Uso: api-gateway-authorizer-smoke-test.sh <gateway-url>}"
CUSTOMER_CPF="${AUTHORIZER_TEST_CUSTOMER_CPF:-}"
REQUEST_TIMEOUT_SECONDS="${REQUEST_TIMEOUT_SECONDS:-30}"
JWT_ISSUER="${JWT_ISSUER:-oficina-api}"
TEMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TEMP_DIR"' EXIT
BASE_URL="${BASE_URL%/}"

RESPONSE_FILE="$TEMP_DIR/response.json"
HEADERS_FILE="$TEMP_DIR/headers.txt"
PAYLOAD_FILE="$TEMP_DIR/request.json"
TOKEN_CONFIG="$TEMP_DIR/curl-token.conf"
SUMMARY_FILE="${GITHUB_STEP_SUMMARY:-}"
RESULTS=()
TOKEN=""
REQUEST_ID="-"

fail() {
    echo "FALHA: $*" >&2
    exit 1
}

[[ "$BASE_URL" =~ ^https?://[^/]+/?$ ]] || fail "URL do Gateway inválida."
[[ -n "$CUSTOMER_CPF" ]] || fail "Secret AUTHORIZER_TEST_CUSTOMER_CPF ausente."
[[ "$CUSTOMER_CPF" =~ ^[0-9]{11}$ ]] || fail "Secret AUTHORIZER_TEST_CUSTOMER_CPF deve conter 11 dígitos."
command -v curl >/dev/null || fail "curl não está instalado."
command -v jq >/dev/null || fail "jq não está instalado."

set_token() {
    TOKEN="$1"
    if [[ -n "$TOKEN" ]]; then
        printf 'header = "Authorization: Bearer %s"\n' "$TOKEN" > "$TOKEN_CONFIG"
    else
        : > "$TOKEN_CONFIG"
    fi
}

request() {
    local name="$1" method="$2" path="$3" expected="$4" payload="${5:-}"
    local status request_id
    : > "$PAYLOAD_FILE"
    : > "$HEADERS_FILE"
    if [[ -n "$payload" ]]; then
        printf '%s' "$payload" > "$PAYLOAD_FILE"
    fi

    local args=(--silent --show-error --max-time "$REQUEST_TIMEOUT_SECONDS"
        --request "$method" --header 'Accept: application/json'
        --output "$RESPONSE_FILE" --dump-header "$HEADERS_FILE" --write-out '%{http_code}')
    [[ -s "$TOKEN_CONFIG" ]] && args+=(--config "$TOKEN_CONFIG")
    [[ -s "$PAYLOAD_FILE" ]] && args+=(--header 'Content-Type: application/json' --data-binary "@$PAYLOAD_FILE")

    status="$(curl "${args[@]}" "$BASE_URL$path")" || fail "$name: Gateway não respondeu."
    request_id="$(awk '{lower=tolower($0); if (lower ~ /^x-amzn-requestid:|^x-amz-apigw-id:|^x-request-id:/) {gsub("\r", ""); value=$2}} END {if (value != "") print value}' "$HEADERS_FILE")"
    REQUEST_ID="${request_id:--}"

    case "$expected" in
        2xx) [[ "$status" =~ ^2[0-9][0-9]$ ]] || fail "$name: HTTP $status; requestId=$REQUEST_ID" ;;
        4xx) [[ "$status" =~ ^4[0-9][0-9]$ ]] || fail "$name: HTTP $status; requestId=$REQUEST_ID" ;;
        deny) [[ "$status" == 401 || "$status" == 403 ]] || fail "$name: HTTP $status; requestId=$REQUEST_ID" ;;
        403) [[ "$status" == 403 ]] || fail "$name: HTTP $status; requestId=$REQUEST_ID" ;;
        *) [[ "$status" == "$expected" ]] || fail "$name: HTTP $status; requestId=$REQUEST_ID" ;;
    esac

    RESULTS+=("| $name | $status | $REQUEST_ID |")
}

extract_token() {
    local json_path="$1"
    local payload claims actual_issuer padding
    TOKEN="$(jq -er "$json_path | select(type == \"string\" and length > 0)" "$RESPONSE_FILE")" \
        || fail "A resposta de autenticação não contém token; requestId=$REQUEST_ID"
    payload="${TOKEN#*.}"
    payload="${payload%%.*}"
    payload="$(tr '_-' '/+' <<<"$payload")"
    padding=$(( (4 - ${#payload} % 4) % 4 ))
    payload+="$(printf '%*s' "$padding" '' | tr ' ' '=')"
    claims="$(base64 --decode <<<"$payload" 2>/dev/null)" \
        || fail "Token de autenticação malformado; requestId=$REQUEST_ID"
    actual_issuer="$(jq -er '.iss | strings' <<<"$claims")" \
        || fail "Token sem issuer; requestId=$REQUEST_ID"
    [[ "$actual_issuer" == "$JWT_ISSUER" ]] \
        || fail "Token emitido com issuer inesperado; requestId=$REQUEST_ID"
    set_token "$TOKEN"
}

generate_unused_cpf() {
    local -a digits=()
    local index check_digit weight sum remainder
    for ((index = 0; index < 9; index++)); do digits+=("$((RANDOM % 10))"); done
    for ((check_digit = 0; check_digit < 2; check_digit++)); do
        sum=0
        weight=$((10 + check_digit))
        for ((index = 0; index < 9 + check_digit; index++)); do
            sum=$((sum + digits[index] * (weight - index)))
        done
        remainder=$((sum % 11))
        digits+=("$((remainder < 2 ? 0 : 11 - remainder))")
    done
    printf '%s' "${digits[@]}"
}

if [[ -n "$SUMMARY_FILE" ]]; then
    {
        echo '### API Gateway Authorizer smoke test'
        echo
        echo '| Cenário | HTTP | Request ID |'
        echo '|---|---:|---|'
    } >> "$SUMMARY_FILE"
fi

set_token ""
request 'health público' GET '/q/health/ready' 200

payload="$(jq -cn --arg cpf "$CUSTOMER_CPF" '{cpf:$cpf}')"
request 'login CPF válido' POST '/v1/auth/customer' 200 "$payload"
extract_token '.token'
CUSTOMER_TOKEN="$TOKEN"

# O CPF sintético é válido no algoritmo, mas muda a cada execução e não é impresso.
payload="$(jq -cn --arg cpf "$(generate_unused_cpf)" '{cpf:$cpf}')"
set_token ""
request 'login CPF sem cadastro' POST '/v1/auth/customer' 4xx "$payload"

set_token ""
request 'rota protegida sem token' GET '/v1/me/work-orders' deny
set_token 'malformed.invalid.token'
request 'rota protegida com Bearer malformado' GET '/v1/me/work-orders' deny

set_token "${CUSTOMER_TOKEN}x"
request 'rota protegida com token alterado' GET '/v1/me/work-orders' deny

set_token "$CUSTOMER_TOKEN"
request 'rota CUSTOMER permitida' GET '/v1/me/work-orders' 200
request 'rota operacional negada por RBAC CUSTOMER' GET '/v1/work-orders' 403

if [[ -n "$SUMMARY_FILE" ]]; then
    printf '%s\n' "${RESULTS[@]}" >> "$SUMMARY_FILE"
fi
printf '%s\n' "${RESULTS[@]}"
echo 'Smoke test da Authorizer concluído.'
