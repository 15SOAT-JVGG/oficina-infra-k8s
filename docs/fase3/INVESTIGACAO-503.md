# Investigação de 503 - sem causa concluída

## Evidência preservada

- Carga de login: oito HTTP 503 em 211 tentativas; p95 global 0,877s.
  Run: https://github.com/15SOAT-JVGG/oficina-app/actions/runs/41158493007
- O HPA criou réplicas Ready adicionais (2 -> 4). Amostras posteriores mostram retorno a 2.
- Gateway registrou integrações de 29.000 ms nos erros. Essa informação isolada não
  identifica em qual salto ocorreu a espera.
- NLB ativo, dois targets saudáveis; cross-zone passou a true. O erro persistiu depois.
- Houve falhas SMTP por limite de envio, mas a carga de login não envia notificações.
  Portanto SMTP não é explicação suficiente para os erros de carga.
- Seed espaçado de seis OS terminou com 200/201, sem 503 nessa execução:
  https://github.com/15SOAT-JVGG/oficina-app/actions/runs/41158958643

## Inspeção de código

AuthController retorna Uni; AuthService.login consulta o usuário e executa password.matches
sincronamente em onItem().transform. BCrypt é trabalho de CPU e pode ocupar a thread
que entrega o resultado reativo. É uma hipótese a medir, não uma causa comprovada.
Não adicionar @Blocking nem mudar o contexto da sessão Hibernate Reactive sem validar
as restrições do framework e os testes de autenticação.

## Próxima sessão do Lab

1. Renovar HOMOLOG_AWS_* nos mesmos três repositórios autorizados. Validar identidade e
   readiness antes de qualquer carga; não repetir Terraform apply por causa de um 503.
2. Conferir VPC Link, SG/NACL, NLB e targets por zona, apenas com consultas.
3. Rodar load_only com dois workers, teto de 4 req/s, sem seed e sem rollout concorrente.
4. Correlacionar horários dos 503 com CPU, readiness, threads, resets do NLB e latência
   de integração. Preservar somente agregados, nunca corpos, credenciais ou CPF.
5. Se precisar isolar a rede, comparar amostras pequenas pelo Gateway e internamente,
   com a mesma operação, sem publicar o origin nem criar outra exposição pública.
6. Corrigir somente o componente sustentado pelas evidências e repetir o perfil leve.

A queda do Lab interrompe a investigação de runtime. Reduzir a carga é mitigação;
não estabelece estabilidade, não garante escala e não converte run reprovado em aprovado.
