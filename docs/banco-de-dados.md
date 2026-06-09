# Banco De Dados

A Forja de Ferro usa SQLite.

Arquivo principal:

```text
data/forja_de_ferro.db
```

Esse banco e versionado e e a fonte da verdade para exercicios, sessoes, logs e
dados de dieta.

## Versao E Migracoes

O esquema atual usa `SCHEMA_VERSION = 4`. A tabela `schema_migrations` registra
uma linha por versao aplicada, com data e hora.

`db_ops.init_db()`:

1. le a maior versao registrada
2. rejeita bancos mais novos que o codigo
3. aplica cada migracao pendente em ordem
4. registra a versao somente depois de concluir suas operacoes

A versao 1 cria as tabelas principais. A versao 2 adiciona indices para localizar
logs pendentes por sessao e historico por exercicio. A versao 3 cria
`exercise_muscle_groups`. A versao 4 cria planos de treino. As migracoes usam
`IF NOT EXISTS`, portanto tambem reconhecem bancos antigos que ja possuam as
tabelas, mas ainda nao tenham `schema_migrations`.

Antes de criar uma nova migracao, fazer backup do banco e adicionar um teste que
parta da versao anterior.

## Backup, Exportacao E Restauracao

O launcher local usa a API de backup do SQLite, sem copiar o arquivo enquanto
uma transacao pode estar incompleta:

```bash
python gerenciar_dados.py backup
python gerenciar_dados.py exportar
```

O backup gera um arquivo `.db` validado em `backups/`. A exportacao gera JSON em
`exportacoes/` com a versao do esquema e o conteudo das tabelas conhecidas.

Para restaurar:

```bash
python gerenciar_dados.py restaurar backups/arquivo.db --confirmar
```

Pare o bot antes da restauracao. O arquivo de origem passa por
`PRAGMA integrity_check`; se o banco atual existir, um backup de seguranca e
criado antes da substituicao.

## Modulo SQLite

Todo acesso direto ao banco fica em:

```text
forja_de_ferro/db_ops.py
```

`DB_PATH` aponta para `data/forja_de_ferro.db` na raiz do repositorio.

## Tabelas

### `exercises`

Catalogo de exercicios.

```text
id          INTEGER PRIMARY KEY AUTOINCREMENT
name        TEXT NOT NULL UNIQUE
sets        INTEGER NOT NULL
reps        INTEGER NOT NULL
sort_order  INTEGER NOT NULL UNIQUE
active      INTEGER NOT NULL DEFAULT 1
```

### `exercise_muscle_groups`

Classificacao muscular compartilhada pelo bot e dashboard.

```text
id             INTEGER PRIMARY KEY AUTOINCREMENT
exercise_name  TEXT NOT NULL
muscle_group   TEXT NOT NULL
role           TEXT NOT NULL (`principal` ou `secundario`)
sort_order     INTEGER NOT NULL
```

Os grupos dos exercicios atuais e aliases historicos sao inseridos de forma
idempotente por `init_db()`. Exercicios sem classificacao aparecem como
`Outros`, mas nenhum exercicio ativo deve permanecer nesse estado.

### `training_plans`

Modelos de treino cadastrados. Apenas um plano fica ativo por vez.

```text
id          INTEGER PRIMARY KEY AUTOINCREMENT
name        TEXT NOT NULL UNIQUE
active      INTEGER NOT NULL
sort_order  INTEGER NOT NULL
```

### `training_plan_exercises`

Sequencia, series e repeticoes de cada plano.

```text
id             INTEGER PRIMARY KEY AUTOINCREMENT
plan_id        INTEGER NOT NULL
exercise_name  TEXT NOT NULL
sets           INTEGER NOT NULL
reps           INTEGER NOT NULL
sort_order     INTEGER NOT NULL
```

O plano `A` e criado a partir do catalogo ativo existente. Outros planos podem
ser cadastrados com `db_ops.replace_training_plan()`. O bot seleciona com
`/plano NOME`.

### `training_sessions`

Uma linha por sessao gerada.

```text
id             INTEGER PRIMARY KEY AUTOINCREMENT
date           TEXT NOT NULL
training_type  TEXT NOT NULL DEFAULT 'TREINO'
```

### `training_logs`

Uma linha por exercicio dentro de uma sessao.

```text
id             INTEGER PRIMARY KEY AUTOINCREMENT
session_id     INTEGER NOT NULL REFERENCES training_sessions(id)
exercise_name  TEXT NOT NULL
sets           INTEGER NOT NULL
reps           INTEGER NOT NULL
weight         REAL
rpe            REAL
sort_order     INTEGER NOT NULL DEFAULT 0
```

`weight` e `rpe` comecam como `NULL`. A entrada `80 8` preenche a proxima linha
pendente da sessao ativa.

O dashboard local considera apenas linhas com `weight IS NOT NULL` e calcula o
volume de treino de cada linha assim:

```text
volume = sets x reps x weight
```

`python gerar_dashboard.py` consolida esse volume por sessao, exercicio, semana,
mes e grupo muscular. O HTML tambem mostra carga, RPE, series, repeticoes,
comparacao da ultima sessao com a anterior, recordes pessoais, maiores evolucoes,
1RM estimado, media movel, consistencia semanal, abas de navegacao, filtros
rapidos, analises cruzadas de volume/RPE/carga e alertas simples.

Os alertas consideram RPE 9 uma fase valida de consolidacao. O dashboard destaca
queda de RPE com a mesma carga como evolucao, acompanha RPE 10 persistente e
explica reducoes de carga feitas depois de RPE 10.

