# Limulus

Diario tecnico de treino e dieta com bot do Telegram, banco SQLite versionado,
dashboard HTML local, backup/exportacao de dados e utilitarios para analise de
video.

> *Limulus polyphemus*, o caranguejo-ferradura: 450 milhoes de anos, cinco
> extincoes em massa, e a mesma forma. Nao venceu por ser o mais forte nem o
> mais rapido — venceu por continuar aparecendo. E disso que trata um diario de
> treino.

Este README e a referencia tecnica principal da raiz do projeto. A documentacao
expandida fica em [`docs/index.md`](docs/index.md), e o catalogo unico de
comandos fica em [`docs/comandos.md`](docs/comandos.md).

## Sumario Tecnico

- Runtime principal: pacote Python [`limulus/`](limulus/).
- Banco principal: [`data/limulus.db`](data/limulus.db).
- Estado local de sessao ativa: `session.json`, nao versionado.
- Variaveis locais: `.env`, nao versionado, com `TELEGRAM_TOKEN=...`.
- Launcher multiplataforma: [`start_bot.py`](start_bot.py).
- Wrapper Windows: [`start_bot.bat`](start_bot.bat).
- Dashboard local: [`gerar_dashboard.py`](gerar_dashboard.py) gera
  `temp/dashboard-treino.html`.
- Backup/exportacao/restauracao: [`gerenciar_dados.py`](gerenciar_dados.py).
- Extracao de frames: [`gerar_frames.py`](gerar_frames.py).
- Schema SQLite atual: `SCHEMA_VERSION = 10`, em
  [`limulus/db_ops.py`](limulus/db_ops.py).
- Fonte da verdade do treino: SQLite, especialmente `training_plans` e
  `training_plan_exercises`.

O projeto foi desenhado para uso local: o bot escreve no SQLite, o dashboard le o
mesmo banco, e os arquivos auxiliares ficam fora do versionamento quando sao
estado de maquina.

## Arquitetura

```text
.
├── start_bot.py                  # launcher multiplataforma do bot
├── start_bot.bat                 # wrapper Windows
├── gerar_dashboard.py            # gera temp/dashboard-treino.html
├── gerar_frames.py               # CLI de extracao de frames com ffmpeg
├── gerenciar_dados.py            # CLI de backup, exportacao e restauracao
├── limulus/
│   ├── db_ops.py                 # schema, migracoes, consultas e escrita SQLite
│   ├── ods_ops.py                # montagem de treino, progressao e session.json
│   ├── telegram_poller.py        # bot Telegram via long polling
│   ├── dashboard.py              # carga de dados e HTML do dashboard
│   ├── backup_ops.py             # backup SQLite, exportacao JSON e restauracao
│   ├── video_ops.py              # wrapper ffmpeg para frames
│   └── assets/                   # assets anatomicos e mapa muscular
├── data/
│   └── limulus.db         # banco SQLite versionado
├── docs/
│   ├── index.md                  # indice da documentacao detalhada
│   ├── comandos.md               # catalogo unico de comandos
│   ├── banco-de-dados.md         # detalhes de SQLite e fonte da verdade
│   ├── bot-telegram.md           # fluxo do bot e falhas comuns
│   ├── operacao.md               # rotina local e troubleshooting
│   └── melhorias-futuras.md      # roadmap tecnico
├── tests/
│   ├── smoke_test.py
│   ├── regras_treino_test.py
│   ├── dashboard_test.py
│   ├── backup_export_test.py
│   ├── telegram_falhas_test.py
│   ├── video_ops_test.py
│   └── e2e_training_flow_test.py
├── videos/
│   ├── entrada/                  # videos a processar
│   └── saida/                    # frames gerados por video
├── backups/                      # local, nao versionado
├── exportacoes/                  # local, nao versionado
├── temp/                         # dashboard e saidas locais
├── session.json                  # cache local da sessao ativa, nao versionado
├── .env.example                  # modelo de variaveis
└── .env                          # segredo local, nao versionado
```

