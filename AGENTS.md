# Instrucoes Do Codex Para Este Repositorio

## Contexto Do Projeto

Este projeto e um diario de treino com bot do Telegram e banco SQLite versionado.

Banco principal: `data/forja_de_ferro.db`.
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
- `/fundamentos`, `/fundamentos a|b|c` (fase sem equipamento algum, um movimento por vez)
- `/mt`, `/mtterca`, `/mtquinta`, `/mtsabado` (semana opcional: `/mtterca 3`)
- `/proximo`, `/mtparar`, `/mtregras`
- `/tecnicas`, `/como NOME` (ex.: `/como chute baixo`, `/como bandagem`)

Todos os comandos textuais exigem `/`. Entradas numericas de carga e RPE nao
usam barra.
Os comandos de Muay Thai entregam o roteiro do dia bloco a bloco e nao gravam
nada no banco; `/como` devolve posicao inicial, execucao numerada, o que gira/quanto/quando,
retorno, checagem e erros de cada golpe, com a busca normalizando acento, espaco e alias em `muaythai.buscar_tecnica`.
`/aquecimento` mostra uma sequencia dinamica curta de corpo todo, com cerca de
5 minutos, sem prescrever um segundo treino.

Fluxo:

1. `/gerar` cria uma sessao de treino no SQLite, reseta o arquivo de sessao
   ativa, envia a lista do treino e em seguida indica o primeiro exercicio a
   executar.
2. O texto gerado mostra `alvo`, calculado pela ultima carga registrada e pelo RPE, e `descanso`.
3. `/prever` mostra o mesmo formato sem criar sessao, logs ou `session.json`.
4. `/treinob` mostra um Treino B de garagem sem criar sessao, logs ou
   `session.json`; os pesos unicos sao calculados pelos alvos atuais do treino
   principal, sem pedir nem registrar RPE.
5. Entrada de carga e escrita diretamente no SQLite.
6. `/desfazer` limpa o ultimo exercicio registrado.
7. `session.json` e validado contra o SQLite ao ser carregado. Se estiver
   ausente, corrompido ou antigo, o bot reconstrui a sessao mais recente com
   logs pendentes; sessoes completas nao sao reabertas.
8. Ao registrar o ultimo exercicio, o bot envia resumo com volume, RPE medio,
   comparacao com sessao compativel, mudancas de carga, consolidacoes, cargas
   mantidas em RPE 9 e recordes.
9. `/planos` lista modelos cadastrados e `/plano NOME` seleciona o plano usado
   por `/gerar`, `/prever`, `/exercicios` e `/volume`.
10. `/dashboard` atualiza `temp/dashboard-treino.html` e responde com horario,
   ultima sessao, volume e RPE medio geral, sem expor caminho local.
11. `/peso VALOR` registra o peso corporal com data e `/peso` consulta o valor
    atual, a variacao anterior e as ultimas medicoes.
12. `/cintura VALOR` registra a circunferencia da cintura em centimetros e
    `/cintura` consulta o valor atual, a variacao e as ultimas medicoes.

### `forja_de_ferro/ods_ops.py`

Camada auxiliar de sessao de treino.

Funcoes importantes:

- `generate_training()` cria uma sessao SQLite e retorna `(exercises, session_id)`.
- `preview_training()` monta o treino sem persistir sessao, logs ou `session.json`.
- `build_training_b()` monta o Treino B de garagem sem persistir sessao, logs ou
  `session.json`, aplicando percentuais dos alvos atuais do treino principal.
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
- Treino B de garagem: farmer walk usa 45% do Terra Romeno e remada leve com
  barra usa 60% da remada curvada; o comando `/treinob` exibe peso unico
  arredondado, 10 voltas fixas,
  montagem com barra reta 2,50 m de 9 kg para remada com barra e barra de 40 cm
  para farmer walk, e nao registra RPE.
- RPE 9 nao representa estagnacao automaticamente. Nesse nivel, manter a carga
  faz parte do metodo para consolidar tecnica, amplitude, controle e qualidade
  das repeticoes. Quando a mesma carga passar a ser registrada como RPE 8 ou
  menor, o sistema aumenta o alvo conforme a regra de progressao.
- Avaliacoes do historico e alertas do dashboard nao devem tratar uma sequencia
  de RPE 9 como problema isolado. Ela so exige atencao quando vier acompanhada
  de perda tecnica, repeticoes incompletas, piora de amplitude ou ausencia
  prolongada de qualquer melhora na execucao.
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
  barra reta de 2,20 m e 11 kg; a observacao deve mostrar carga total como
  `barra reta 2,20 m 11kg + Xkg de anilhas`.
