# Melhorias Futuras

Este documento registra melhorias desejaveis para a Forja de Ferro. Ele nao e
uma lista de tarefas obrigatorias nem substitui uma decisao de implementacao.
Cada item deve ser reavaliado antes de virar codigo, considerando utilidade,
risco para o historico e simplicidade operacional.

## Principios

- preservar o SQLite como fonte da verdade
- manter o bot simples de operar pelo celular
- priorizar confiabilidade antes de adicionar funcionalidades
- evitar interpretar RPE 9 isolado como estagnacao
- manter compatibilidade com o historico existente
- testar mudancas sem alterar o banco ou a sessao reais
- manter interface e documentacao em PT-BR

## Prioridade Alta

### Tornar Os Alertas Coerentes Com A Regra De RPE

Entregue em 2026-06-09.

O dashboard atualmente alerta quando o RPE medio fica em 9 ou mais e quando a
carga nao aumenta em tres entradas. Esses sinais podem ser informativos, mas nao
devem classificar consolidacao tecnica como falta de progresso.

Melhoria proposta:

- trocar alertas absolutos por mensagens de acompanhamento
- considerar a passagem da mesma carga de RPE 9 para RPE 8 como evolucao
- diferenciar manutencao intencional, reducao por RPE 10 e possivel estagnacao
- evitar alertar apenas porque a carga ficou igual por tres sessoes

Criterio de conclusao:

- nenhuma mensagem considera RPE 9 ou carga mantida um problema isolado
- testes cobrem consolidacao, progressao e reducao de carga

### Ampliar Os Testes Das Regras De Treino

Entregue em 2026-06-09.

As regras centrais merecem testes diretos, alem do fluxo ponta a ponta.

Cobertura proposta:

- progressao completa de RPE 7, 8, 9 e 10
- carga sem RPE
- alvo inicial da rosca martelo
- observacoes de montagem das barras W e H
- descanso de cada categoria de exercicio
- entrada invalida, sessao completa e `/desfazer` sem registro
- `/exercicios`, `/volume`, `/prever` e dashboard

Criterio de conclusao:

- regras de negocio podem ser alteradas com falhas claras quando houver regressao
- todos os testes usam banco e arquivos temporarios

### Recuperar A Sessao Ativa Pelo SQLite

Entregue em 2026-06-09.

`session.json` e apenas contexto local, mas sua perda interrompe o fluxo mesmo
quando a sessao e os logs continuam no banco.

Melhoria proposta:

- reconstruir a sessao ativa pela sessao SQLite mais recente com logs pendentes
- manter `session.json` como cache simples, nao como dependencia unica
- detectar arquivo antigo, corrompido ou apontando para logs inexistentes

Criterio de conclusao:

- apagar `session.json` durante uma sessao nao perde o progresso
- o bot recupera somente uma sessao realmente incompleta
- sessoes completas nao sao reabertas

## Prioridade Media

### Gerar Resumo Automatico Ao Concluir O Treino

Entregue em 2026-06-09.

Quando o ultimo exercicio receber carga, o bot pode enviar um resumo da sessao
sem exigir um novo comando.

Resumo proposto:

- volume total da sessao
- RPE medio
- comparacao de volume com a sessao anterior
- exercicios que aumentaram ou reduziram carga
- consolidacoes confirmadas, quando a mesma carga passar de RPE 9 para RPE 8
- cargas mantidas em RPE 9, sem classifica-las automaticamente como estagnacao
- recordes pessoais de carga ou volume

A duracao do treino so deve aparecer depois que o horario de inicio e conclusao
for armazenado de forma confiavel.

Criterio de conclusao:

- o resumo e enviado automaticamente ao completar o ultimo exercicio
- os calculos usam apenas logs preenchidos da sessao concluida
- a comparacao usa a sessao anterior compativel
- RPE 9 mantido e consolidacao confirmada aparecem como conceitos distintos

### Armazenar Grupos Musculares No SQLite

Entregue em 2026-06-09.

Hoje os grupos musculares ficam definidos em mapas no codigo. Isso exige
alterar Python quando um exercicio novo entra no catalogo e pode fazer
exercicios desconhecidos aparecerem como `Outros`.

Melhoria proposta:

- criar uma tabela de relacao entre exercicios e grupos musculares
- permitir distinguir grupo principal e secundario
- fazer `/volume` e dashboard consultarem o SQLite
- manter compatibilidade com o historico e com nomes antigos
- migrar os grupos atuais sem alterar os calculos existentes

Beneficios:

- catalogo pode mudar sem editar mapas no codigo
- volume semanal por grupo fica mais consistente
- exercicios novos deixam de depender de reconhecimento pelo nome
- a mesma classificacao passa a ser usada pelo bot e pelo dashboard

Criterio de conclusao:

