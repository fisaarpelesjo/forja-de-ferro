# Forja de Ferro

Diario de treino e dieta com bot do Telegram e banco SQLite local.

## Visao Geral

A Forja de Ferro permite controlar uma sessao de treino pelo Telegram:

- `/gerar` cria uma nova sessao de treino no SQLite.
- `/prever` mostra o treino no mesmo formato, mas sem salvar sessao ou logs.
- O treino gerado lista carga alvo e descanso sugerido por exercicio.
- Quando o exercicio atual usa equipamento de peso fixo, o bot mostra como
  montar a carga, por exemplo `barra W 6kg + 12kg de anilhas`.
- Enviar `80` registra 80 kg no proximo exercicio pendente.
- Enviar `80 8` registra 80 kg com RPE 8.
- `/status` mostra o progresso da sessao ativa.
- `/desfazer` apaga o ultimo exercicio registrado.
- `/planos` lista os modelos cadastrados e `/plano NOME` seleciona o ativo.
- `/dashboard` atualiza o HTML local e responde com um resumo curto.
- Ao concluir o ultimo exercicio, o bot envia resumo da sessao com volume, RPE,
  comparacao, mudancas de carga, consolidacoes e recordes.
- `python gerar_dashboard.py` gera um dashboard HTML local com a evolucao do
  volume de treino.
- `python gerar_frames.py --todos --instalar-ffmpeg` verifica a dependencia e
  gera todos os frames dos videos de `videos/entrada/`.
- `python gerenciar_dados.py backup` cria uma copia consistente do SQLite.
- `python gerenciar_dados.py exportar` exporta os dados para JSON.

O catalogo completo e centralizado em
[`docs/comandos.md`](docs/comandos.md).

O banco principal e `data/forja_de_ferro.db`. A sessao ativa fica em `session.json`,
que e estado local e nao deve ser versionado.

`session.json` funciona como cache. Se for apagado, corrompido ou apontar para
uma sessao antiga, o bot tenta reconstruir a sessao SQLite mais recente que
ainda possui exercicios pendentes. Sessoes completas nao sao reabertas.

O esquema SQLite possui versao propria em `schema_migrations`. Ao iniciar, o
projeto aplica migracoes pendentes em ordem e preserva os dados existentes.

Os grupos musculares ficam em `exercise_muscle_groups`, com classificacao
principal ou secundaria. `/volume` e dashboard consultam a mesma tabela.

## Estrutura

```text
forja_de_ferro/
├── start_bot.py             # launcher multiplataforma
├── start_bot.bat            # wrapper Windows
├── gerar_dashboard.py       # gera temp/dashboard-treino.html
├── gerar_frames.py          # gera frames de video com ffmpeg
├── videos/
│   ├── entrada/             # videos de entrada
│   └── saida/               # frames gerados por arquivo
├── gerenciar_dados.py       # backup, exportacao e restauracao
├── forja_de_ferro/
│   ├── banner.py            # banner do terminal
│   ├── backup_ops.py        # gestao segura dos dados SQLite
│   ├── telegram_poller.py   # bot Telegram com long polling
│   ├── ods_ops.py           # operacoes de sessao de treino
│   ├── dashboard.py         # dashboard HTML de volume de treino
│   └── db_ops.py            # operacoes SQLite
├── tests/
│   ├── smoke_test.py        # checagem basica do ambiente
│   ├── regras_treino_test.py # regras de progressao e comandos
│   ├── dashboard_test.py    # calculos e HTML do dashboard
│   ├── backup_export_test.py # backup, exportacao e restauracao
│   ├── telegram_falhas_test.py # rede, token e repeticao gradual
│   └── e2e_training_flow_test.py # teste ponta a ponta local
├── docs/
│   └── index.md             # indice da documentacao detalhada
├── session.json             # estado local, nao versionado
├── .env.example             # modelo de ambiente
├── .env                     # TELEGRAM_TOKEN=..., nao versionado
└── data/
    └── forja_de_ferro.db         # banco SQLite versionado
```

## Comandos Do Telegram

