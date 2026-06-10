# Melhorias Futuras

Este documento registra somente melhorias que ainda precisam ser avaliadas ou
implementadas na Forja de Ferro.

## Estado Atual

Nao existem melhorias tecnicas priorizadas pendentes.

Novas propostas devem entrar neste arquivo apenas quando resolverem uma
necessidade observada no uso. Evite adicionar funcionalidades por antecipacao
ou manter tarefas ja concluidas como se ainda fizessem parte da fila.

## Principios

- preservar o SQLite como fonte da verdade
- manter o bot simples de operar pelo celular
- priorizar confiabilidade antes de adicionar funcionalidades
- evitar interpretar RPE 9 isolado como estagnacao
- manter compatibilidade com o historico existente
- testar mudancas sem alterar o banco ou a sessao reais
- manter interface e documentacao em PT-BR
- evitar novos aliases e exigir `/` nos comandos textuais do Telegram

## Novas Propostas

Nenhuma proposta pendente.

Antes de adicionar um item:

1. confirmar que o problema foi observado no uso real
2. descrever o impacto e o comportamento esperado
3. definir um criterio objetivo de conclusao
4. avaliar riscos para o banco e o historico
5. planejar testes isolados

## Historico De Entregas

### 2026-06-10

- extracao em lote de frames para analise de execucao:
  `8761362 feat: extrai frames de videos locais`
- documentacao do fluxo de videos e frames:
  `2eb008a docs: documenta analise de videos por frames`
- remocao de aliases e exigencia de `/` nos comandos textuais:
  `d2957cb refactor: remove aliases de comandos`
- catalogo centralizado de comandos:
  `3f9d58e docs: centraliza catalogo de comandos`

### 2026-06-09

- alertas coerentes com a regra de RPE:
  `4b693c5 feat: contextualize training alerts`
- testes diretos das regras de treino:
  `13f0b3f test: cover training rules`
- recuperacao da sessao ativa pelo SQLite:
  `a09a605 feat: recover active training sessions`
- versionamento e migracoes do esquema:
  `fee63a4 feat: version SQLite schema`
- backup, exportacao e restauracao:
  `f8ab04b feat: add data backup tools`
- observabilidade e tratamento de falhas do Telegram:
  `b7ff6a3 feat: improve Telegram reliability`
- resumo automatico ao concluir o treino:
  `09d134b feat: summarize completed workouts`
- grupos musculares armazenados no SQLite:
  `1713401 feat: store muscle groups in SQLite`
- planos de treino selecionaveis:
  `846654f feat: add selectable training plans`
- atualizacao do dashboard pelo Telegram:
  `f92b322 feat: update dashboard from Telegram`

## Itens Fora De Prioridade

Os itens abaixo nao devem ser implementados sem uma necessidade concreta:

- criar servidor web apenas para substituir o long polling
- trocar SQLite por banco remoto
- criar aplicativo movel separado
- adicionar contas e autenticacao multiusuario
- tornar o dashboard publico

Esses itens aumentam manutencao e superficie de falha sem resolver problemas
atuais do projeto.

## Manutencao Deste Documento

Ao iniciar uma melhoria:

- registrar a decisao tecnica no documento relacionado
- criar ou atualizar testes
- atualizar `AGENTS.md`, `CLAUDE.md` e
  `.github/copilot-instructions.md` quando o comportamento ou a estrutura mudar
- revisar README, `docs/index.md` e demais guias afetados

Ao concluir:

- remover o item de `Novas Propostas`
- registrar a entrega no historico com data e commit
