# Roteiro de demonstração - máximo 15 minutos

O usuário gravará o vídeo após fechar as pendências técnicas da matriz. Este roteiro não
representa vídeo já produzido. Meta de duração: 14min30s, com margem de 30s.

| Tempo | Demonstração | Evidência visível |
|---|---|---|
| 00:00-00:45 | Apresentar o problema, quatro repositórios e diagrama de componentes | Links e componentes reais |
| 00:45-02:15 | Mostrar PR/main protegida e execução de pipeline | Commit, checks e deploy concluído; não apenas disparo |
| 02:15-04:00 | Autenticar cliente sintético por CPF | Resposta 200 sem CPF/token no enquadramento; identificar grupo CUSTOMER |
| 04:00-05:00 | Consumir rota protegida e mostrar negativas | 200 de cliente; 401 sem token; 403 token inválido/RBAC |
| 05:00-07:00 | Funcionário abre e avança uma OS controlada | 201, sequência de estados e persistência; sem dados reais |
| 07:00-08:30 | Demonstrar escalabilidade e saúde | HPA, réplicas e readiness sob carga limitada |
| 08:30-10:30 | Grafana: visão geral e infraestrutura | Tráfego/latência/erros, uptime, CPU/memória |
| 10:30-12:00 | Indicadores de negócio exigidos | Volume por dia, médias por etapa e falhas de integrações; pendente implementação/evidência |
| 12:00-13:15 | Investigar log e trace do mesmo fluxo | JSON, correlação e trace exportado de fato |
| 13:15-14:00 | Mostrar alerta de falha de OS e recuperação | firing e resolved; destino quando configurado |
| 14:00-14:30 | Encerrar com ER, decisões e links de entrega | Documentação e avaliador nos quatro repositórios |

## Antes de gravar

- Confirmar sessão AWS ainda válida e endpoints ativos; não mostrar a tela de credenciais.
- Fechar todos os itens de negócio/alertas/traces na matriz; não apresentar painel vazio como zero.
- Preparar dados exclusivamente sintéticos e requests que não exibam senha/JWT/CPF.
- Preservar logs/traces necessários durante a gravação: emptyDir perde histórico em recriação.
- Mostrar uma execução automatizada concluída dos quatro repositórios; o DB não foi reaplicado
  nesta revisão e sua sessão atual precisa ser conferida sem ampliar o escopo de secrets definido pelo usuário.
- Conferir as alterações na documentação e os links ativos nos quatro READMEs.
- Fazer upload público/não listado no YouTube/Vimeo, conferir duração <=15min e acesso sem login.
- Preencher o link real em ENTREGA.md e gerar o PDF único de submissão somente depois disso.
