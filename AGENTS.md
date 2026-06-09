# Instrucoes Do Codex Para Este Repositorio

## Contexto Do Projeto

Este projeto e um diario de treino com bot do Telegram e banco SQLite versionado.

Banco principal: `data/forja_de_ferro.db`.
Launcher multiplataforma: `start_bot.py`.
Wrapper Windows: `start_bot.bat`.
Dashboard local: `gerar_dashboard.py` gera `temp/dashboard-treino.html`.

Teste direto das regras: `python tests/regras_treino_test.py`.

## Padrao De Idioma

O projeto deve ser o mais PT-BR possivel. Use portugues brasileiro como padrao
para tudo que for criado ou alterado, especialmente:

- comandos do Telegram
- mensagens do bot
- ajuda principal do bot
- documentacao de uso
- documentacao tecnica
- titulos e secoes de Markdown
- nomes de arquivos e pastas novos, quando forem parte da documentacao
- mensagens dos launchers
- comentarios novos, quando comentarios forem necessarios
- textos futuros visiveis ao usuario

Evitar criar novos nomes, textos ou caminhos em ingles quando houver uma opcao
natural em PT-BR. Termos tecnicos muito estabelecidos podem aparecer quando
ajudarem a clareza, mas devem ser acompanhados de contexto em portugues sempre
que forem visiveis ao usuario ou na documentacao.

Aliases antigos em ingles podem continuar existindo para compatibilidade, mas a
documentacao, a ajuda principal e os exemplos devem priorizar os comandos e nomes
em PT-BR.

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
a partir desse pacote, por exemplo `from forja_de_ferro import db_ops`.

### `forja_de_ferro/telegram_poller.py`

Bot Telegram usado para controlar o treino pelo celular.

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

Aliases legados em ingles podem ser aceitos:

- `/generate`
- `/exercises`
- `/warmup`
- `/undo`
- `/help`

Fluxo:

1. `/gerar` cria uma sessao de treino no SQLite e reseta o arquivo de sessao ativa.
2. O texto gerado mostra `alvo`, calculado pela ultima carga registrada e pelo RPE, e `descanso`.
3. `/prever` mostra o mesmo formato sem criar sessao, logs ou `session.json`.
4. Entrada de carga e escrita diretamente no SQLite.
5. `/desfazer` limpa o ultimo exercicio registrado.
6. `session.json` e validado contra o SQLite ao ser carregado. Se estiver
   ausente, corrompido ou antigo, o bot reconstrui a sessao mais recente com
   logs pendentes; sessoes completas nao sao reabertas.

### `forja_de_ferro/ods_ops.py`

Camada auxiliar de sessao de treino.

Funcoes importantes:

- `generate_training()` cria uma sessao SQLite e retorna `(exercises, session_id)`.
- `preview_training()` monta o treino sem persistir sessao, logs ou `session.json`.
- `gerar_treino()` e alias de compatibilidade para scripts locais antigos.
- `read_exercises()` le do SQLite.
- `read_previous_weights()` retorna a carga mais recente por exercicio.
- `read_previous_performance()` retorna carga e RPE mais recentes por exercicio.
- `suggest_next_weight(previous_weight, previous_rpe=None)` calcula o alvo pela regra de RPE.
- `get_rest_interval(exercise_name)` retorna o descanso sugerido entre series.
- `format_loading_note(exercise_name, target_weight)` retorna observacao de montagem da carga quando houver equipamento fixo.
- `write_session()` escreve `session.json`.
- `recover_active_session()` reconstrui `session.json` a partir da sessao
  SQLite mais recente que ainda possui logs pendentes.

Regras importantes:

- Indices ativos: `TRAINING_EXERCISES = range(0, 11)`.
- Progressao por RPE: RPE 7 ou menor `+4 kg`, RPE 8 `+2 kg`, RPE 9 mantem, RPE 10 ou maior `-2 kg`, sem RPE mantem.
- RPE 9 nao representa estagnacao automaticamente. Nesse nivel, manter a carga
  faz parte do metodo para consolidar tecnica, amplitude, controle e qualidade
  das repeticoes. Quando a mesma carga passar a ser registrada como RPE 8 ou
  menor, o sistema aumenta o alvo conforme a regra de progressao.
