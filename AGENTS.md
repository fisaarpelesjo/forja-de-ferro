# Instrucoes Do Codex Para Este Repositorio

## Contexto Do Projeto

Este projeto e um diario de treino com bot do Telegram e banco SQLite versionado.

Banco principal: `data/forja_de_ferro.db`.
Launcher multiplataforma: `start_bot.py`.
Wrapper Windows: `start_bot.bat`.
Dashboard local: `gerar_dashboard.py` gera `temp/dashboard-treino.html`.
Extracao de frames de video: `gerar_frames.py --todos --instalar-ffmpeg`
verifica a dependencia, processa os videos de `videos/entrada/` e grava cada
resultado em `videos/saida/<nome-do-video>/`, informando a contagem de frames.
Gestao de dados: `gerenciar_dados.py` cria backup, exporta JSON e restaura
backups validados.

Teste direto das regras: `python tests/regras_treino_test.py`.
Catalogo unico de comandos: `docs/comandos.md`.

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

Comandos textuais do Telegram devem usar somente os nomes oficiais em PT-BR e
sempre exigir `/`. Nao aceitar aliases em ingles ou nomes sem barra.

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

O polling usa logs com horario, nivel, comando e `session_id`, sem registrar
token ou URL completa da API. Falhas temporarias usam espera gradual; token
invalido encerra o polling com erro claro.

Comandos principais:

- `/gerar`
- `/prever`
- `/exercicios`
- `/aquecimento`
- `/volume`
- `/dashboard`
- `/planos`
- `/plano NOME`
- `/status`
- `/desfazer`
- `/ajuda`
- `80` ou `80 8` para registrar carga e RPE opcional

Todos os comandos textuais exigem `/`. Entradas numericas de carga e RPE nao
usam barra.

Fluxo:

1. `/gerar` cria uma sessao de treino no SQLite e reseta o arquivo de sessao ativa.
2. O texto gerado mostra `alvo`, calculado pela ultima carga registrada e pelo RPE, e `descanso`.
3. `/prever` mostra o mesmo formato sem criar sessao, logs ou `session.json`.
4. Entrada de carga e escrita diretamente no SQLite.
5. `/desfazer` limpa o ultimo exercicio registrado.
6. `session.json` e validado contra o SQLite ao ser carregado. Se estiver
   ausente, corrompido ou antigo, o bot reconstrui a sessao mais recente com
   logs pendentes; sessoes completas nao sao reabertas.
7. Ao registrar o ultimo exercicio, o bot envia resumo com volume, RPE medio,
   comparacao com sessao compativel, mudancas de carga, consolidacoes, cargas
   mantidas em RPE 9 e recordes.
8. `/planos` lista modelos cadastrados e `/plano NOME` seleciona o plano usado
   por `/gerar`, `/prever`, `/exercicios` e `/volume`.
9. `/dashboard` atualiza `temp/dashboard-treino.html` e responde com horario,
   ultima sessao, volume e RPE medio geral, sem expor caminho local.

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

- A sequencia ativa vem de `training_plan_exercises`; `TRAINING_EXERCISES` e
  `TREINO_EXERCISES` permanecem apenas como aliases legados.
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
- `Tríceps testa`, `Pullover (barra)` e `Remada alta (barra)` usam barra W de 6 kg; a observacao deve mostrar carga total como `barra W 6kg + Xkg de anilhas`.
- `Rosca martelo (barra H)` usa barra H de 9 kg; a observacao deve mostrar carga total como `barra H 9kg + Xkg de anilhas`.
- Manter `TREINO_EXERCISES` apenas como alias de compatibilidade.
- O primeiro exercicio ativo e `Agachamento Zercher` (`3x5`).
- O decimo exercicio ativo e `Rosca martelo (barra H)` (`3x8`), substituindo `Rosca direta` para sessoes futuras.
- Logs historicos de `Agachamento (barra)` ou `Zercher squat` podem permanecer como historico.

### `forja_de_ferro/db_ops.py`

Modulo SQLite para exercicios, logs de treino e dados de dieta.

- Banco versionado: `data/forja_de_ferro.db`.
- Versao atual do esquema: `SCHEMA_VERSION = 4`.
- `schema_migrations` registra cada migracao aplicada. `init_db()` executa
  migracoes pendentes em ordem e rejeita bancos com versao futura.
- `get_session_summary(session_id)` calcula o resumo pos-treino e usa a sessao
  anterior com a mesma sequencia de exercicios para comparar volume.
- Tabela principal de exercicios: `exercises` (`name`, `sets`, `reps`, `sort_order`, `active`).
- `exercise_muscle_groups` relaciona exercicios a grupos principais e
  secundarios. `/volume` e dashboard usam essa tabela como fonte unica.
- `training_plans` e `training_plan_exercises` armazenam modelos A/B ou outros
  ciclos. Apenas um plano com exercicios fica ativo por vez.
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
  rapidos, analises cruzadas de volume/RPE/carga, mapa muscular anterior e
  posterior da ultima sessao e alertas.
- O mapa muscular usa `exercise_muscle_groups`, deixa regioes sem treino
  transparentes e aumenta a opacidade vermelha conforme o volume relativo da
  ultima sessao. Ele representa volume atribuido, nao ativacao muscular medida.
- As regioes musculares sao renderizadas diretamente dos paths vetoriais de
  `body-muscles` (Apache-2.0), numa SVG unica por vista. Os SVGs anatomicos de
  Termininja (CC BY-SA 3.0) ficam preservados em `forja_de_ferro/assets/`.
  Manter os ativos e os textos das licencas em `docs/licencas/`.
- Os alertas nao tratam RPE 9 repetido ou carga mantida como problema isolado.
  Queda de RPE com a mesma carga aparece como consolidacao; RPE 10 persistente
  e reducao de carga apos RPE 10 aparecem como sinais de acompanhamento.
- O layout do dashboard deve permanecer escuro, cru e compacto.
- `salvar_dashboard()` escreve `temp/dashboard-treino.html`.
- `gerar_dashboard.py` e o launcher de uso local.
- O bot chama a mesma funcao em `/dashboard`; o comando nao cria ou altera
  sessoes e nao envia o arquivo HTML.

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
- `exportar_dados()` gera JSON com versao de esquema e tabelas do projeto.
- `restaurar_backup()` valida integridade, cria backup de seguranca quando o
  destino existe e substitui o banco somente depois de concluir a copia.

## Estado Local

Arquivos locais e secretos nao sao versionados:

- `session.json`
- `.env` (`TELEGRAM_TOKEN=...`)

Arquivos auxiliares SQLite nao sao versionados:

- `data/*.db-shm`
- `data/*.db-wal`
- `temp/dashboard-treino.html`
- `backups/`
- `exportacoes/`

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