## Fluxo De Dados

1. O usuario envia comandos pelo Telegram.
2. [`telegram_poller.py`](limulus/telegram_poller.py) interpreta a entrada
   e chama funcoes de treino, banco, dashboard ou medicoes corporais.
3. [`ods_ops.py`](limulus/ods_ops.py) monta o treino do plano ativo,
   calcula carga alvo por RPE, adiciona descanso e observacoes de montagem.
   Tambem calcula o Treino B de garagem a partir dos alvos do treino principal.
4. [`db_ops.py`](limulus/db_ops.py) cria sessoes, logs, planos, medicoes,
   dieta e resumo pos-treino no SQLite.
5. `session.json` guarda um cache da sessao ativa para o bot saber qual exercicio
   esta pendente.
6. [`dashboard.py`](limulus/dashboard.py) le o SQLite e gera um HTML unico
   em `temp/dashboard-treino.html`.
7. [`backup_ops.py`](limulus/backup_ops.py) usa a API nativa de backup do
   SQLite para criar copias consistentes e exportar JSON.

O SQLite e a fonte da verdade. `session.json` e apenas cache recuperavel.

## Instalar E Verificar

Requisitos:

- Python 3.10 ou superior.
- Dependencias de [`requirements.txt`](requirements.txt).
- Token do Telegram em `.env` para rodar o bot.
- `ffmpeg` apenas para extracao de frames.

Instalacao:

```bash
python -m pip install -r requirements.txt
copy .env.example .env
```

No Linux/macOS:

```bash
python3 -m pip install -r requirements.txt
cp .env.example .env
```

Configure `.env`:

```text
TELEGRAM_TOKEN=seu_token_aqui
```

Verificacao basica:

```bash
python tests/smoke_test.py
python tests/regras_treino_test.py
python tests/dashboard_test.py
python tests/backup_export_test.py
python tests/telegram_falhas_test.py
python tests/video_ops_test.py
python tests/e2e_training_flow_test.py
```

No Linux/macOS, use `python3` se `python` apontar para Python 2.

## Operacao Rapida

Iniciar o bot:

```bash
python start_bot.py
```

No Windows:

```powershell
.\start_bot.bat
```

Gerar dashboard:

```bash
python gerar_dashboard.py
```

Criar backup:

```bash
python gerenciar_dados.py backup
```

Exportar JSON:

```bash
python gerenciar_dados.py exportar
```

Restaurar backup validado:

```bash
python gerenciar_dados.py restaurar backups/arquivo.db --confirmar
```

Extrair frames de todos os videos:

```bash
python gerar_frames.py --todos --instalar-ffmpeg
```

## Bot Do Telegram

Todos os comandos textuais exigem `/`. Entradas numericas de carga e RPE nao usam
barra.

```text
/gerar          Cria uma sessao de treino no SQLite
/prever         Mostra o treino sem salvar sessao, logs ou session.json
/treinob        Mostra o Treino B de garagem com pesos do treino principal
/exercicios     Lista exercicios do plano ativo
/aquecimento    Mostra aquecimento curto de corpo todo
/volume         Mostra series e volume por grupo muscular
/dashboard      Atualiza temp/dashboard-treino.html e envia resumo curto
/planos         Lista modelos cadastrados
/plano NOME     Seleciona o plano ativo
/peso VALOR     Registra peso corporal em kg
/peso           Consulta peso atual, variacao e ultimas medicoes
/cintura VALOR  Registra cintura em cm
/cintura        Consulta cintura atual, variacao e ultimas medicoes
/status         Mostra exercicio atual e progresso
/desfazer       Remove carga e RPE do ultimo exercicio preenchido
/ajuda          Mostra ajuda principal
80              Registra 80 kg no proximo exercicio pendente
80 8            Registra 80 kg com RPE 8
80,5 8          Aceita virgula decimal e salva 80.5 kg
```

### Muay Thai (saco)