- `Tríceps testa` e `Pullover (barra)` usam barra W de 6 kg; a observacao deve mostrar carga total como `barra W 6kg + Xkg de anilhas`.
- `Rosca martelo (barra H)` usa barra H de 9 kg; a observacao deve mostrar carga total como `barra H 9kg + Xkg de anilhas`.
- Manter `TREINO_EXERCISES` apenas como alias de compatibilidade.
- O primeiro exercicio ativo e `Agachamento com barra nas costas` (`3x5`).
- O segundo exercicio ativo e `Agachamento sumô com barra à frente` (`3x10`),
  com foco principal nos adutores.
- O quinto exercicio ativo e `Supino inclinado (barra)` (`3x8`), logo depois
  de `Supino reto back-off`, substituindo `Pullover (barra)` para sessoes futuras.
- O setimo exercicio ativo e `Remada curvada alta no peito (barra)` (`3x10`),
  logo depois de `Remada curvada (barra)`.
- O decimo exercicio ativo e `Rosca martelo (barra H)` (`3x8`), substituindo `Rosca direta` para sessoes futuras.
- `Supino fechado (barra)` e `Remada alta (barra)` estao inativos para sessoes futuras.
- Logs historicos de `Agachamento (barra)`, `Agachamento Zercher`, `Zercher squat`, `Pullover (barra)`, `Tríceps testa`, `Supino fechado (barra)` ou `Remada alta (barra)` podem permanecer como historico.

### `forja_de_ferro/db_ops.py`

Modulo SQLite para exercicios, logs de treino e dados de dieta.

- Banco versionado: `data/forja_de_ferro.db`.
- Versao atual do esquema: `SCHEMA_VERSION = 10`.
- `schema_migrations` registra cada migracao aplicada. `init_db()` executa
  migracoes pendentes em ordem e rejeita bancos com versao futura.
- `get_session_summary(session_id)` calcula o resumo pos-treino e usa a sessao
  anterior com a mesma sequencia de exercicios para comparar volume.
- Tabela principal de exercicios: `exercises` (`name`, `sets`, `reps`, `sort_order`, `active`).
- `exercise_muscle_groups` relaciona exercicios a grupos principais e
  secundarios. `/volume` e dashboard usam essa tabela como fonte unica.
- `training_plans` e `training_plan_exercises` armazenam modelos A/B ou outros
  ciclos. Apenas um plano com exercicios fica ativo por vez.
- `body_weights` armazena o historico temporal de peso corporal.
- `waist_measurements` armazena o historico temporal da circunferencia da cintura.
- `body_profile` armazena altura e idade em um registro unico para os calculos
  corporais do dashboard.
- No schema atual, `body_weights` usa `weight_kg` e `recorded_at`; nao assumir
  colunas `weight` ou `date`. `body_profile` usa `height_cm` e `age_years`; nao
  assumir coluna `age`.
- SQLite e a fonte da verdade para exercicios.
- Mudancas de catalogo que devem valer para bancos novos tambem precisam atualizar `DEFAULT_EXERCISES`.

### `forja_de_ferro/dashboard.py`

Dashboard local de volume de treino.

- `carregar_dados()` le `training_sessions` e `training_logs` no SQLite.
- O volume de cada linha e calculado como `sets x reps x weight`.
- Apenas logs com carga preenchida (`weight IS NOT NULL` e maior que zero) entram no dashboard.
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
  cintura/altura abaixo de 0,50 e os limites correspondentes de peso e cintura
  calculados pela altura cadastrada.
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
  segmentos anatomicos visuais, deixa regioes sem treino transparentes e aumenta
  a opacidade vermelha conforme o volume relativo da ultima sessao. Ele
  usa pesos por exercicio quando houver regra especifica e representa volume
  atribuido, nao ativacao muscular medida.
- Graficos de dados do dashboard, como evolucao de volume, minigraficos
  corporais, carga vs RPE, comparacoes, PRs e filtros rapidos, usam Chart.js
  carregado por CDN com versao fixa.
  Nao trocar o mapa anatomico para biblioteca de graficos; ele continua SVG
  vetorial baseado nos assets anatomicos.
- As regioes musculares sao renderizadas diretamente dos paths vetoriais de
  `body-muscles` (Apache-2.0), numa SVG unica por vista. Os SVGs anatomicos de
  Termininja (CC BY-SA 3.0) ficam preservados em `forja_de_ferro/assets/`.
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
