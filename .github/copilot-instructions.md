# Instrucoes Do Copilot Para Este Repositorio

## Contexto Do Projeto

O Limulus e um diario de treino e dieta com bot do Telegram e banco SQLite local.

Banco principal: `data/limulus.db`.
Launcher multiplataforma: `start_bot.py`.
Wrapper Windows: `start_bot.bat`.
O launcher do bot deve manter saida minimalista no terminal: sem banner, ASCII
art ou mensagens cosmeticas; preservar apenas logs operacionais e erros uteis.
Dashboard local: `gerar_dashboard.py` gera `temp/dashboard-treino.html`.
Extracao de frames de video: `gerar_frames.py --todos --instalar-ffmpeg`
verifica a dependencia, processa os videos de `videos/entrada/` e grava cada
resultado em `videos/saida/<nome-do-video>/`, informando a contagem de frames.
Gestao de dados: `gerenciar_dados.py` cria backup, exporta JSON e restaura
backups validados.

Teste direto das regras: `python tests/regras_treino_test.py`.
Catalogo unico de comandos: `docs/comandos.md`.

SQLite e a fonte da verdade para exercicios, sessoes, logs de treino e dados de
dieta. Nao mover a gestao de exercicios de volta para ODS.
Ao consultar o banco em tarefas de manutencao, preferir scripts Python com o
modulo padrao `sqlite3` ou helpers de `limulus/db_ops.py`. Nao depender
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
para interface, mensagens do bot, comandos principais, ajuda, documentacao
tecnica, exemplos, titulos Markdown, nomes de arquivos e pastas novos de
documentacao, mensagens de launcher e textos visiveis ao usuario.

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

## Arquivos Principais

### `start_bot.py`

Launcher principal para iniciar o bot.
Nao imprime banner nem texto cosmetico; a saida deve ficar restrita aos logs
operacionais e erros uteis.

### `start_bot.bat`

Wrapper Windows para iniciar o bot com duplo clique ou pelo terminal.

### `gerar_dashboard.py`

Launcher local que gera o dashboard HTML de volume de treino em
`temp/dashboard-treino.html`.

### `limulus/telegram_poller.py`

Bot Telegram com long polling.

O polling usa logs com horario, nivel, comando e `session_id`, sem registrar
token ou URL completa da API. Falhas temporarias usam espera gradual; token
invalido encerra o polling com erro claro.

Comandos principais:

- `/gerar`
- `/prever`
- `/treinob`
- `/exercicios`
- `/aquecimento`
- `/volume`
- `/dashboard`
- `/planos`
- `/plano NOME`
- `/peso VALOR`
- `/peso`
- `/cintura VALOR`
- `/cintura`
- `/status`
- `/desfazer`
- `/ajuda`
- `80` ou `80 8` para registrar carga e RPE opcional
- `/fundamentos`, `/fundamentos a|b|c` (espelho + saco leve, um movimento por vez)
- `/mt`, `/mtterca`, `/mtquinta`, `/mtsabado` (semana opcional: `/mtterca 3`)
- `/proximo`, `/mtparar`, `/mtregras`
- `/tecnicas`, `/como NOME` (curto), `/como NOME tudo` (completo)

Todos os comandos textuais exigem `/`. Entradas numericas de carga e RPE nao
usam barra.
Os comandos de Muay Thai (`limulus/muaythai.py`) entregam o roteiro do
dia bloco a bloco e nao gravam nada no banco; o estado fica em
`mt_session.json`, separado de `session.json`. `/como` devolve o essencial de cada movimento e `/como NOME tudo` o passo a
passo completo, com a busca normalizando acento, espaco e alias
em `muaythai.buscar_tecnica`.
`/aquecimento` mostra uma sequencia dinamica curta de corpo todo, com cerca de
5 minutos, sem prescrever um segundo treino.

Fluxo principal:

1. `/gerar` cria uma sessao de treino no SQLite, envia a lista do treino e em
   seguida indica o primeiro exercicio a executar.