Antes do saco existe uma fase de fundamentos (`/fundamentos`): tres sessoes
que ensinam cada movimento isolado, sem impacto, sem combinacao e sem nenhum
equipamento — sem saco, luva, bandagem ou corda. Bater no saco
antes de o padrao estar formado grava o padrao errado com impacto junto, e
chute baixo sem giro do pe de apoio machuca o joelho na primeira sessao.

Ciclo de 8 semanas para iniciante, treinando saco em terca, quinta e sabado,
complementando a musculacao de segunda, quarta e sexta. Quinta e leve de
proposito, para nao prejudicar a sexta. Nada e gravado no banco: o modelo de
treino existente e serie x repeticao x carga, e Muay Thai e round x tempo x
percentual de potencia — encaixar um no outro faria o volume do dashboard
mentir.

```
/fundamentos    Fase sem equipamento: cada movimento isolado, sem combo
/fundamentos a  Sessao de fundamentos (a, b ou c)
/mt             Roteiro de hoje (ter/qui/sab); nos outros dias avisa e nao inicia
/mtterca        Forca o roteiro de terca (idem /mtquinta e /mtsabado)
/mtterca 3      Mesma coisa, na semana 3 da progressao
/proximo        Avanca um bloco do roteiro; no ultimo, encerra
/mtparar        Encerra o roteiro em andamento
/mtregras       Regras de seguranca do ciclo
/tecnicas       Indice da biblioteca de execucao
/como jab       Passo a passo e erros comuns de um golpe
/como chute baixo   A busca aceita acento, espaco, alias e numeracao (1, 2, 3)
```

Cada bloco termina com os atalhos `/como` das tecnicas que ele usa, em vez de
embutir o passo a passo inteiro — o Telegram corta mensagem em 4096 caracteres.
O estado do roteiro vive em `mt_session.json`, arquivo separado de
`session.json`, para que uma sessao de musculacao ativa e um roteiro de Muay
Thai em andamento nao se atropelem.

O polling registra logs operacionais com horario, nivel, comando e `session_id`.
Token e URL completa da API nao devem aparecer nos logs. Falhas temporarias usam
espera gradual; token invalido encerra o polling com erro claro.

O launcher deve manter saida minimalista no terminal: sem banner, ASCII art ou
mensagens cosmeticas.

## Fluxo De Sessao De Treino

`/gerar`:

1. Chama `db_ops.get_or_seed_exercises()`.
2. Busca o plano ativo em `training_plans` e `training_plan_exercises`.
3. Consulta desempenho anterior por exercicio.
4. Cria linha em `training_sessions` com `date` e `training_type`.
5. Cria um `training_logs` pendente para cada exercicio do plano ativo.
6. Calcula `target_weight` pela carga anterior e RPE anterior.
7. Adiciona `rest_interval` por exercicio.
8. Adiciona `loading_note` quando o exercicio usa barra/equipamento fixo.
9. Escreve `session.json` com `date`, `session_id` e exercicios.
10. Envia a lista do treino e indica o primeiro exercicio pendente.

`/prever` usa a mesma montagem de treino, mas nao cria `training_sessions`, nao
cria `training_logs` e nao escreve `session.json`.

`/treinob` nao cria sessao, logs nem `session.json`. Ele mostra um treino de
garagem de 10 voltas para dias sem treino principal, com peso unico por
exercicio. Os pesos sao calculados a partir dos alvos atuais do treino principal:
farmer walk usa 45% do terra romeno e remada leve com barra usa 60% da remada
curvada.
O comando nao pede nem registra RPE. Quando houver carga, ele tambem mostra a
montagem: barra reta de 2,50 m com 9 kg para remada com barra, e barra de
40 cm para farmer walk.

Registro numerico:

1. O bot carrega `session.json`.
2. Valida o cache contra o SQLite.
3. Encontra o proximo exercicio sem carga.
4. Atualiza `training_logs.weight` e `training_logs.rpe`.
5. Envia o proximo exercicio com alvo, descanso e montagem de carga quando houver.
6. No ultimo exercicio, envia resumo pos-treino.

