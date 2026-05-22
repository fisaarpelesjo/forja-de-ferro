# Banco De Dados

IronForge usa SQLite.

Arquivo principal:

```text
data/ironforge.db
```

Esse banco e versionado e e a fonte da verdade para exercicios, sessoes, logs e
dados de dieta.

## Modulo SQLite

Todo acesso direto ao banco fica em:

```text
ironforge/db_ops.py
```

`DB_PATH` aponta para `data/ironforge.db` na raiz do repositorio.

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

`python gerar_dashboard.py` consolida esse volume por sessao e por exercicio e
escreve `temp/dashboard-treino.html`.

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

Ao mudar o catalogo para frente, atualize:

- `data/ironforge.db`
- `ironforge/db_ops.py`, em `DEFAULT_EXERCISES`

## Criacao De Sessao

```text
ods_ops.generate_training()
  -> ods_ops.read_exercises()
     -> db_ops.get_or_seed_exercises()
  -> seleciona TRAINING_EXERCISES = range(0, 11)
  -> db_ops.create_session(today)
  -> db_ops.log_exercise(...) para cada exercicio
```

`session.json` guarda `session_id` e `log_id` para o bot saber qual linha
atualizar quando o usuario envia carga. Ele tambem guarda `target_weight`, que
e a carga alvo calculada para a sessao atual, e `rest_interval`, que e o
descanso sugerido entre series.

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

Se nao houver historico de carga para o exercicio, `target_weight` fica `None` e
a tabela do bot mostra `-`.

A carga alvo nao altera `training_logs.weight` ao gerar a sessao. `weight`
continua `NULL` ate o usuario registrar a carga real pelo Telegram.

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
sqlite3 data/ironforge.db ".tables"
sqlite3 data/ironforge.db ".schema exercises"
sqlite3 data/ironforge.db "SELECT name, sets, reps FROM exercises ORDER BY sort_order;"
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