2. `ods_ops.write_session(...)` grava o estado ativo em `session.json`.
3. O texto de treino mostra `alvo`, calculado pela ultima carga registrada e pelo RPE, e `descanso`.
4. `/prever` mostra o mesmo formato sem criar sessao, logs ou `session.json`.
5. `/treinob` mostra o Treino B de garagem sem criar sessao, logs ou
   `session.json`; os pesos unicos sao calculados pelos alvos atuais do treino
   principal, sem pedir nem registrar RPE.
6. Entrada de carga atualiza diretamente o log correspondente em `data/limulus.db`.
7. `/desfazer` limpa o ultimo registro preenchido.
8. `session.json` e validado contra o SQLite ao ser carregado. Se estiver
   ausente, corrompido ou antigo, o bot reconstrui a sessao mais recente com
   logs pendentes; sessoes completas nao sao reabertas.
9. Ao registrar o ultimo exercicio, o bot envia resumo com volume, RPE medio,
   comparacao com sessao compativel, mudancas de carga, consolidacoes, cargas
   mantidas em RPE 9 e recordes.
10. `/planos` lista modelos cadastrados e `/plano NOME` seleciona o plano usado
   por `/gerar`, `/prever`, `/exercicios` e `/volume`.
11. `/dashboard` atualiza `temp/dashboard-treino.html` e responde com horario,
    ultima sessao, volume e RPE medio geral, sem expor caminho local.
12. `/peso VALOR` registra o peso corporal com data e `/peso` consulta o valor
    atual, a variacao anterior e as ultimas medicoes.
13. `/cintura VALOR` registra a circunferencia da cintura em centimetros e
    `/cintura` consulta o valor atual, a variacao e as ultimas medicoes.

### `limulus/ods_ops.py`

Camada auxiliar de sessao de treino. O nome e historico, mas o fluxo atual usa
SQLite e `session.json`.

Funcoes importantes:

- `generate_training()` cria uma sessao SQLite e retorna `(exercises, session_id)`.
- `preview_training()` monta o treino sem persistir sessao, logs ou `session.json`.
- `build_training_b()` monta o Treino B de garagem sem persistir sessao, logs ou
  `session.json`, aplicando percentuais dos alvos atuais do treino principal.
- `gerar_treino()` e alias de compatibilidade.
- `read_exercises()` le exercicios do SQLite.
- `read_previous_weights()` retorna a carga mais recente por exercicio.
- `read_previous_performance()` retorna carga e RPE mais recentes por exercicio.
- `suggest_next_weight(previous_weight, previous_rpe=None)` calcula a carga alvo pela regra de RPE.
- `get_rest_interval(exercise_name)` retorna o descanso sugerido entre series.
- `format_loading_note(exercise_name, target_weight)` retorna observacao de montagem da carga quando houver equipamento fixo.
- `write_session()` escreve `session.json`.
- `recover_active_session()` reconstrui `session.json` a partir da sessao
  SQLite mais recente que ainda possui logs pendentes.

Regras importantes:

- A sequencia ativa vem de `training_plan_exercises`; `TRAINING_EXERCISES` e
  `TREINO_EXERCISES` permanecem apenas como aliases legados.
- Treino B de garagem: farmer walk usa 45% do Terra Romeno e remada leve com
  barra usa 60% da remada curvada; o comando `/treinob` exibe peso unico
  arredondado, 10 voltas fixas,
  montagem com barra reta 2,50 m de 9 kg para remada com barra e barra de 40 cm
  para farmer walk, e nao registra RPE.
- Progressao por RPE: RPE 7 ou menor `+4 kg`, RPE 8 `+2 kg`, RPE 9 mantem, RPE 10 ou maior `-2 kg`, sem RPE mantem.
- RPE 9 nao representa estagnacao automaticamente. Manter a carga nesse nivel
  faz parte do metodo para consolidar tecnica, amplitude, controle e qualidade
  das repeticoes. Quando a mesma carga passar a RPE 8 ou menor, o sistema
  aumenta o alvo conforme a regra de progressao.
- Analises do historico e alertas do dashboard nao devem considerar uma
  sequencia de RPE 9 um problema isolado. Ela so exige atencao quando houver
  perda tecnica, repeticoes incompletas, piora de amplitude ou ausencia
  prolongada de melhora na execucao.