`/desfazer` encontra o ultimo log preenchido da sessao ativa e limpa `weight` e
`rpe`.

Se `session.json` estiver ausente, corrompido ou antigo, o bot tenta reconstruir
a sessao mais recente ainda incompleta a partir do SQLite. Sessoes completas nao
sao reabertas.

## Resumo Pos-Treino

Ao concluir a sessao, `db_ops.get_session_summary(session_id)` calcula:

- volume total da sessao;
- RPE medio geral;
- comparacao com a sessao anterior compativel;
- mudancas de carga por exercicio;
- consolidacoes, quando a mesma carga fica mais facil;
- cargas mantidas em RPE 9;
- recordes e sinais relevantes.

A comparacao usa a sessao anterior com a mesma sequencia de exercicios. Isso
evita comparar planos diferentes como se fossem equivalentes.

## Progressao De Carga

A regra atual fica em `ods_ops.suggest_next_weight(previous_weight,
previous_rpe)`:

```text
RPE 7 ou menor  -> +4 kg
RPE 8           -> +2 kg
RPE 9           -> manter
RPE 10 ou maior -> -2 kg
Sem RPE         -> manter
```

Se nao houver historico, o alvo aparece como `-`, exceto nos exercicios com alvo
inicial configurado:

```text
Rosca martelo (barra H)  -> 16 kg
Supino inclinado (barra) -> 41 kg
```

RPE 9 repetido nao e tratado como estagnacao automaticamente. Nesse metodo,
manter carga em RPE 9 serve para consolidar tecnica, amplitude, controle e
qualidade. O aumento volta a acontecer quando a mesma carga passa a ser
registrada como RPE 8 ou menor.

Alertas e dashboard nao devem considerar carga mantida em RPE 9 como problema
isolado. Sinais de acompanhamento sao RPE 10 persistente, reducao apos RPE 10,
perda tecnica, repeticoes incompletas, piora de amplitude ou ausencia prolongada
de melhora na execucao.

## Plano Ativo E Catalogo

O treino ativo vem de `training_plan_exercises`, ligado ao plano ativo em
`training_plans`. `DEFAULT_EXERCISES` define o seed para bancos novos, mas o
SQLite permanece a fonte da verdade em runtime.

Catalogo ativo atual:

```text
1.  Agachamento com barra nas costas           3x5
2.  Agachamento sumô com barra à frente        3x10
3.  Supino reto (barra)                        3x5
4.  Supino reto back-off                       3x8
5.  Supino inclinado (barra)                   3x8
6.  Remada curvada (barra)                     3x8
7.  Remada curvada alta no peito (barra)       3x10
8.  Desenvolvimento (barra em pé)              3x5
9.  Levantamento Terra Romeno                  3x8
10. Rosca martelo (barra H)                    3x8
```

Nomes canonicos devem permanecer no SQLite porque sao usados no historico,
progressao, grupos musculares e dashboard. A interface pode usar
`ods_ops.get_display_name()` para ocultar qualificadores como `(barra)`,
`(barra H)` e `(barra em pé)`.

Logs historicos de exercicios substituidos ou renomeados podem permanecer no
banco como historico. Exemplos: `Agachamento (barra)`, `Agachamento Zercher`,
`Zercher squat`, `Pullover (barra)`, `Tríceps testa`, `Supino fechado (barra)`
e `Remada alta (barra)`.

## Descanso E Montagem De Carga

`ods_ops.get_rest_interval(exercise_name)` define descanso sugerido:

```text
Agachamento com barra nas costas       4 min
Agachamento Zercher                    4 min
Supino reto (barra)                    4 min
Supino reto back-off                   4 min
Supino inclinado (barra)               4 min
Remada curvada (barra)                 3 min
Desenvolvimento (barra em pé)          4 min
Levantamento Terra Romeno              4 min
Pullover (barra)                       2 min
Remada curvada alta no peito (barra)   2 min
Rosca direta                           2 min
Rosca martelo (barra H)                3 min
Tríceps testa                          2 min
Padrao para demais exercicios          2 min
```

