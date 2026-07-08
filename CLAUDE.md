# Notas Do Repositorio

A Forja de Ferro e um diario de treino com bot do Telegram e armazenamento SQLite.

Launcher do bot: `start_bot.py`, com saida minimalista no terminal. Nao adicionar
banner, ASCII art ou mensagens cosmeticas; preservar apenas logs operacionais e
erros uteis.
Dashboard local: `gerar_dashboard.py` gera `temp/dashboard-treino.html` com a
evolucao do volume de treino.
Extracao de frames de video: `gerar_frames.py --todos --instalar-ffmpeg`
verifica a dependencia, processa os videos de `videos/entrada/` e grava cada
resultado em `videos/saida/<nome-do-video>/`, informando a contagem de frames.
Gestao de dados: `gerenciar_dados.py` cria backup, exporta JSON e restaura
backups validados.
Catalogo unico de comandos: `docs/comandos.md`.

Teste direto das regras: `python tests/regras_treino_test.py`.

Ao consultar o banco em tarefas de manutencao, preferir scripts Python com o
modulo padrao `sqlite3` ou helpers de `forja_de_ferro/db_ops.py`. Nao depender
do binario externo `sqlite3`, pois ele pode nao estar disponivel no PATH local.
No schema atual, `training_sessions` usa `id`, `date` e `training_type`; nao
assumir colunas como `started_at`, `completed_at` ou `plan_name`. `training_logs`
usa `exercise_name` para o nome do exercicio, nao `exercise`, e nao possui
`logged_at`; usar `session_id`, `sort_order` e `id` para ordenar logs.
Em consultas via `python -c` no PowerShell, evitar metacaracteres como `|` dentro
da string do comando. Preferir codigo Python entre aspas simples e saida CSV ou
texto simples. Se o sandbox do Windows falhar com `CreateProcessAsUserW failed:
1312`, repetir a mesma consulta com permissao escalada em vez de trocar para o
binario `sqlite3`.
Neste ambiente Windows, esse erro de sandbox e recorrente tambem em leituras
locais com PowerShell, especialmente em caminhos do OneDrive, Area de Trabalho
ou arquivos grandes. Quando um comando necessario falhar com
`CreateProcessAsUserW failed: 1312`, repetir diretamente o mesmo comando com
permissao escalada e justificativa curta. Nao interromper o fluxo para explicar
o erro ao usuario toda vez; mencionar apenas se a permissao for negada ou se o
bloqueio impedir a tarefa.

## Memoria Operacional Do Projeto

Quando uma tarefa revelar um detalhe estavel sobre estrutura, caminhos, esquema
do banco, comandos, fluxos locais, arquivos de estado ou convencoes do projeto,
registrar essa descoberta nos arquivos de agente antes de finalizar, desde que a
informacao ajude manutencoes futuras e nao contenha segredo. Sincronizar a mesma
nota em `AGENTS.md`, `CLAUDE.md` e `.github/copilot-instructions.md` quando ela
se aplicar aos tres.

Nao depender apenas da memoria da conversa para fatos recorrentes do projeto.
Preferir consolidar no proprio repositorio onde ficam os arquivos, nomes de
tabelas, colunas, comandos e particularidades do ambiente local.

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

- `/gerar` cria uma sessao de treino, envia a lista do treino e em seguida
  indica o primeiro exercicio a executar.
- `/prever` mostra o treino em texto sem salvar sessao ou logs.
- `/exercicios` lista exercicios atuais.
- `/aquecimento` mostra o aquecimento.
- `/volume` mostra series por grupo muscular.
- `/dashboard` atualiza o dashboard local e envia resumo curto.
- `/planos` lista planos cadastrados.
- `/plano NOME` seleciona o plano ativo.
- `/peso VALOR` registra peso corporal e `/peso` consulta o historico recente.
- `/cintura VALOR` registra a circunferencia em centimetros e `/cintura`
  consulta o historico recente.
- `/status` mostra progresso da sessao ativa.
- `/desfazer` limpa o ultimo exercicio registrado.
- `/ajuda` lista comandos.
- `80` ou `80 8` registra carga e RPE opcional.
- `/aquecimento` mostra uma sequencia dinamica curta de corpo todo, com cerca
  de 5 minutos, sem prescrever um segundo treino.
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
- `Rosca martelo (barra H)` tem alvo inicial de 16 kg, `Supino inclinado
  (barra)` tem alvo inicial de 41 kg e `Supino fechado (barra)` tem alvo
  inicial de 35 kg quando ainda nao houver historico proprio; depois disso usam
  a progressao por RPE.
- `target_weight` fica em `session.json`.
- `rest_interval` fica em `session.json` e aparece em `/gerar`, `/status` e proximo exercicio.
- `loading_note` fica em `session.json` quando houver equipamento fixo e aparece apenas no exercicio atual/proximo, nao na lista `/exercicios`.
- Nomes visiveis no bot e dashboard podem usar `ods_ops.get_display_name()` para
  ocultar qualificadores como `(barra)`, `(barra H)` e `(barra em pé)`. Nao
  renomear os nomes canonicos no SQLite para isso, pois eles sao usados no
  historico e na progressao.
- `Agachamento com barra nas costas`, os supinos com barra, `Remada curvada (barra)`,
  `Desenvolvimento (barra em pé)`, `Levantamento Terra Romeno` e `Remada
  curvada alta no peito (barra)` usam barra reta de 2,20 m e 11 kg; a observacao
  mostra a carga total como `barra reta 2,20 m 11kg + Xkg de anilhas`.
- `Agachamento sumô com barra à frente` usa barra oca de 1,50 m e 1 kg; a
  observacao mostra a carga total como
  `barra oca 1,50 m 1kg + Xkg de anilhas`.