```text
/gerar          Cria uma sessao de treino SQLite e mostra o treino em texto
/prever         Mostra uma previa do treino sem salvar nada
/exercicios     Lista exercicios atuais, series e repeticoes
/aquecimento    Mostra o aquecimento
/volume         Mostra series por grupo muscular e estimativa semanal
/dashboard      Atualiza o dashboard local e mostra um resumo
/planos         Lista planos de treino cadastrados
/plano NOME     Seleciona o plano ativo
/peso 118,5     Registra o peso corporal em quilogramas
/peso           Mostra o peso atual e as ultimas medicoes
/cintura 110,5  Registra a circunferencia da cintura em centimetros
/cintura        Mostra a cintura atual e as ultimas medicoes
/status         Mostra exercicio atual e progresso da sessao
/desfazer       Limpa o ultimo registro de carga
/ajuda          Mostra ajuda
```

Todos os comandos textuais do Telegram exigem `/` e usam somente os nomes
oficiais em PT-BR. Entradas numericas como `80` e `80 8` registram carga e RPE.

## Registro De Carga

```text
80        Registra 80 kg no proximo exercicio pendente
80 8      Registra 80 kg e RPE 8
80,5 8    Virgula decimal e aceita e salva como 80.5 kg
```

No ultimo registro, a resposta inclui o resumo automatico. A comparacao de
volume usa a sessao anterior com a mesma sequencia de exercicios. Carga mantida
em RPE 9 e mostrada separadamente de consolidacao confirmada, que ocorre quando
a mesma carga passa de RPE 9 para RPE 8 ou menor.

## Dashboard De Treino

O dashboard local mostra a evolucao do volume usando:

```text
volume = series x repeticoes x carga
```

Para gerar:

```bash
python gerar_dashboard.py
```

Pelo Telegram, `/dashboard` executa a mesma geracao e responde com horario,
ultima sessao, volume e RPE medio geral. O arquivo permanece local e nenhum
caminho do computador e enviado.

O arquivo e criado em `temp/dashboard-treino.html`. Abra esse HTML no navegador
para ver um layout escuro, cru e compacto com pagina unica rolavel:

- 8 indicadores de resumo, incluindo peso corporal, cintura e variacoes recentes
- grafico de evolucao do volume por sessao
- mapa muscular anterior e posterior da ultima sessao com segmentos anatomicos e gradiente azul-amarelo-vermelho proporcional ao volume
- equilibrio muscular com relacoes anterior/posterior, empurrar/puxar e outras comparacoes
- calendario de carga das ultimas sessoes
- carga, RPE e 1RM estimado (Epley) por exercicio
- comparacao da ultima sessao com a anterior
- grupos musculares por volume e series
- volume semanal
- maiores evolucoes de carga e volume, quedas, recordes pessoais e PRs expandidos
- grafico de carga vs. RPE por exercicio
- alertas simples com sinais de consolidacao
- filtros rapidos por periodo, exercicio, segmento anatomico e ordenacao
- relatorio semanal local com volume, RPE, segmentos principais e observacoes
- dieta atual no final da pagina, com alimentos repetidos consolidados
- totais de calorias e macros comparados com as metas diarias