`ods_ops.format_loading_note()` gera observacoes de montagem quando ha
equipamento fixo:

```text
barra reta 2,20 m 11kg + Xkg de anilhas
barra W 6kg + Xkg de anilhas
barra H 9kg + Xkg de anilhas
```

Mapeamento atual:

- barra reta de 2,20 m e 11 kg: agachamento com barra nas costas, supinos com
  barra, agachamento sumô com barra à frente, remada curvada, desenvolvimento,
  levantamento terra romeno e remada curvada alta no peito;
- barra W de 6 kg: tríceps testa e pullover;
- barra H de 9 kg: rosca martelo.

A observacao aparece no exercicio atual/proximo e no `/status`; nao aparece na
lista simples de `/exercicios`.

## Banco De Dados

O banco fica em `data/limulus.db`. O schema e migrado por
`db_ops.init_db()`, que:

1. garante a tabela `schema_migrations`;
2. descobre a maior versao aplicada;
3. rejeita bancos com versao futura;
4. executa migracoes pendentes em ordem;
5. registra cada versao aplicada;
6. semeia grupos musculares padrao;
7. semeia o plano de treino padrao quando necessario.

Versao atual: `SCHEMA_VERSION = 10`.

Tabelas principais:

```text
exercises
training_sessions
training_logs
foods
diet_targets
diet_entries
exercise_muscle_groups
training_plans
training_plan_exercises
body_weights
waist_measurements
body_profile
schema_migrations
```

Colunas importantes:

- `training_sessions`: `id`, `date`, `training_type`.
- `training_logs`: `id`, `session_id`, `exercise_name`, `sets`, `reps`,
  `weight`, `rpe`, `sort_order`.
- `exercises`: `name`, `sets`, `reps`, `sort_order`, `active`.
- `training_plans`: `name`, `active`, `sort_order`.
- `training_plan_exercises`: `plan_id`, `exercise_name`, `sets`, `reps`,
  `sort_order`.
- `exercise_muscle_groups`: `exercise_name`, `muscle_group`, `role`,
  `sort_order`.
- `body_weights`: `weight_kg`, `recorded_at`, `source`.
- `waist_measurements`: `circumference_cm`, `recorded_at`, `source`.
- `body_profile`: `height_cm`, `age_years`, `updated_at`.

Nao assumir colunas que nao existem, como `started_at`, `completed_at`,
`plan_name`, `exercise`, `logged_at`, `weight`, `date` em `body_weights`, ou
`age` em `body_profile`.

Indices relevantes:

- `idx_training_logs_session_pending` em `training_logs`;
- `idx_training_logs_exercise_history` em `training_logs`;
- `idx_exercise_muscle_groups_exercise`;
- `idx_training_plan_exercises_plan`;
- `idx_body_weights_recorded_at`;
- `idx_waist_measurements_recorded_at`.

Para manutencao, prefira scripts Python com `sqlite3` ou os helpers de
`limulus.db_ops`. Nao dependa do binario externo `sqlite3` estar no PATH.

## Migracoes

Resumo das versoes:

```text
1   Cria tabelas iniciais de exercicios, sessoes, logs e dieta
2   Adiciona indices de logs por sessao pendente e historico por exercicio
3   Cria exercise_muscle_groups
4   Cria training_plans e training_plan_exercises
5   Insere Agachamento sumô com barra à frente no catalogo/plano ativo
6   Cria body_weights
7   Cria waist_measurements
8   Cria body_profile
9   Adiciona vitamina B6 em foods e diet_targets
10  Renomeia Agachamento Zercher para Agachamento com barra nas costas
```

Mudancas de catalogo que precisam valer para bancos novos devem atualizar
`DEFAULT_EXERCISES`. Mudancas que precisam afetar bancos existentes devem virar
migracao.

