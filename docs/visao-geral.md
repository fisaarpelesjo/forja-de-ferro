# Visao Geral Do Sistema

A Forja de Ferro e um diario de treino controlado pelo Telegram.

Responsabilidades principais:

1. manter o SQLite versionado em `data/forja_de_ferro.db`
2. rodar um bot Telegram com long polling
3. guardar a sessao ativa em `session.json`
4. gerar um dashboard HTML local com a evolucao do volume de treino
5. extrair frames de videos locais para analise de execucao

## Fluxo Principal

```text
Usuario envia /gerar
  -> bot cria uma sessao no SQLite
  -> bot cria um log por exercicio ativo
  -> bot escreve session.json
  -> bot envia o treino em texto com alvo e descanso

Usuario envia /prever
  -> bot monta o treino em texto com alvo e descanso
  -> bot nao cria sessao, logs nem session.json

Usuario envia 80 ou 80 8
  -> bot carrega session.json
  -> bot conta logs preenchidos
  -> bot atualiza o proximo exercicio pendente
  -> bot responde com progresso

Usuario envia /desfazer
  -> bot encontra o ultimo log preenchido
  -> bot limpa carga e RPE

Usuario roda python gerar_dashboard.py
  -> dashboard le training_sessions e training_logs
  -> calcula volume = series x repeticoes x carga
  -> consolida carga, RPE, 1RM estimado, PRs, grupos musculares e periodos
  -> cruza volume x RPE, carga x RPE e ultima sessao contra media recente
  -> renderiza graficos de dados com Chart.js, mantendo o mapa anatomico em SVG
  -> organiza as secoes em pagina unica com layout escuro usando Carbon Web
     Components oficiais e adiciona filtros rapidos
  -> escreve temp/dashboard-treino.html

Usuario roda python gerar_frames.py --todos --instalar-ffmpeg
  -> launcher verifica e instala ffmpeg quando necessario
  -> localiza todos os videos em videos/entrada/
  -> modulo chama ffmpeg sem interacao
  -> cria uma pasta por video em videos/saida/
  -> informa a quantidade de frames gerada
```

## Entry Points

```bash
python start_bot.py
python gerar_dashboard.py
python gerar_frames.py --todos --instalar-ffmpeg
```

No Windows:

```bat
start_bot.bat
```

## Arquivos Principais

`start_bot.py`: launcher multiplataforma.

`gerar_dashboard.py`: gera `temp/dashboard-treino.html`.

`gerar_frames.py`: extrai frames de videos locais usando `ffmpeg`.

`forja_de_ferro/banner.py`: banner colorido do terminal.

`forja_de_ferro/telegram_poller.py`: comandos, polling e mensagens Telegram.

`forja_de_ferro/ods_ops.py`: gera sessoes e escreve `session.json`.

`forja_de_ferro/video_ops.py`: valida e executa a extracao de frames.

`forja_de_ferro/dashboard.py`: consolida logs de treino e renderiza HTML local.

`forja_de_ferro/db_ops.py`: acesso SQLite.

`tests/`: testes locais.

## Fonte Da Verdade

SQLite e a fonte da verdade para exercicios e logs.

`session.json` nao e fonte da verdade; ele so guarda o contexto da sessao ativa.
Ao carregar o estado, o bot valida os IDs contra o SQLite. Se o arquivo estiver
ausente, corrompido ou antigo, ele reconstrui a sessao mais recente com logs
pendentes. Uma sessao completa nao e recuperada como ativa.

## Catalogo Atual

```text
Agachamento Zercher - 3x5
Agachamento sumô com barra à frente - 3x10
Supino inclinado (barra) - 3x8
Remada curvada alta no peito (barra) - 3x10
Supino fechado (barra) - 3x8
```

O Zercher substitui o agachamento com barra para sessoes futuras porque o setup
atual nao tem rack adequado. O agachamento sumô com barra à frente complementa
o treino com foco principal nos adutores. O supino inclinado substitui o
`Pullover (barra)` e o supino fechado substitui `Tríceps testa` para sessoes
futuras. Historico antigo permanece como
historico.

## Idioma

A interface principal deve ser em PT-BR:

- comandos principais do Telegram
- mensagens do bot
- docs de uso
- mensagens de launcher

Comandos textuais do Telegram exigem `/` e usam somente os nomes oficiais em
PT-BR.