O mapa muscular renderiza os paths vetoriais de
[`body-muscles`](https://github.com/vulovix/body-muscles), de Ivan Vulovic,
sob Apache-2.0, numa SVG unica por vista. Grupos amplos do catalogo, como
peitoral, dorsais, trapezio, biceps, triceps, antebraco, core, quadriceps,
adutores, gluteos e posteriores, sao distribuidos em segmentos anatomicos para
o desenho e a legenda lateral. Quando houver regra especifica para o exercicio, o
dashboard usa pesos por segmento em vez de dividir tudo igualmente. Os
SVGs anatomicos de Termininja (CC BY-SA 3.0) ficam preservados em
`forja_de_ferro/assets/`. A atribuicao e as licencas ficam em `docs/licencas/`.

## Extrair Frames De Video

Use o launcher local quando quiser analisar videos de execucao quadro a quadro:

1. coloque o video em `videos/entrada/`
2. rode o comando abaixo

```bash
python gerar_frames.py --todos --instalar-ffmpeg
```

O comando verifica se o `ffmpeg` esta disponivel e tenta instala-lo quando
necessario. No Windows, a instalacao usa o `winget`. Cada video recebe sua
propria pasta em `videos/saida/<nome-do-video>/`, e o terminal mostra quantos
frames foram gerados.

Sem `--fps`, todos os frames sao extraidos. Para reduzir a quantidade:

```bash
python gerar_frames.py --todos --instalar-ffmpeg --fps 1
```

Tambem e possivel processar apenas um arquivo:

```bash
python gerar_frames.py video.mp4 --instalar-ffmpeg
python gerar_frames.py video.mp4 --fps 1
python gerar_frames.py video.mp4 --saida temp/frames
```

JPG, JPEG, PNG, WebP e BMP sao aceitos. Antes de processar um video, os frames
anteriores com o mesmo nome sao removidos para manter a contagem correta.

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

Neste metodo, repetir a mesma carga em RPE 9 nao significa automaticamente
estagnacao. A manutencao da carga serve para consolidar tecnica, amplitude,
controle e qualidade das repeticoes. Quando essa mesma carga passar a ser
percebida como RPE 8 ou menor, o bot sugere o aumento correspondente.

Uma sequencia de RPE 9 deve ser interpretada junto com a execucao. Ela merece
atencao quando houver perda tecnica, repeticoes incompletas, piora de amplitude
ou ausencia prolongada de melhora, e nao apenas porque a carga permaneceu igual.

Exemplo:

```text
Treino anterior: 40 kg RPE 8
Proximo /gerar: alvo 42 kg
```

Se o exercicio ainda nao tiver historico de carga, o alvo aparece como `-`.
A carga alvo fica em `session.json`; o banco continua guardando apenas a carga
real registrada pelo usuario.

Excecao atual: `Rosca martelo (barra H)` comeca com alvo inicial de 16 kg quando
ainda nao houver historico proprio. Depois do primeiro registro, ela segue a
progressao normal por RPE.

Para exercicios com equipamento de peso fixo, o bot tambem guarda uma observacao
de montagem em `session.json`. Os dois supinos, `Agachamento Zercher`, `Remada
curvada (barra)`, `Desenvolvimento (barra em pé)`, `Levantamento Terra Romeno`
e `Remada curvada alta no peito (barra)` usam barra reta de 2,20 m e 11 kg.
`Agachamento sumô com barra à frente` usa barra oca de 1,50 m e 1 kg.
`Tríceps testa`, `Pullover (barra)` e `Remada alta (barra)` usam barra W de
6 kg; `Rosca martelo (barra H)` usa barra H de 9 kg. Essa observacao aparece
no `/status` e na indicacao do proximo exercicio, mas nao na lista
`/exercicios`.

## Descanso Entre Series

O `/gerar` tambem mostra o descanso sugerido por exercicio:

```text
Agachamento Zercher, Supino reto principal, Levantamento Terra Romeno: 4 min
Remada curvada, Desenvolvimento, Remada alta: 3 min
Acessorios e supino reto back-off: 2 min
Rosca martelo (barra H), Triceps testa: 2 min
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
  -> adiciona observacao de montagem quando houver equipamento fixo
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
Agachamento sumô com barra à frente 3x10
Supino reto back-off   2x8
Rosca martelo (barra H) 3x8
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
python tests/regras_treino_test.py
python tests/dashboard_test.py
python tests/backup_export_test.py
python tests/telegram_falhas_test.py
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
- `exercise_muscle_groups`
- `training_plans`
- `training_plan_exercises`

O catalogo de exercicios fica no SQLite. Nao substituir por ODS.

Operacoes locais:

```bash
python gerenciar_dados.py backup
python gerenciar_dados.py exportar
python gerenciar_dados.py restaurar backups/arquivo.db --confirmar
```

Backups ficam em `backups/` e exportacoes em `exportacoes/`. Ambos sao locais e
nao versionados. A restauracao valida a integridade do arquivo e cria um backup
de seguranca do banco atual antes da substituicao. Pare o bot antes de restaurar.

## API Interna

```python
from forja_de_ferro import db_ops, ods_ops

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

`forja_de_ferro.ods_ops.gerar_treino()` existe como alias de compatibilidade.

## Documentacao Detalhada

A documentacao detalhada fica em [`docs/index.md`](docs/index.md):

- arquitetura e fronteiras dos modulos
- schema SQLite e regras de fonte da verdade
- fluxo dos comandos Telegram
- testes smoke e ponta a ponta
- portabilidade entre Windows, Linux, macOS e maquinas fracas
- operacao e troubleshooting
- roadmap priorizado de melhorias futuras