### Dieta

Tambem existem:

- `foods`
- `diet_targets`
- `diet_entries`

Essas tabelas guardam alimentos, metas e entradas de dieta.

## Catalogo Atual

Primeiro exercicio ativo:

```text
sort_order 1
name       Agachamento Zercher
sets       3
reps       5
```

Ele substituiu o agachamento com barra para sessoes futuras por falta de rack.
Historico antigo deve permanecer como historico salvo no SQLite.

O decimo exercicio ativo e `Rosca martelo (barra H)` (`3x8`), substituindo
`Rosca direta` para sessoes futuras. Historico antigo de `Rosca direta`
permanece como historico salvo no SQLite.

Ao mudar o catalogo para frente, atualize:

- `data/forja_de_ferro.db`
- `forja_de_ferro/db_ops.py`, em `DEFAULT_EXERCISES`

## Criacao De Sessao

```text
ods_ops.generate_training()
  -> ods_ops.read_exercises()
     -> db_ops.get_or_seed_exercises()
  -> le a sequencia do plano ativo em training_plan_exercises
  -> db_ops.create_session(today)
  -> db_ops.log_exercise(...) para cada exercicio
```

`session.json` guarda `session_id` e `log_id` para o bot saber qual linha
atualizar quando o usuario envia carga. Ele tambem guarda `target_weight`, que
e a carga alvo calculada para a sessao atual, e `rest_interval`, que e o
descanso sugerido entre series. Quando o exercicio usa equipamento de peso fixo,
tambem pode guardar `loading_note`, uma observacao de montagem da carga para o
bot mostrar no exercicio atual/proximo.

O SQLite tambem permite recuperar esse contexto. A consulta procura a sessao
mais recente que possui logs e pelo menos um `weight IS NULL`, preserva a ordem
por `sort_order` e reconstrui os alvos usando o desempenho anterior a cada log.
Sessoes sem pendencias nao sao consideradas ativas.

## Progressao De Carga

`db_ops.get_last_performance()` busca a ultima carga valida e o RPE mais recente
por exercicio. Durante `ods_ops.generate_training()`, cada exercicio recebe um
`target_weight` calculado assim:

```text
RPE 7 ou menor  -> ultima carga + 4 kg
RPE 8           -> ultima carga + 2 kg
RPE 9           -> ultima carga
RPE 10 ou maior -> ultima carga - 2 kg
Sem RPE         -> ultima carga
```

RPE 9 mantem `target_weight` de forma intencional. Essa fase permite consolidar
tecnica, amplitude, controle e qualidade das repeticoes com a carga atual; ela
nao deve ser classificada automaticamente como estagnacao. Quando a mesma carga
for registrada como RPE 8 ou menor, `suggest_next_weight()` aplica o aumento
correspondente.

Analises derivadas do banco devem interpretar uma sequencia de RPE 9 junto com
a qualidade da execucao. Sem dados de tecnica, repeticoes incompletas ou
amplitude, o valor isolado nao comprova falta de evolucao.

Se nao houver historico de carga para o exercicio, `target_weight` fica `None` e
a tabela do bot mostra `-`.

Excecao atual: `Rosca martelo (barra H)` recebe alvo inicial de 16 kg quando
ainda nao houver historico proprio. Depois do primeiro registro real, a funcao
usa o historico e a progressao por RPE.

A carga alvo nao altera `training_logs.weight` ao gerar a sessao. `weight`
continua `NULL` ate o usuario registrar a carga real pelo Telegram.

## Resumo Pos-Treino

`db_ops.get_session_summary(session_id)` calcula volume, RPE medio, mudancas de
carga, consolidacoes e recordes. Para comparar volume, procura a sessao anterior
com a mesma sequencia de exercicios preenchidos. Isso evita comparar diretamente
modelos de treino diferentes.

Para `Tríceps testa`, `Pullover (barra)` e `Remada alta (barra)`,
`ods_ops.format_loading_note()` usa barra W de 6 kg e calcula as anilhas como
`target_weight - 6`. Exemplo: `target_weight = 18` gera
`barra W 6kg + 12kg de anilhas`.

Para `Rosca martelo (barra H)`, a funcao usa barra H de 9 kg e calcula as
anilhas como `target_weight - 9`. Exemplo: `target_weight = 18` gera
`barra H 9kg + 9kg de anilhas`.

## Descanso Entre Series

O descanso sugerido fica em `session.json`, nao em uma tabela SQLite. Ele e
derivado do nome do exercicio por `ods_ops.get_rest_interval()` durante a geracao
da sessao.

## Progresso

`count_filled(log_ids)` conta quantos logs tem `weight IS NOT NULL`.

```text
filled = 0  -> proximo exercicio exercises[0]
filled = 1  -> proximo exercicio exercises[1]
filled = 11 -> treino completo
```

## Inspecao Segura

```bash
sqlite3 data/forja_de_ferro.db ".tables"
sqlite3 data/forja_de_ferro.db ".schema exercises"
sqlite3 data/forja_de_ferro.db "SELECT name, sets, reps FROM exercises ORDER BY sort_order;"
python gerar_dashboard.py
```

## Nao Versionar

```text
data/*.db-shm
data/*.db-wal
session.json
.env
temp/
```

## Isolamento Dos Testes

O E2E troca temporariamente `DB_PATH`, `DATA_DIR`, `SESSION_FILE` e `send` para
nao tocar no banco real nem chamar Telegram.