- todos os exercicios ativos possuem pelo menos um grupo muscular
- `/volume` e dashboard usam a mesma fonte de dados
- nenhum exercicio ativo aparece como `Outros`
- testes cobrem grupos principais, secundarios e exercicio sem classificacao

### Versionar O Esquema Do Banco

Entregue em 2026-06-09.

O banco e versionado junto com o projeto, mas ainda nao existe um mecanismo
explicito de versao e migracao do esquema.

Melhoria proposta:

- registrar uma versao de esquema
- executar migracoes pequenas e idempotentes
- validar compatibilidade antes de iniciar o bot
- documentar backup e recuperacao antes de cada migracao

Criterio de conclusao:

- bancos antigos podem ser atualizados sem recriacao manual
- uma migracao interrompida nao deixa o banco em estado ambiguo

### Automatizar Backup E Exportacao

Entregue em 2026-06-09.

Criar comandos locais para copiar o banco com seguranca e exportar o historico
para CSV ou JSON facilitaria recuperacao e analises externas.

Criterio de conclusao:

- backup usa a API de backup do SQLite
- o arquivo recebe data e hora no nome
- exportacao nao altera o banco
- restauracao possui procedimento documentado e testado

### Melhorar A Observabilidade Do Bot

Entregue em 2026-06-09.

O polling deve deixar mais claro quando houve falha de rede, token invalido,
erro de leitura da sessao ou erro de banco.

Melhoria proposta:

- logs estruturados e mensagens de erro em PT-BR
- repeticao com espera gradual para falhas temporarias de rede
- encerramento claro para erros permanentes de configuracao
- identificacao da sessao e do comando nos logs, sem expor token

Criterio de conclusao:

- uma falha pode ser diagnosticada pelo terminal sem editar o codigo
- segredos nunca aparecem nos logs

## Prioridade Baixa

### Permitir Ciclos E Variacoes De Treino

Entregue em 2026-06-09.

O catalogo atual e fixo para todas as sessoes. No futuro, o sistema pode suportar
modelos A/B ou ciclos, desde que os nomes dos exercicios e o historico continuem
comparaveis.

Antes de implementar:

- definir como cada modelo seleciona exercicios
- preservar `sort_order`, series e repeticoes por sessao
- evitar misturar variacoes diferentes no mesmo historico

### Gerar O Dashboard Por Comando Do Bot

Adicionar um comando oficial, como `/dashboard`, para atualizar o dashboard sem
precisar acessar o terminal.

Fluxo proposto:

- o bot executa a mesma geracao usada por `python gerar_dashboard.py`
- o HTML continua salvo localmente em `temp/dashboard-treino.html`
- o bot confirma data e horario da atualizacao
- a resposta pode incluir um resumo curto da ultima sessao
- o arquivo completo so deve ser enviado pelo Telegram depois de validar
  tamanho, seguranca e tratamento de falhas

Resumo opcional na resposta:

- volume e RPE medio da ultima sessao
- comparacao com a sessao anterior
- aumentos, reducoes e cargas mantidas
- consolidacoes confirmadas
- recordes pessoais

Criterio de conclusao:

- `/dashboard` atualiza o HTML usando a mesma funcao do launcher local
- falhas de leitura ou escrita geram resposta clara e log no terminal
- o comando nao cria nem altera sessoes de treino
- testes usam banco e arquivo de saida temporarios
- o envio do HTML permanece opcional e nao expoe caminhos locais

## Itens Que Nao Sao Prioridade

- criar servidor web apenas para substituir o long polling
- trocar SQLite por um banco remoto sem necessidade real
- criar aplicativo movel separado
- adicionar contas e autenticacao multiusuario
- tornar o dashboard publico
- remover aliases antigos que ainda preservam compatibilidade

Esses itens aumentariam manutencao e superficie de falha sem resolver os riscos
mais importantes do projeto atual.

## Ordem Recomendada

1. corrigir a semantica dos alertas de RPE e carga mantida
2. ampliar testes das regras centrais
3. recuperar sessao ativa pelo SQLite
4. adicionar versao e migracoes do banco
5. automatizar backup e exportacao
6. melhorar logs e tratamento de falhas do polling
7. gerar resumo automatico ao concluir o treino
8. armazenar grupos musculares no SQLite
9. permitir ciclos e variacoes de treino
10. gerar o dashboard por comando do bot

## Manutencao Deste Documento

Ao iniciar uma melhoria:

- confirmar se ela ainda resolve um problema real
- registrar a decisao tecnica no documento relacionado
- criar ou atualizar testes
- atualizar `AGENTS.md`, `CLAUDE.md` e
  `.github/copilot-instructions.md` quando o comportamento ou a estrutura mudar

Ao concluir uma melhoria, remover o item daqui ou marca-lo como entregue com a
data e a referencia do commit.
