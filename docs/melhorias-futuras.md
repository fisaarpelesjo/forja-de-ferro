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

### Versionar O Esquema Do Banco

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

Criar comandos locais para copiar o banco com seguranca e exportar o historico
para CSV ou JSON facilitaria recuperacao e analises externas.

Criterio de conclusao:

- backup usa a API de backup do SQLite
- o arquivo recebe data e hora no nome
- exportacao nao altera o banco
- restauracao possui procedimento documentado e testado

### Melhorar A Observabilidade Do Bot

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

### Adicionar Integracao Continua

Executar os testes automaticamente em cada envio e pull request reduz
regressoes e divergencias entre maquinas.

Criterio de conclusao:

- smoke test, fluxo ponta a ponta e teste do dashboard rodam no GitHub Actions
- a automacao nao usa token real nem banco real

## Prioridade Baixa

### Registrar Qualidade Tecnica Opcional

O RPE mede esforco, mas nao registra sozinho melhora de amplitude, controle ou
execucao. Um campo opcional de observacao curta poderia complementar a analise.

Exemplos:

- tecnica melhor
- amplitude completa
- repeticoes lentas
- execucao instavel

Esse dado nao deve ser obrigatorio nem alterar automaticamente a carga alvo sem
uma regra futura bem definida.

### Permitir Ciclos E Variacoes De Treino

O catalogo atual e fixo para todas as sessoes. No futuro, o sistema pode suportar
modelos A/B ou ciclos, desde que os nomes dos exercicios e o historico continuem
comparaveis.

Antes de implementar:

- definir como cada modelo seleciona exercicios
- preservar `sort_order`, series e repeticoes por sessao
- evitar misturar variacoes diferentes no mesmo historico

### Gerar O Dashboard Por Comando Do Bot

Pode ser util solicitar uma atualizacao ou um resumo pelo Telegram. A geracao do
HTML completo deve continuar local enquanto nao houver uma forma segura e
simples de entrega.

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
7. adicionar integracao continua
8. avaliar recursos opcionais com base no uso real

## Manutencao Deste Documento

Ao iniciar uma melhoria:

- confirmar se ela ainda resolve um problema real
- registrar a decisao tecnica no documento relacionado
- criar ou atualizar testes
- atualizar `AGENTS.md`, `CLAUDE.md` e
  `.github/copilot-instructions.md` quando o comportamento ou a estrutura mudar

Ao concluir uma melhoria, remover o item daqui ou marca-lo como entregue com a
data e a referencia do commit.
