# Visao Geral Do Sistema

A Forja de Ferro e um diario de treino controlado pelo Telegram.

Responsabilidades principais:

1. manter o SQLite versionado em `data/forja_de_ferro.db`
2. rodar um bot Telegram com long polling
3. guardar a sessao ativa em `session.json`
4. gerar um dashboard HTML local com a evolucao do volume de treino

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
  -> organiza as secoes em abas com layout escuro e adiciona filtros rapidos
  -> escreve temp/dashboard-treino.html
```

## Entry Points

```bash
python start_bot.py
python gerar_dashboard.py
```

No Windows:

```bat
start_bot.bat
```

## Arquivos Principais

`start_bot.py`: launcher multiplataforma.

`gerar_dashboard.py`: gera `temp/dashboard-treino.html`.

`forja_de_ferro/banner.py`: banner colorido do terminal.

`forja_de_ferro/telegram_poller.py`: comandos, polling e mensagens Telegram.

`forja_de_ferro/ods_ops.py`: gera sessoes e escreve `session.json`.

`forja_de_ferro/dashboard.py`: consolida logs de treino e renderiza HTML local.

`forja_de_ferro/db_ops.py`: acesso SQLite.

`tests/`: testes locais.

## Fonte Da Verdade

SQLite e a fonte da verdade para exercicios e logs.

`session.json` nao e fonte da verdade; ele so guarda o contexto da sessao ativa.

## Catalogo Atual

```text
Agachamento Zercher - 3x5
```

Esse exercicio substitui o agachamento com barra para sessoes futuras porque o
setup atual nao tem rack adequado. Historico antigo permanece como historico.

## Idioma

A interface principal deve ser em PT-BR:

- comandos principais do Telegram
- mensagens do bot
- docs de uso
- mensagens de launcher

Aliases antigos em ingles podem continuar existindo por compatibilidade.