- Avaliacoes do historico e alertas do dashboard nao devem tratar uma sequencia
  de RPE 9 como problema isolado. Ela so exige atencao quando vier acompanhada
  de perda tecnica, repeticoes incompletas, piora de amplitude ou ausencia
  prolongada de qualquer melhora na execucao.
- `Rosca martelo (barra H)` tem alvo inicial de 16 kg quando ainda nao houver historico proprio; depois disso usa a progressao por RPE.
- `target_weight` fica em `session.json`.
- `rest_interval` fica em `session.json` e aparece em `/gerar`, `/status` e proximo exercicio.
- `loading_note` fica em `session.json` quando houver equipamento fixo e aparece apenas no exercicio atual/proximo, nao na lista `/exercicios`.
- `Tríceps testa` e `Pullover (barra)` usam barra W de 6 kg; a observacao deve mostrar carga total como `barra W 6kg + Xkg de anilhas`.
- `Rosca martelo (barra H)` usa barra H de 9 kg; a observacao deve mostrar carga total como `barra H 9kg + Xkg de anilhas`.
- Manter `TREINO_EXERCISES` apenas como alias de compatibilidade.
- O primeiro exercicio ativo e `Agachamento Zercher` (`3x5`).
- O decimo exercicio ativo e `Rosca martelo (barra H)` (`3x8`), substituindo `Rosca direta` para sessoes futuras.
- Logs historicos de `Agachamento (barra)` ou `Zercher squat` podem permanecer como historico.

### `forja_de_ferro/db_ops.py`

Modulo SQLite para exercicios, logs de treino e dados de dieta.

- Banco versionado: `data/forja_de_ferro.db`.
- Tabela principal de exercicios: `exercises` (`name`, `sets`, `reps`, `sort_order`, `active`).
- SQLite e a fonte da verdade para exercicios.
- Mudancas de catalogo que devem valer para bancos novos tambem precisam atualizar `DEFAULT_EXERCISES`.

### `forja_de_ferro/dashboard.py`

Dashboard local de volume de treino.

- `carregar_dados()` le `training_sessions` e `training_logs` no SQLite.
- O volume de cada linha e calculado como `sets x reps x weight`.
- Apenas logs com carga preenchida (`weight IS NOT NULL` e maior que zero) entram no dashboard.
- O HTML mostra volume por sessao, semana, mes, exercicio e grupo muscular,
  alem de carga, RPE, 1RM estimado, media movel, consistencia semanal,
  comparacao recente, PRs, maiores evolucoes, abas de navegacao, filtros
  rapidos, analises cruzadas de volume/RPE/carga e alertas.
- Os alertas nao tratam RPE 9 repetido ou carga mantida como problema isolado.
  Queda de RPE com a mesma carga aparece como consolidacao; RPE 10 persistente
  e reducao de carga apos RPE 10 aparecem como sinais de acompanhamento.
- O layout do dashboard deve permanecer escuro, cru e compacto.
- `salvar_dashboard()` escreve `temp/dashboard-treino.html`.
- `gerar_dashboard.py` e o launcher de uso local.

## Estado Local

Arquivos locais e secretos nao sao versionados:

- `session.json`
- `.env` (`TELEGRAM_TOKEN=...`)

Arquivos auxiliares SQLite nao sao versionados:

- `data/*.db-shm`
- `data/*.db-wal`
- `temp/dashboard-treino.html`

Nao versionar segredos. Antes de alterar arquivos de estado local, verificar se a mudanca e necessaria.

## Diretrizes De Mudanca

- Preferir mudancas cirurgicas compativeis com o fluxo atual.
- Manter SQLite como fonte da verdade dos exercicios.
- Preservar a diferenca entre estado local e dados versionados.
- Preferir helpers existentes antes de criar novas abstracoes.

## Padrao De Commit

Usar Conventional Commits no titulo:

`feat: add sync command`

Requisitos:

- Titulo no formato `<type>: <title>` (`feat`, `fix`, `refactor`, `docs`, etc.).
- Corpo do commit e obrigatorio.
- Corpo deve explicar contexto tecnico, escopo e motivo da decisao.