- `Rosca martelo (barra H)` tem alvo inicial de 16 kg e `Supino inclinado
  (barra)` tem alvo inicial de 41 kg quando ainda nao houver historico proprio;
  depois disso usam a progressao por RPE.
- `target_weight` fica em `session.json`.
- `rest_interval` fica em `session.json` e aparece em `/gerar`, `/status` e proximo exercicio.
- `Supino reto back-off` e `Supino inclinado (barra)` usam descanso de 4 min.
- `Rosca martelo (barra H)` usa descanso de 3 min.
- `loading_note` fica em `session.json` quando houver equipamento fixo e aparece apenas no exercicio atual/proximo, nao na lista `/exercicios`.
- Nomes visiveis no bot e dashboard podem usar `ods_ops.get_display_name()` para
  ocultar qualificadores como `(barra)`, `(barra H)` e `(barra em pé)`. Nao
  renomear os nomes canonicos no SQLite para isso, pois eles sao usados no
  historico e na progressao.
- `Agachamento com barra nas costas`, `Agachamento sumô com barra à frente`, os
  supinos com barra, `Remada curvada (barra)`, `Desenvolvimento (barra em pé)`,
  `Levantamento Terra Romeno` e `Remada curvada alta no peito (barra)` usam
  barra reta de 2,20 m e 11 kg; a observacao mostra a carga total como
  `barra reta 2,20 m 11kg + Xkg de anilhas`.
- `Tríceps testa` e `Pullover (barra)` usam barra W de 6 kg; a observacao mostra a carga total como `barra W 6kg + Xkg de anilhas`.
- `Rosca martelo (barra H)` usa barra H de 9 kg; a observacao mostra a carga total como `barra H 9kg + Xkg de anilhas`.
- Manter `TREINO_EXERCISES` apenas como alias de compatibilidade.
- O primeiro exercicio ativo e `Agachamento com barra nas costas` (`3x5`).
- O segundo exercicio ativo e `Agachamento sumô com barra à frente` (`3x10`),
  com foco principal nos adutores.
- Logs historicos podem permanecer com nomes antigos ou inativos, incluindo `Agachamento (barra)`, `Agachamento Zercher`, `Zercher squat`, `Pullover (barra)`, `Tríceps testa`, `Supino fechado (barra)` e `Remada alta (barra)`.

### `limulus/db_ops.py`

Modulo SQLite para exercicios, logs de treino e dados de dieta.

- Banco versionado: `data/limulus.db`.
- Versao atual do esquema: `SCHEMA_VERSION = 10`.
- `schema_migrations` registra migracoes aplicadas; `init_db()` executa
  pendencias em ordem e rejeita bancos com versao futura.
- `get_session_summary(session_id)` calcula o resumo pos-treino e usa a sessao
  anterior com a mesma sequencia de exercicios para comparar volume.
- Tabela principal de exercicios: `exercises` (`name`, `sets`, `reps`, `sort_order`, `active`).
- `exercise_muscle_groups` relaciona exercicios a grupos principais e
  secundarios. `/volume` e dashboard usam essa tabela como fonte unica.
- `training_plans` e `training_plan_exercises` armazenam modelos A/B ou outros
  ciclos. Apenas um plano com exercicios fica ativo por vez.
- `body_weights` e `waist_measurements` armazenam historicos temporais de peso
  corporal e circunferencia da cintura.
- `body_profile` armazena altura e idade em um registro unico para os calculos
  corporais do dashboard.
- No schema atual, `body_weights` usa `weight_kg` e `recorded_at`; nao assumir
  colunas `weight` ou `date`. `body_profile` usa `height_cm` e `age_years`; nao
  assumir coluna `age`.
- Mudancas de catalogo que devem valer para bancos novos tambem precisam atualizar `DEFAULT_EXERCISES`.
- Mudancas que devem valer no banco atual precisam atualizar `data/limulus.db`.

### `limulus/dashboard.py`

Dashboard local de volume:

- `carregar_dados()` le `training_sessions` e `training_logs`.
- Volume de cada log: `sets x reps x weight`.
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
  corporais, carga vs RPE, comparacoes, PRs e filtros rapidos, usam Chart.js
  carregado por CDN com versao fixa.
  Nao trocar o mapa anatomico para biblioteca de graficos; ele continua SVG
  vetorial baseado nos assets anatomicos.
- As regioes musculares sao renderizadas diretamente dos paths vetoriais de
  `body-muscles` (Apache-2.0), numa SVG unica por vista. Os SVGs anatomicos de
  Termininja (CC BY-SA 3.0) ficam preservados em `limulus/assets/`.
  Manter os ativos e os textos das licencas em `docs/licencas/`.
- Os alertas nao tratam RPE 9 repetido ou carga mantida como problema isolado.
  Queda de RPE com a mesma carga aparece como consolidacao; RPE 10 persistente
  e reducao de carga apos RPE 10 aparecem como sinais de acompanhamento.
- Alertas por exercicio consideram apenas exercicios do plano ativo atual; logs
  historicos de exercicios inativos permanecem nos graficos e PRs, mas nao
  geram alertas.
- `Maiores evolucoes` considera apenas exercicios do plano ativo atual.
- O layout do dashboard deve permanecer escuro, cru e compacto, usando IBM
  Carbon Design System oficial via Carbon Web Components. Nao copiar nem
  reinventar tokens `cds`; os componentes oficiais `cds-*` devem cuidar do tema
  quando houver componente aplicavel. O HTML gerado nao deve exigir servidor ou
  build para abrir localmente, mas pode depender da CDN oficial configurada no
  arquivo para carregar os componentes.
- `salvar_dashboard()` escreve `temp/dashboard-treino.html`.
- O bot chama a mesma funcao em `/dashboard`; o comando nao cria ou altera
  sessoes e nao envia o arquivo HTML.

### `limulus/video_ops.py`

- `extrair_frames(video_path, saida=None, fps=None, formato="jpg")` usa
  `ffmpeg` para gerar frames em uma pasta local.
- Formatos aceitos: JPG, JPEG, PNG, WebP e BMP. Arquivos existentes sao
  substituidos sem prompt interativo.
- `--todos` processa todos os videos de `videos/entrada/`; sem `--fps`, extrai
  todos os frames.
- `--instalar-ffmpeg` tenta instalar com winget, Homebrew ou apt-get.

### `limulus/backup_ops.py`

- `criar_backup()` usa a API de backup do SQLite.
- `exportar_dados()` gera JSON com versao de esquema e tabelas do projeto.
- `restaurar_backup()` valida integridade, cria backup de seguranca quando o
  destino existe e substitui o banco somente depois de concluir a copia.

## Estado Local E Segredos

Nao versionar:

- `session.json`
- `.env` (`TELEGRAM_TOKEN=...`)
- `data/*.db-shm`
- `data/*.db-wal`
- arquivos temporarios em `temp/`
- dashboard gerado em `temp/dashboard-treino.html`
- `backups/`
- `exportacoes/`

Antes de alterar arquivos de estado local, verifique se a mudanca e realmente
necessaria.

## Catalogo Ativo

Fonte unica: tabela `exercises` em `data/limulus.db`.

Ordem ativa atual:

1. Agachamento com barra nas costas - 3x5
2. Agachamento sumô com barra à frente - 3x10
3. Supino reto (barra) - 3x5
4. Supino reto back-off - 3x8
5. Supino inclinado (barra) - 3x8
6. Remada curvada (barra) - 3x8
7. Remada curvada alta no peito (barra) - 3x10
8. Desenvolvimento (barra em pe) - 3x5
9. Levantamento Terra Romeno - 3x8
10. Rosca martelo (barra H) - 3x8

`Supino fechado (barra)` e `Remada alta (barra)` estao inativos para sessoes futuras.

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
- `docs/melhorias-futuras.md`

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
python tests/regras_treino_test.py
python tests/dashboard_test.py
python tests/backup_export_test.py
python tests/telegram_falhas_test.py
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