- `Tríceps testa`, `Pullover (barra)` e `Remada alta (barra)` usam barra W de 6 kg; a observacao mostra a carga total como `barra W 6kg + Xkg de anilhas`.
- `Rosca martelo (barra H)` usa barra H de 9 kg; a observacao mostra a carga total como `barra H 9kg + Xkg de anilhas`.
- Primeiro exercicio ativo: `Agachamento com barra nas costas` (`3x5`).
- Segundo exercicio ativo: `Agachamento sumô com barra à frente` (`3x10`),
  com foco principal nos adutores.
- Quinto exercicio ativo: `Supino inclinado (barra)` (`3x8`), logo depois de
  `Supino reto back-off`, substituindo `Pullover (barra)` para sessoes futuras.
- Setimo exercicio ativo: `Remada curvada alta no peito (barra)` (`3x10`),
  logo depois de `Remada curvada (barra)`.
- Decimo primeiro exercicio ativo: `Rosca martelo (barra H)` (`3x8`), substituindo `Rosca direta` para sessoes futuras.
- Decimo segundo exercicio ativo: `Supino fechado (barra)` (`3x8`), substituindo `Tríceps testa` para sessoes futuras.
- O agachamento com barra nas costas usa a barra apoiada no trapezio/ombro.
- Logs historicos podem permanecer com nomes antigos, incluindo `Agachamento (barra)`, `Agachamento Zercher`, `Zercher squat`, `Pullover (barra)` e `Tríceps testa`.

### `forja_de_ferro/db_ops.py`

Operacoes SQLite:

- `get_or_seed_exercises()`
- `list_exercises()`
- `create_session()`
- `log_exercise()`
- `update_log_weight()`
- `get_last_weights()`
- `count_filled()`
- `add_body_weight()` e `add_waist_measurement()` preservam historicos temporais.
- `body_profile` armazena altura e idade em um registro unico para os calculos
  corporais do dashboard.
- No schema atual, `body_weights` usa `weight_kg` e `recorded_at`; nao assumir
  colunas `weight` ou `date`. `body_profile` usa `height_cm` e `age_years`; nao
  assumir coluna `age`.

### `forja_de_ferro/dashboard.py`

Dashboard local de volume:

- `carregar_dados()` le sessoes e logs do SQLite.
- Volume de cada registro: `sets x reps x weight`.
- Entram apenas logs com `weight IS NOT NULL` e carga maior que zero.
- O HTML exibe uma pagina unica rolavel com indicadores de resumo, treino ativo
  do plano selecionado, grafico de evolucao do volume, mapa muscular anterior e posterior da ultima sessao,
  carga e RPE e 1RM estimado por exercicio, comparacao da ultima sessao com a
  anterior, equilibrio muscular, calendario de carga, grupos musculares, volume
  semanal, maiores evolucoes, recordes pessoais, PRs expandidos, carga vs RPE,
  alertas, filtros rapidos por segmento, relatorio semanal, peso corporal,
  cintura atual, IMC, relacao cintura/altura e dieta atual no final da pagina.
- IMC e relacao cintura/altura usam as medicoes mais recentes e sao
  indicadores derivados, nao diagnosticos.
- Os cards corporais mostram metas de referencia: IMC de 18,5 a 24,9,
  cintura/altura abaixo de 0,50 e limites de peso e cintura derivados da altura.
- Cada card com meta mostra uma barra de proximidade calculada como
  `limite da meta / valor atual`, limitada a 100%.
- Os quatro cards corporais mostram minigraficos de linha. Peso e IMC usam o
  historico de peso; cintura e cintura/altura usam o historico de cintura.
- A secao de dieta le `diet_entries`, `foods` e `diet_targets`, mostra uma lista
  unica de alimentos, consolida itens repetidos e compara os totais diarios de
  macros com as metas. Os micros aparecem em uma segunda linha de cards e na
  tabela por alimento e no total: fibra, omega 3, potassio, magnesio, zinco e
  vitaminas D e B6.
- O mapa muscular usa `exercise_muscle_groups`, expande grupos amplos em
  segmentos anatomicos visuais; regioes sem volume ficam transparentes e o
  vermelho ganha opacidade conforme o volume relativo. O dashboard usa pesos por
  exercicio quando houver regra especifica; a visualizacao nao representa
  ativacao muscular medida.
- Graficos de dados do dashboard, como evolucao de volume, minigraficos
  corporais e carga vs RPE, usam Chart.js carregado por CDN com versao fixa.
  Nao trocar o mapa anatomico para biblioteca de graficos; ele continua SVG
  vetorial baseado nos assets anatomicos.
- As regioes musculares sao renderizadas diretamente dos paths vetoriais de
  `body-muscles` (Apache-2.0), numa SVG unica por vista. Os SVGs anatomicos de
  Termininja (CC BY-SA 3.0) ficam preservados em `forja_de_ferro/assets/`.
  Manter os ativos e os textos das licencas em `docs/licencas/`.
- Os alertas nao tratam RPE 9 repetido ou carga mantida como problema isolado.
  Queda de RPE com a mesma carga aparece como consolidacao; RPE 10 persistente
  e reducao de carga apos RPE 10 aparecem como sinais de acompanhamento.
- O layout do dashboard deve permanecer escuro, cru e compacto, usando IBM
  Carbon Design System oficial via Carbon Web Components. Nao copiar nem
  reinventar tokens `cds`; os componentes oficiais `cds-*` devem cuidar do tema
  quando houver componente aplicavel. O HTML gerado nao deve exigir servidor ou
  build para abrir localmente, mas pode depender da CDN oficial configurada no
  arquivo para carregar os componentes.
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
- Versao atual do esquema: `SCHEMA_VERSION = 10`.
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
