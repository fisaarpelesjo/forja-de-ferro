# IronForge

Diario de treino e dieta com bot do Telegram e banco SQLite local.

## Visao Geral

O IronForge permite controlar uma sessao de treino pelo Telegram:

- `/gerar` cria uma nova sessao de treino no SQLite.
- `/prever` mostra o treino no mesmo formato, mas sem salvar sessao ou logs.
- O treino gerado lista carga alvo e descanso sugerido por exercicio.
- Enviar `80` registra 80 kg no proximo exercicio pendente.
- Enviar `80 8` registra 80 kg com RPE 8.
- `/status` mostra o progresso da sessao ativa.
- `/desfazer` apaga o ultimo exercicio registrado.
- `python gerar_dashboard.py` gera um dashboard HTML local com a evolucao do
  volume de treino.

O banco principal e `data/ironforge.db`. A sessao ativa fica em `session.json`,
que e estado local e nao deve ser versionado.

## Estrutura

```text
ironforge/
├── start_bot.py             # launcher multiplataforma
├── start_bot.bat            # wrapper Windows
├── gerar_dashboard.py       # gera temp/dashboard-treino.html
├── ironforge/
│   ├── banner.py            # banner do terminal
│   ├── telegram_poller.py   # bot Telegram com long polling
│   ├── ods_ops.py           # operacoes de sessao de treino
│   ├── dashboard.py         # dashboard HTML de volume de treino
│   └── db_ops.py            # operacoes SQLite
├── tests/
│   ├── smoke_test.py        # checagem basica do ambiente
│   └── e2e_training_flow_test.py # teste ponta a ponta local
├── docs/
│   └── index.md             # indice da documentacao detalhada
├── session.json             # estado local, nao versionado
├── .env.example             # modelo de ambiente
├── .env                     # TELEGRAM_TOKEN=..., nao versionado
└── data/
    └── ironforge.db         # banco SQLite versionado
```

## Comandos Do Telegram

```text
/gerar          Cria uma sessao de treino SQLite e mostra o treino em texto
/prever         Mostra uma previa do treino sem salvar nada
/exercicios     Lista exercicios atuais, series e repeticoes
/aquecimento    Mostra o aquecimento
/volume         Mostra series por grupo muscular e estimativa semanal
/status         Mostra exercicio atual e progresso da sessao
/desfazer       Limpa o ultimo registro de carga
/ajuda          Mostra ajuda
```

Aliases antigos em ingles ainda podem funcionar por compatibilidade:
`/generate`, `/exercises`, `/warmup`, `/undo`, `/help`.

## Registro De Carga

```text
80        Registra 80 kg no proximo exercicio pendente
80 8      Registra 80 kg e RPE 8
80,5 8    Virgula decimal e aceita e salva como 80.5 kg
```

## Dashboard De Treino

O dashboard local mostra a evolucao do volume usando:

```text
volume = series x repeticoes x carga
```

Para gerar:

```bash
python gerar_dashboard.py
```

O arquivo e criado em `temp/dashboard-treino.html`. Abra esse HTML no navegador
para ver:

- volume por sessao, semana e mes
- evolucao por exercicio
- carga atual, melhor carga, variacao e RPE medio
- series, repeticoes e media de volume por exercicio
- comparacao da ultima sessao com a anterior
- grupos musculares por volume e series
- maiores evolucoes, quedas, recordes pessoais e alertas simples
- 1RM estimado por exercicio usando a formula de Epley
- media movel de volume em janela de 3 sessoes
- consistencia semanal e dias desde o ultimo treino
- filtros rapidos por periodo, exercicio e ordenacao

## Progressao De Carga Por RPE

Ao gerar uma nova sessao, o bot busca a ultima carga registrada de cada
exercicio e sugere a proxima carga conforme o RPE registrado:

```text
RPE 7 ou menor  -> +4 kg
RPE 8           -> +2 kg
RPE 9           -> manter
RPE 10 ou maior -> -2 kg
Sem RPE         -> manter
```

Exemplo:

```text
Treino anterior: 40 kg RPE 8
Proximo /gerar: alvo 42 kg
```

