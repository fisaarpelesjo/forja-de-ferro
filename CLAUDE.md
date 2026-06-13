# Notas Do Repositorio

A Forja de Ferro e um diario de treino com bot do Telegram e armazenamento SQLite.

Dashboard local: `gerar_dashboard.py` gera `temp/dashboard-treino.html` com a
evolucao do volume de treino.
Extracao de frames de video: `gerar_frames.py --todos --instalar-ffmpeg`
verifica a dependencia, processa os videos de `videos/entrada/` e grava cada
resultado em `videos/saida/<nome-do-video>/`, informando a contagem de frames.
Gestao de dados: `gerenciar_dados.py` cria backup, exporta JSON e restaura
backups validados.
Catalogo unico de comandos: `docs/comandos.md`.

Teste direto das regras: `python tests/regras_treino_test.py`.

## Padrao De Idioma

O projeto deve ser o mais PT-BR possivel. Use portugues brasileiro como padrao
para interface, mensagens do bot, comandos principais, documentacao de uso,
documentacao tecnica, titulos de Markdown, exemplos, nomes de arquivos e pastas
novos de documentacao, mensagens de launcher e textos visiveis ao usuario.

Evite criar novos nomes ou textos em ingles quando houver uma alternativa
natural em PT-BR. Comandos textuais do Telegram devem usar somente os nomes
oficiais em portugues e sempre exigir `/`.

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

O roadmap tecnico fica em `docs/melhorias-futuras.md`. Consultar esse documento
antes de iniciar melhorias amplas e atualiza-lo quando um item for entregue,
descartado ou repriorizado.

## Modulos Principais

Os modulos de runtime ficam no pacote `forja_de_ferro/`. Importe codigo de aplicacao
com `from forja_de_ferro import db_ops`, `ods_ops` ou `telegram_poller`.

### `forja_de_ferro/telegram_poller.py`

Bot Telegram com long polling.

O polling usa logs com horario, nivel, comando e `session_id`, sem registrar
token ou URL completa da API. Falhas temporarias usam espera gradual; token
invalido encerra o polling com erro claro.

Comandos principais em PT-BR:

- `/gerar` cria uma sessao de treino e envia o treino em texto.
- `/prever` mostra o treino em texto sem salvar sessao ou logs.
- `/exercicios` lista exercicios atuais.
- `/aquecimento` mostra o aquecimento.
- `/volume` mostra series por grupo muscular.
- `/dashboard` atualiza o dashboard local e envia resumo curto.
- `/planos` lista planos cadastrados.
- `/plano NOME` seleciona o plano ativo.
- `/status` mostra progresso da sessao ativa.
- `/desfazer` limpa o ultimo exercicio registrado.
- `/ajuda` lista comandos.
- `80` ou `80 8` registra carga e RPE opcional.
- O texto de `/gerar` mostra `alvo`, calculado pela ultima carga do exercicio e pelo RPE, e `descanso`.
- Ao carregar, `session.json` e validado contra o SQLite. Arquivo ausente,
  corrompido ou antigo e reconstruido pela sessao mais recente com logs
  pendentes; sessoes completas nao sao reabertas.
- O ultimo registro da sessao gera resumo automatico com volume, RPE medio,
  comparacao compativel, mudancas de carga, consolidacoes, cargas mantidas em
  RPE 9 e recordes.
- `/gerar`, `/prever`, `/exercicios` e `/volume` usam o plano ativo no SQLite.
- `/dashboard` reutiliza `dashboard.salvar_dashboard()`, nao altera sessoes e
  nao expoe caminho local.

Aliases em ingles e comandos textuais sem `/` nao sao aceitos. Entradas
numericas de carga e RPE continuam sem barra.

### `forja_de_ferro/ods_ops.py`

Helpers de operacao de treino:

- `generate_training()` cria sessao e linhas de treino no SQLite.
- `preview_training()` monta o treino sem persistir sessao, logs ou `session.json`.
- `gerar_treino()` permanece como alias de compatibilidade.
- `read_exercises()` le exercicios do SQLite.
- `read_previous_weights()` retorna cargas recentes do SQLite.
- `read_previous_performance()` retorna carga e RPE recentes do SQLite.
- `suggest_next_weight(previous_weight, previous_rpe=None)` calcula a carga alvo pela regra de RPE.
- `get_rest_interval(exercise_name)` retorna o descanso sugerido entre series.
- `format_loading_note(exercise_name, target_weight)` retorna observacao de montagem da carga quando houver equipamento fixo.
- `write_session()` escreve estado ativo em `session.json`.
- `recover_active_session()` reconstrui o cache local pela sessao SQLite mais
  recente que ainda possui logs pendentes.

Catalogo atual:

- A sequencia ativa vem de `training_plan_exercises`; `TRAINING_EXERCISES` e
  `TREINO_EXERCISES` permanecem apenas como aliases legados.
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
- `Tríceps testa`, `Pullover (barra)` e `Remada alta (barra)` usam barra W de 6 kg; a observacao mostra a carga total como `barra W 6kg + Xkg de anilhas`.
- `Rosca martelo (barra H)` usa barra H de 9 kg; a observacao mostra a carga total como `barra H 9kg + Xkg de anilhas`.
- Primeiro exercicio ativo: `Agachamento Zercher` (`3x5`).
- Segundo exercicio ativo: `Agachamento sumô com barra à frente` (`3x10`),
  com foco principal nos adutores.
- Decimo primeiro exercicio ativo: `Rosca martelo (barra H)` (`3x8`), substituindo `Rosca direta` para sessoes futuras.
- Substitui o agachamento com barra para sessoes futuras por falta de rack adequado.
- Logs historicos podem permanecer com nomes antigos.

### `forja_de_ferro/db_ops.py`

Operacoes SQLite:

- `get_or_seed_exercises()`
- `list_exercises()`
- `create_session()`
- `log_exercise()`
- `update_log_weight()`
- `get_last_weights()`
- `count_filled()`

### `forja_de_ferro/dashboard.py`

Dashboard local de volume:

- `carregar_dados()` le sessoes e logs do SQLite.
- Volume de cada registro: `sets x reps x weight`.
- Entram apenas logs com `weight IS NOT NULL` e carga maior que zero.
- O HTML exibe uma pagina unica rolavel com indicadores de resumo, grafico de
  evolucao do volume, mapa muscular anterior e posterior da ultima sessao,
  carga e RPE e 1RM estimado por exercicio, comparacao da ultima sessao com a
  anterior, grupos musculares, volume semanal, maiores evolucoes, recordes
  pessoais, alertas e filtros rapidos.
- O mapa muscular usa `exercise_muscle_groups`; regioes sem volume ficam
  transparentes e o vermelho ganha opacidade conforme o volume relativo. A
  visualizacao nao representa ativacao muscular medida.
- As regioes musculares sao renderizadas diretamente dos paths vetoriais de
  `body-muscles` (Apache-2.0), numa SVG unica por vista. Os SVGs anatomicos de
  Termininja (CC BY-SA 3.0) ficam preservados em `forja_de_ferro/assets/`.
  Manter os ativos e os textos das licencas em `docs/licencas/`.
- Os alertas nao tratam RPE 9 repetido ou carga mantida como problema isolado.
  Queda de RPE com a mesma carga aparece como consolidacao; RPE 10 persistente
  e reducao de carga apos RPE 10 aparecem como sinais de acompanhamento.
- O layout do dashboard deve permanecer escuro, cru e compacto.
- `salvar_dashboard()` escreve `temp/dashboard-treino.html`.
- Launcher local: `python gerar_dashboard.py`.
- O bot usa a mesma funcao no comando `/dashboard`.

### `forja_de_ferro/video_ops.py`

- `extrair_frames(video_path, saida=None, fps=None, formato="jpg")` usa
  `ffmpeg` para gerar frames em uma pasta local.
- Formatos aceitos: JPG, JPEG, PNG, WebP e BMP. Arquivos existentes sao
  substituidos sem prompt interativo.
- `--todos` processa todos os videos de `videos/entrada/`; sem `--fps`, extrai
  todos os frames.
- `--instalar-ffmpeg` tenta instalar com winget, Homebrew ou apt-get.

### `forja_de_ferro/backup_ops.py`

- `criar_backup()` usa a API de backup do SQLite.
- `exportar_dados()` gera JSON com a versao do esquema e as tabelas do projeto.
- `restaurar_backup()` valida integridade, cria backup de seguranca quando o
  destino existe e substitui o banco somente depois da copia.

## Dados E Estado

- Banco versionado: `data/forja_de_ferro.db`.
- Versao atual do esquema: `SCHEMA_VERSION = 5`.
- `schema_migrations` registra migracoes aplicadas; `init_db()` executa
  pendencias em ordem e rejeita bancos com versao futura.
- `get_session_summary(session_id)` calcula o resumo pos-treino e compara volume
  apenas com sessao anterior que tenha a mesma sequencia de exercicios.
- Estado local: `session.json`, nao versionado.
- Configuracao secreta: `.env`, nao versionada.
- Sidecars SQLite (`*.db-shm`, `*.db-wal`) nao sao versionados.
- Dashboard gerado em `temp/dashboard-treino.html` nao e versionado.
- `backups/` e `exportacoes/` nao sao versionados.

SQLite e a fonte da verdade dos exercicios. Nao mover a gestao de exercicios de volta para ODS.
`exercise_muscle_groups` e a fonte da classificacao muscular usada pelo bot e
pelo dashboard.
`training_plans` e `training_plan_exercises` armazenam modelos A/B; apenas um
plano nao vazio fica ativo por vez.
Mudancas de catalogo devem sincronizar `data/forja_de_ferro.db` e `forja_de_ferro/db_ops.py`
quando tambem precisarem valer para bancos novos.

## Estilo De Commit

Use Conventional Commits:

```text
feat: add sync command

Explique contexto tecnico, escopo e motivo da mudanca.
```
