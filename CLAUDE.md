# Notas Do Repositorio

IronForge e um diario de treino com bot do Telegram e armazenamento SQLite.

Dashboard local: `gerar_dashboard.py` gera `temp/dashboard-treino.html` com a
evolucao do volume de treino.

## Padrao De Idioma

O projeto deve ser o mais PT-BR possivel. Use portugues brasileiro como padrao
para interface, mensagens do bot, comandos principais, documentacao de uso,
documentacao tecnica, titulos de Markdown, exemplos, nomes de arquivos e pastas
novos de documentacao, mensagens de launcher e textos visiveis ao usuario.

Evite criar novos nomes ou textos em ingles quando houver uma alternativa natural
em PT-BR. Aliases legados em ingles podem permanecer por compatibilidade, mas a
ajuda principal, os exemplos e a documentacao devem priorizar os nomes em PT-BR.

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

## Modulos Principais

Os modulos de runtime ficam no pacote `ironforge/`. Importe codigo de aplicacao
com `from ironforge import db_ops`, `ods_ops` ou `telegram_poller`.

### `ironforge/telegram_poller.py`

Bot Telegram com long polling.

Comandos principais em PT-BR:

- `/gerar` cria uma sessao de treino e envia o treino em texto.
- `/prever` mostra o treino em texto sem salvar sessao ou logs.
- `/exercicios` lista exercicios atuais.
- `/aquecimento` mostra o aquecimento.
- `/volume` mostra series por grupo muscular.
- `/status` mostra progresso da sessao ativa.
- `/desfazer` limpa o ultimo exercicio registrado.
- `/ajuda` lista comandos.
- `80` ou `80 8` registra carga e RPE opcional.
- O texto de `/gerar` mostra `alvo`, calculado pela ultima carga do exercicio e pelo RPE, e `descanso`.

Aliases antigos em ingles podem permanecer para compatibilidade.

### `ironforge/ods_ops.py`

Helpers de operacao de treino:

- `generate_training()` cria sessao e linhas de treino no SQLite.
- `preview_training()` monta o treino sem persistir sessao, logs ou `session.json`.
- `gerar_treino()` permanece como alias de compatibilidade.
- `read_exercises()` le exercicios do SQLite.
- `read_previous_weights()` retorna cargas recentes do SQLite.
- `read_previous_performance()` retorna carga e RPE recentes do SQLite.
- `suggest_next_weight(previous_weight, previous_rpe=None)` calcula a carga alvo pela regra de RPE.
- `get_rest_interval(exercise_name)` retorna o descanso sugerido entre series.
- `write_session()` escreve estado ativo em `session.json`.

Catalogo atual:

- Indices ativos: `TRAINING_EXERCISES = range(0, 11)`.
- Progressao por RPE: RPE 7 ou menor `+4 kg`, RPE 8 `+2 kg`, RPE 9 mantem, RPE 10 ou maior `-2 kg`, sem RPE mantem.
- `target_weight` fica em `session.json`.
- `rest_interval` fica em `session.json` e aparece em `/gerar`, `/status` e proximo exercicio.
- Primeiro exercicio ativo: `Agachamento Zercher` (`3x5`).
- Substitui o agachamento com barra para sessoes futuras por falta de rack adequado.
- Logs historicos podem permanecer com nomes antigos.

### `ironforge/db_ops.py`

Operacoes SQLite:

- `get_or_seed_exercises()`
- `list_exercises()`
- `create_session()`
- `log_exercise()`
- `update_log_weight()`
- `get_last_weights()`
- `count_filled()`

### `ironforge/dashboard.py`

Dashboard local de volume:

- `carregar_dados()` le sessoes e logs do SQLite.
- Volume de cada registro: `sets x reps x weight`.
- Entram apenas logs com `weight IS NOT NULL` e carga maior que zero.
- `salvar_dashboard()` escreve `temp/dashboard-treino.html`.
- Launcher local: `python gerar_dashboard.py`.

## Dados E Estado

- Banco versionado: `data/ironforge.db`.
- Estado local: `session.json`, nao versionado.
- Configuracao secreta: `.env`, nao versionada.
- Sidecars SQLite (`*.db-shm`, `*.db-wal`) nao sao versionados.
- Dashboard gerado em `temp/dashboard-treino.html` nao e versionado.

SQLite e a fonte da verdade dos exercicios. Nao mover a gestao de exercicios de volta para ODS.
Mudancas de catalogo devem sincronizar `data/ironforge.db` e `ironforge/db_ops.py`
quando tambem precisarem valer para bancos novos.

## Estilo De Commit

Use Conventional Commits:

```text
feat: add sync command

Explique contexto tecnico, escopo e motivo da mudanca.
```