Se o exercicio ainda nao tiver historico de carga, o alvo aparece como `-`.
A carga alvo fica em `session.json`; o banco continua guardando apenas a carga
real registrada pelo usuario.

## Descanso Entre Series

O `/gerar` tambem mostra o descanso sugerido por exercicio:

```text
Agachamento Zercher, Supino reto principal, Levantamento Terra Romeno: 4 min
Remada curvada, Desenvolvimento: 3 min
Acessorios e supino reto back-off: 2 min
Rosca direta, Triceps testa: 2 min
```

Esses tempos fixos ajudam a manter a qualidade das series e deixam o RPE mais
confiavel para calcular a proxima carga.

## Fluxo Do Treino

```text
/gerar
  -> db_ops.get_or_seed_exercises()
  -> db_ops.get_last_performance()
  -> db_ops.create_session(date)
  -> db_ops.log_exercise(...) para cada exercicio ativo, com alvo calculado por carga + RPE
  -> adiciona descanso sugerido por exercicio
  -> ods_ops.write_session(...) escreve session.json

/prever
  -> monta o mesmo treino com alvo e descanso
  -> nao cria training_sessions
  -> nao cria training_logs
  -> nao escreve session.json

"80 8"
  -> carrega a sessao ativa
  -> encontra o proximo exercicio sem carga
  -> db_ops.update_log_weight(log_id, 80.0, 8)

/desfazer
  -> encontra o ultimo exercicio preenchido
  -> db_ops.update_log_weight(log_id, None, None)
```

## Catalogo Atual

O catalogo ativo comeca com:

```text
Agachamento Zercher    3x5
Supino reto back-off   2x8
```

Ele substituiu o agachamento com barra para sessoes futuras porque o setup atual
nao tem rack de agachamento adequado. Logs historicos com nomes antigos continuam
como historico.

## Setup

1. Instale Python 3.10+.
2. Instale dependencias:

```bash
pip install -r requirements.txt
```

3. Crie `.env`:

```bash
copy .env.example .env
```

No Linux/macOS:

```bash
cp .env.example .env
```

4. Rode a checagem basica:

```bash
python tests/smoke_test.py
```

5. Rode o teste ponta a ponta local:

```bash
python tests/dashboard_test.py
python tests/e2e_training_flow_test.py
```

6. Gere o dashboard local:

```bash
python gerar_dashboard.py
```

7. Inicie o bot:

```bash
python start_bot.py
```

No Linux/macOS, use `python3 start_bot.py` se `python` apontar para Python 2.
No Windows, tambem pode rodar `start_bot.bat`.

## Banco De Dados

Tabelas principais:

- `exercises`
- `training_sessions`
- `training_logs`
- `foods`
- `diet_targets`
- `diet_entries`

O catalogo de exercicios fica no SQLite. Nao substituir por ODS.

## API Interna

```python
from ironforge import db_ops, ods_ops

db_ops.get_or_seed_exercises()
db_ops.create_session(date_iso, training_type="TREINO")
db_ops.log_exercise(session_id, name, sets, reps, sort_order)
db_ops.update_log_weight(log_id, weight, rpe=None)
db_ops.get_last_weights()
db_ops.get_last_performance()
db_ops.count_filled(log_ids)

ods_ops.generate_training()
ods_ops.preview_training()
ods_ops.suggest_next_weight(previous_weight, previous_rpe=None)
ods_ops.get_rest_interval(exercise_name)
ods_ops.write_session(exercises, session_id)
ods_ops.read_exercises()
ods_ops.read_previous_weights()

dashboard.carregar_dados()
dashboard.salvar_dashboard()
```

`ironforge.ods_ops.gerar_treino()` existe como alias de compatibilidade.

## Documentacao Detalhada

A documentacao detalhada fica em [`docs/index.md`](docs/index.md):

- arquitetura e fronteiras dos modulos
- schema SQLite e regras de fonte da verdade
- fluxo dos comandos Telegram
- testes smoke e ponta a ponta
- portabilidade entre Windows, Linux, macOS e maquinas fracas
- operacao e troubleshooting
