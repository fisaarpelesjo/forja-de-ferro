# Instrucoes Do Copilot Para Este Repositorio

## Contexto Do Projeto

A Forja de Ferro e um diario de treino e dieta com bot do Telegram e banco SQLite local.

Banco principal: `data/forja_de_ferro.db`.
Launcher multiplataforma: `start_bot.py`.
Wrapper Windows: `start_bot.bat`.
Dashboard local: `gerar_dashboard.py` gera `temp/dashboard-treino.html`.

SQLite e a fonte da verdade para exercicios, sessoes, logs de treino e dados de
dieta. Nao mover a gestao de exercicios de volta para ODS.

## Padrao De Idioma

O projeto deve ser o mais PT-BR possivel. Use portugues brasileiro como padrao
para interface, mensagens do bot, comandos principais, ajuda, documentacao
tecnica, exemplos, titulos Markdown, nomes de arquivos e pastas novos de
documentacao, mensagens de launcher e textos visiveis ao usuario.

Aliases antigos em ingles podem permanecer por compatibilidade, mas a ajuda
principal, os exemplos e a documentacao devem priorizar nomes e comandos em
PT-BR.

## Sincronizacao Das Instrucoes De Agentes

Sempre que uma mudanca alterar comportamento, comandos, fluxo de uso, estrutura
de arquivos, nomes de caminhos, catalogo de exercicios, banco de dados,
launchers, padrao de idioma ou documentacao principal, revisar e atualizar em
conjunto:

- `AGENTS.md`
- `CLAUDE.md`
- `.github/copilot-instructions.md`

Nao atualizar apenas um arquivo de agente quando a informacao tambem se aplicar
aos outros. Antes de finalizar uma mudanca, verificar se README, `docs/index.md`
ou outros documentos em `docs/` tambem precisam ser atualizados.

## Arquivos Principais

### `start_bot.py`

Launcher principal para iniciar o bot.

### `start_bot.bat`

Wrapper Windows para iniciar o bot com duplo clique ou pelo terminal.

### `gerar_dashboard.py`

Launcher local que gera o dashboard HTML de volume de treino em
`temp/dashboard-treino.html`.

### `forja_de_ferro/telegram_poller.py`

Bot Telegram com long polling.

Comandos principais:

- `/gerar`
- `/prever`
- `/exercicios`
- `/aquecimento`
- `/volume`
- `/status`
- `/desfazer`
- `/ajuda`
- `80` ou `80 8` para registrar carga e RPE opcional

Aliases legados em ingles podem existir para compatibilidade:

- `/generate`
- `/exercises`
- `/warmup`
- `/undo`
- `/help`

Fluxo principal:

1. `/gerar` cria uma sessao de treino no SQLite.
2. `ods_ops.write_session(...)` grava o estado ativo em `session.json`.
3. O texto de treino mostra `alvo`, calculado pela ultima carga registrada e pelo RPE, e `descanso`.
4. `/prever` mostra o mesmo formato sem criar sessao, logs ou `session.json`.
5. Entrada de carga atualiza diretamente o log correspondente em `data/forja_de_ferro.db`.
6. `/desfazer` limpa o ultimo registro preenchido.

### `forja_de_ferro/ods_ops.py`

Camada auxiliar de sessao de treino. O nome e historico, mas o fluxo atual usa
SQLite e `session.json`.

Funcoes importantes:

- `generate_training()` cria uma sessao SQLite e retorna `(exercises, session_id)`.
- `preview_training()` monta o treino sem persistir sessao, logs ou `session.json`.
- `gerar_treino()` e alias de compatibilidade.
- `read_exercises()` le exercicios do SQLite.
- `read_previous_weights()` retorna a carga mais recente por exercicio.
- `read_previous_performance()` retorna carga e RPE mais recentes por exercicio.
- `suggest_next_weight(previous_weight, previous_rpe=None)` calcula a carga alvo pela regra de RPE.
- `get_rest_interval(exercise_name)` retorna o descanso sugerido entre series.
- `format_loading_note(exercise_name, target_weight)` retorna observacao de montagem da carga quando houver equipamento fixo.
- `write_session()` escreve `session.json`.

Regras importantes:

- Indices ativos: `TRAINING_EXERCISES = range(0, 11)`.
- Progressao por RPE: RPE 7 ou menor `+4 kg`, RPE 8 `+2 kg`, RPE 9 mantem, RPE 10 ou maior `-2 kg`, sem RPE mantem.
- RPE 9 nao representa estagnacao automaticamente. Manter a carga nesse nivel
  faz parte do metodo para consolidar tecnica, amplitude, controle e qualidade
  das repeticoes. Quando a mesma carga passar a RPE 8 ou menor, o sistema
  aumenta o alvo conforme a regra de progressao.
- Analises do historico e alertas do dashboard nao devem considerar uma
  sequencia de RPE 9 um problema isolado. Ela so exige atencao quando houver
  perda tecnica, repeticoes incompletas, piora de amplitude ou ausencia
  prolongada de melhora na execucao.
