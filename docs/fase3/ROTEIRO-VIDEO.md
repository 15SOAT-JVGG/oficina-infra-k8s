# Roteiro simples - demonstração da Fase 3

Meta: 12 a 14 minutos. Limite do enunciado: 15 minutos. Gravar a versão final após fechar
as pendências da matriz; não apresentar painel vazio como indicador atendido.

## Preparação

- Abrir o diagrama de componentes, os quatro repositórios e uma execução de deploy concluída.
- Abrir Swagger, cliente HTTP e os dois dashboards do Grafana.
- Usar apenas dados sintéticos. Ocultar CPF, senha e JWT no enquadramento.
- Fazer o seed antes da gravação: seed_only, 6 OS. A carga é separada: load_only,
  180 segundos, concorrência 2. Esses valores menores ainda precisam de validação de carga.
- Não executar carga junto com rollout. Não repetir seed para gerar pressão: cada lote permanece.

## 1. Apresentação e arquitetura - 1 minuto

Fala sugerida: “Esta é a aplicação da oficina. Organizamos a solução em quatro repositórios:
aplicação, autenticação serverless, infraestrutura Kubernetes e banco gerenciado.”
Mostrar o diagrama e apontar Gateway, Lambda, EKS, PostgreSQL e observabilidade.

## 2. Pipeline e deploy - 2 minutos

Mostrar um PR, proteção da main, checks e uma execução concluída em homologação.
Apontar teste, publicação da imagem, rollout e smoke pelo Gateway. Mostrar também os
workflows dos outros três repositórios. Dizer que produção tem triggers configurados,
mas sua execução ainda não está comprovada nesta homologação.

## 3. Autenticação e API protegida - 2 minutos

Fazer login com CPF sintético ativo sem revelar seu valor nem o JWT. Mostrar apenas HTTP 200.
Consumir uma rota CUSTOMER com sucesso. Repetir sem token (401) e tentar uma rota
operacional como CUSTOMER (403). Explicar que a Lambda verifica cadastro/status e emite JWT.

## 4. Ordem de serviço - 2 minutos

Como funcionário, abrir uma OS e mostrar sua consulta. Usar o lote preparado para mostrar
Recebida, Diagnóstico, Aguardando aprovação, Em execução, Concluída e Entregue.
Explicar o orçamento e a reserva de estoque, sem expor dados pessoais.

## 5. Monitoramento e escala - 3 minutos

No Grafana, abrir Visão geral e Infraestrutura. Mostrar uptime, CPU, memória e réplicas.
Iniciar uma carga leve separada do seed, observar o HPA e sua recuperação. Não prometer
atingir seis pods. Se ocorrer 503, interromper e registrar a falha; não esconder o resultado.
Mostrar latência/erros, volume diário de OS, tempo médio por etapa e falhas de integrações
somente após implementar e validar esses indicadores, ainda pendentes na revisão atual.

## 6. Logs, traces e alertas - 2 minutos

Selecionar uma requisição de teste, mostrar log JSON e o trace correspondente no Tempo.
Demonstrar alerta de falha de OS disparando e resolvendo. Esses exemplos precisam estar
validados antes da gravação final: logs com traceId, sozinhos, não comprovam trace exportado.

## 7. Documentação e encerramento - 1 minuto

Mostrar componentes, as duas sequências, ER, RFCs e ADRs nos arquivos separados.
Encerrar com links dos quatro repositórios e confirmação de acesso do avaliador.

## Depois da gravação

Publicar no YouTube/Vimeo como público ou não listado, conferir acesso e duração de até
15 minutos e incluir o link na folha de entrega. O Portal pede um PDF único com links dos
repositórios, vídeo, documentação e confirmação do avaliador. Os arquivos separados são
material complementar; não substituem o vídeo nem o PDF único.