## Dashboard

`gerar_dashboard.py` chama `dashboard.salvar_dashboard()` e escreve
`temp/dashboard-treino.html`.

O dashboard:

- le `training_sessions` e `training_logs`;
- considera apenas logs com `weight IS NOT NULL` e carga maior que zero;
- calcula volume como `sets x reps x weight`;
- usa `exercise_muscle_groups` como fonte unica de grupos musculares;
- consulta plano ativo, cargas, RPE, peso, cintura, perfil corporal e dieta;
- gera HTML local sem servidor ou build.

O layout deve permanecer escuro, cru e compacto, usando IBM Carbon Design System
oficial via Carbon Web Components. O HTML pode depender da CDN oficial ja
configurada para carregar componentes `cds-*`.

Graficos de dados usam Chart.js por CDN com versao fixa. O mapa anatomico
continua SVG vetorial baseado nos assets locais; nao deve ser trocado por
biblioteca de graficos.

Secoes principais:

- indicadores de resumo;
- treino ativo com series, repeticoes, alvo, descanso e montagem de carga;
- evolucao de volume por sessao;
- mapa muscular anterior e posterior da ultima sessao;
- equilibrio muscular;
- calendario de carga;
- carga, RPE e 1RM estimado por exercicio;
- comparacao da ultima sessao com a anterior;
- grupos musculares por volume e series;
- volume semanal;
- maiores evolucoes, quedas, recordes e PRs expandidos;
- carga vs. RPE;
- alertas;
- filtros rapidos;
- relatorio semanal;
- peso corporal, cintura, IMC e cintura/altura;
- dieta atual, macros, metas e micronutrientes.

Indicadores corporais:

- peso e IMC usam historico de `body_weights`;
- cintura e cintura/altura usam historico de `waist_measurements`;
- IMC e cintura/altura sao indicadores derivados, nao diagnosticos;
- metas de referencia usam IMC entre 18,5 e 24,9 e cintura/altura abaixo de
  0,50;
- barras de proximidade usam `limite da meta / valor atual`, limitadas a 100%.

Dieta:

- le `diet_entries`, `foods` e `diet_targets`;
- consolida alimentos repetidos;
- compara totais diarios com metas;
- mostra calorias, proteina, carboidrato, gordura, fibra, omega 3, potassio,
  magnesio, zinco, vitamina D e vitamina B6.

Mapa muscular:

- usa `limulus/assets/mapa_muscular_body_muscles.json`;
- renderiza paths do projeto `body-muscles` em uma SVG por vista;
- expande grupos amplos em segmentos anatomicos visuais;
- deixa regioes sem treino transparentes;
- aumenta opacidade conforme volume relativo da ultima sessao;
- representa volume atribuido, nao ativacao muscular medida.

Licencas dos assets ficam em `docs/licencas/`. Os SVGs anatomicos de Termininja
ficam preservados em `limulus/assets/`.

## Peso, Cintura E Perfil Corporal

`/peso VALOR` grava em `body_weights`:

- `weight_kg`;
- `recorded_at`;
- `source`.

`/peso` mostra:

- peso atual;
- variacao em relacao a medicao anterior;
- ultimas medicoes.

`/cintura VALOR` grava em `waist_measurements`:

- `circumference_cm`;
- `recorded_at`;
- `source`.

`/cintura` mostra:

- cintura atual;
- variacao em relacao a medicao anterior;
- ultimas medicoes.

`body_profile` guarda altura e idade em um registro unico, usado pelos calculos
corporais do dashboard.

## Dieta

As tabelas de dieta sao:

- `foods`: cadastro de alimentos por unidade/porcao e nutrientes;
- `diet_targets`: metas diarias de calorias, macros e micros;
- `diet_entries`: itens consumidos, refeicao, alimento, quantidade e ordem.

Nutrientes suportados:

```text
protein_g
carbo_g
fat_g
calories
fiber_g
omega3_g
potassium_mg
magnesium_mg
zinc_mg
vitamin_d_ui
vitamin_b6_mg
```

O dashboard calcula totais a partir de `diet_entries.quantity`, dados por porcao
em `foods` e metas em `diet_targets`.

## Backup, Exportacao E Restauracao

`backup_ops.validar_banco()` executa `PRAGMA integrity_check` e exige pelo menos
as tabelas `training_sessions`, `training_logs` e `exercises`.

`criar_backup()`:

1. valida o banco de origem;
2. cria a pasta de destino;
3. usa `sqlite3.Connection.backup()` para copiar;
4. valida o backup gerado.

`exportar_dados()`:

1. valida o banco;
2. cria JSON com `exported_at`, `schema_version` e tabelas do projeto;
3. exporta apenas tabelas conhecidas em `EXPORT_TABLES`.

`restaurar_backup()`:

1. valida o backup de origem;
2. cria backup de seguranca do banco atual quando ele existe;
3. copia para arquivo temporario no diretorio do destino;
4. valida o temporario;
5. substitui o banco com `os.replace()`;
6. remove temporarios em caso de falha.

Pare o bot antes de restaurar para evitar escrita concorrente no SQLite.

## Videos E Frames

`video_ops.extrair_frames(video_path, saida=None, fps=None, formato="jpg")` usa
`ffmpeg` para gerar frames.

Formatos aceitos:

```text
bmp
jpeg
jpg
png
webp
```

Comportamento:

- sem `fps`, extrai todos os frames;
- com `fps`, aplica filtro `fps=N`;
- a numeracao comeca em 1;
- arquivos anteriores do mesmo video e formato suportado sao removidos antes de
  processar;
- `ffmpeg` roda com `-hide_banner`, `-loglevel error`, `-nostdin` e `-y`.

CLI:

```bash
python gerar_frames.py --todos --instalar-ffmpeg
python gerar_frames.py --todos --instalar-ffmpeg --fps 1
python gerar_frames.py video.mp4 --instalar-ffmpeg
python gerar_frames.py video.mp4 --fps 1
python gerar_frames.py video.mp4 --saida temp/frames
python gerar_frames.py video.mp4 --formato png
```

`--instalar-ffmpeg` tenta usar:

- Windows: `winget`;
- macOS: Homebrew;
- Linux: `apt-get`, com `sudo` quando necessario.

## Testes

```text
tests/smoke_test.py              Checagem basica de importacao/ambiente
tests/regras_treino_test.py      Progressao, comandos e regras do treino
tests/dashboard_test.py          Calculos, secoes e HTML do dashboard
tests/backup_export_test.py      Backup, exportacao e restauracao
tests/telegram_falhas_test.py    Rede, token e espera gradual do polling
tests/video_ops_test.py          ffmpeg, formatos, limpeza e comandos
tests/e2e_training_flow_test.py  Fluxo local completo de treino
```

Comando completo:

```bash
python tests/smoke_test.py
python tests/regras_treino_test.py
python tests/dashboard_test.py
python tests/backup_export_test.py
python tests/telegram_falhas_test.py
python tests/video_ops_test.py
python tests/e2e_training_flow_test.py
```

Para mudancas pequenas, rode no minimo o teste mais proximo da area alterada e
`tests/smoke_test.py`. Para mudancas em schema, treino, bot ou dashboard, rode a
suite completa listada acima.

## API Interna Principal

`db_ops`:

```python
from limulus import db_ops

db_ops.init_db()
db_ops.get_or_seed_exercises()
db_ops.list_muscle_groups()
db_ops.list_training_plans()
db_ops.get_active_training_plan()
db_ops.create_session(date_iso, training_type="TREINO")
db_ops.log_exercise(session_id, exercise_name, sets, reps, sort_order)
db_ops.update_log_weight(log_id, weight, rpe=None)
db_ops.get_last_weights()
db_ops.get_last_performance()
db_ops.get_latest_incomplete_session()
db_ops.get_session_summary(session_id)
db_ops.add_body_weight(weight_kg)
db_ops.list_body_weights(limit=10)
db_ops.add_waist_measurement(circumference_cm)
db_ops.list_waist_measurements(limit=10)
db_ops.set_diet_targets(...)
db_ops.get_diet_targets()
db_ops.add_diet_entry(meal, food_id, quantity, sort_order=0)
db_ops.list_diet_entries()
db_ops.get_diet_totals()
```

`ods_ops`:

```python
from limulus import ods_ops

ods_ops.generate_training()
ods_ops.preview_training()
ods_ops.gerar_treino()
ods_ops.read_exercises()
ods_ops.read_previous_weights()
ods_ops.read_previous_performance()
ods_ops.suggest_next_weight(previous_weight, previous_rpe=None)
ods_ops.get_initial_target_weight(exercise_name)
ods_ops.get_display_name(exercise_name)
ods_ops.get_rest_interval(exercise_name)
ods_ops.format_loading_note(exercise_name, target_weight)
ods_ops.write_session(exercises, session_id)
ods_ops.recover_active_session()
```

`dashboard`:

```python
from limulus import dashboard

dashboard.carregar_dados()
dashboard.salvar_dashboard()
```

`backup_ops`:

```python
from limulus import backup_ops

backup_ops.validar_banco("data/limulus.db")
backup_ops.criar_backup()
backup_ops.exportar_dados()
backup_ops.restaurar_backup("backups/arquivo.db")
```

`video_ops`:

```python
from limulus import video_ops

video_ops.ffmpeg_disponivel()
video_ops.instalar_ffmpeg()
video_ops.extrair_frames("videos/entrada/video.mp4")
video_ops.contar_frames("videos/saida/video", "video")
```

## Estado Local E Versionamento

Nao versionar:

```text
session.json
.env
data/*.db-shm
data/*.db-wal
temp/dashboard-treino.html
backups/
exportacoes/
```

O banco principal `data/limulus.db` e versionado. Arquivos `-wal` e
`-shm` sao auxiliares do SQLite e continuam locais.

Antes de alterar arquivos de estado local, confirme que a mudanca e realmente
necessaria. Nunca grave segredos na documentacao, nos testes ou nos commits.

## Convencoes De Manutencao

- Usar portugues brasileiro para textos visiveis ao usuario, comandos,
  documentacao e mensagens do bot.
- Comandos textuais do Telegram devem ser oficiais, em PT-BR e com `/`.
- Nao adicionar aliases em ingles nem comandos sem barra.
- Preferir helpers existentes de `db_ops`, `ods_ops`, `dashboard`, `backup_ops`
  e `video_ops`.
- Manter SQLite como fonte da verdade para catalogo e historico.
- Preservar separacao entre dados versionados e estado local.
- Atualizar `docs/comandos.md` quando comando ou launcher mudar.
- Atualizar `docs/melhorias-futuras.md` quando item do roadmap for entregue,
  descartado ou repriorizado.
- Revisar `AGENTS.md`, `CLAUDE.md` e `.github/copilot-instructions.md` quando a
  mudanca alterar comportamento, comandos, fluxo, schema, paths ou padrao de
  idioma.

## Commits

Use Conventional Commits no titulo:

```text
feat: add sync command
fix: correct dashboard volume filter
docs: expand technical README
```

O corpo do commit e obrigatorio e deve explicar contexto tecnico, escopo e
motivo da decisao.

## Documentacao Detalhada

Consulte [`docs/index.md`](docs/index.md) para:

- visao geral do sistema;
- arquitetura e fronteiras de modulos;
- schema SQLite e fonte da verdade;
- bot Telegram e parsing de comandos;
- testes e estrategia de verificacao;
- portabilidade entre Windows, Linux, macOS e WSL;
- operacao diaria e troubleshooting;
- roadmap tecnico.