- `Rosca martelo (barra H)` tem alvo inicial de 16 kg quando ainda nao houver historico proprio; depois disso usa a progressao por RPE.
- `target_weight` fica em `session.json`.
- `rest_interval` fica em `session.json` e aparece em `/gerar`, `/status` e proximo exercicio.
- `loading_note` fica em `session.json` quando houver equipamento fixo e aparece apenas no exercicio atual/proximo, nao na lista `/exercicios`.
- `Tríceps testa` e `Pullover (barra)` usam barra W de 6 kg; a observacao mostra a carga total como `barra W 6kg + Xkg de anilhas`.
- `Rosca martelo (barra H)` usa barra H de 9 kg; a observacao mostra a carga total como `barra H 9kg + Xkg de anilhas`.
- Manter `TREINO_EXERCISES` apenas como alias de compatibilidade.
- O primeiro exercicio ativo e `Agachamento Zercher` (`3x5`).

### `forja_de_ferro/db_ops.py`

Modulo SQLite para exercicios, logs de treino e dados de dieta.

- Banco versionado: `data/forja_de_ferro.db`.
- Tabela principal de exercicios: `exercises` (`name`, `sets`, `reps`, `sort_order`, `active`).
- Mudancas de catalogo que devem valer para bancos novos tambem precisam atualizar `DEFAULT_EXERCISES`.
- Mudancas que devem valer no banco atual precisam atualizar `data/forja_de_ferro.db`.

### `forja_de_ferro/dashboard.py`

Dashboard local de volume:

- `carregar_dados()` le `training_sessions` e `training_logs`.
- Volume de cada log: `sets x reps x weight`.
- Entram apenas logs com `weight IS NOT NULL` e carga maior que zero.
- O HTML mostra volume por sessao, semana, mes, exercicio e grupo muscular,
  carga, RPE, 1RM estimado, media movel, consistencia semanal, comparacao
  recente, PRs, maiores evolucoes, abas de navegacao, filtros rapidos, analises
  cruzadas de volume/RPE/carga e alertas.
- O layout do dashboard deve permanecer escuro, cru e compacto.
- `salvar_dashboard()` escreve `temp/dashboard-treino.html`.

## Estado Local E Segredos

Nao versionar:

- `session.json`
- `.env` (`TELEGRAM_TOKEN=...`)
- `data/*.db-shm`
- `data/*.db-wal`
- arquivos temporarios em `temp/`
- dashboard gerado em `temp/dashboard-treino.html`

Antes de alterar arquivos de estado local, verifique se a mudanca e realmente
necessaria.

## Catalogo Ativo

Fonte unica: tabela `exercises` em `data/forja_de_ferro.db`.

Ordem ativa atual:

1. Agachamento Zercher - 3x5
2. Supino reto (barra) - 3x5
3. Supino reto back-off - 2x8
4. Remada curvada (barra) - 3x8
5. Desenvolvimento (barra em pe) - 3x5
6. Levantamento Terra Romeno - 3x8
7. Pullover (barra) - 3x10
8. Remada alta (barra) - 3x10
9. Remada curvada alta no peito (barra) - 3x10
10. Rosca martelo (barra H) - 3x8
11. Triceps testa - 3x8

## Documentacao

A documentacao detalhada fica em `docs/index.md`.

Arquivos tecnicos principais:

- `docs/visao-geral.md`
- `docs/arquitetura.md`
- `docs/banco-de-dados.md`
- `docs/bot-telegram.md`
- `docs/testes.md`
- `docs/portabilidade.md`
- `docs/operacao.md`

Referencias cientificas e notas de treino ficam em `docs/referencias-treino/`.

## Dependencias E Execucao

Dependencias Python:

- `requests`

Biblioteca padrao usada no projeto:

- `sqlite3`
- `json`
- `datetime`
- `pathlib`
- `time`

Comandos uteis:

```bash
pip install -r requirements.txt
python tests/smoke_test.py
python tests/dashboard_test.py
python tests/e2e_training_flow_test.py
python gerar_dashboard.py
python start_bot.py
```

No Linux/macOS, use `python3` se necessario.

## Diretrizes Para Alteracoes

- Preferir mudancas cirurgicas e compativeis com o fluxo atual.
- Manter SQLite como fonte da verdade dos exercicios.
- Preservar a diferenca entre dados versionados e estado local.
- Preferir helpers existentes antes de criar novas abstracoes.
- Atualizar documentacao quando uma mudanca alterar comandos, caminhos, nomes de arquivos, catalogo ou fluxo de uso.
- Nao versionar segredos.

## Padrao De Commit

Use Conventional Commits no titulo:

```text
feat: adiciona comando de sincronizacao
```

Requisitos:

- Titulo no formato `<type>: <title>` (`feat`, `fix`, `refactor`, `docs`, etc.).
- Corpo do commit e obrigatorio.
- Corpo deve explicar contexto tecnico, escopo e motivo da decisao.
