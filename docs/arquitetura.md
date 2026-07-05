# Arquitetura

A Forja de Ferro e um pacote Python pequeno com entry points de script. A ideia e
manter tudo simples: Python, SQLite e API HTTP do Telegram.

## Estrutura

```text
.
├── start_bot.py
├── start_bot.bat
├── gerar_frames.py
├── gerenciar_dados.py
├── videos/
│   ├── entrada/
│   └── saida/
├── data/
│   └── forja_de_ferro.db
├── docs/
├── forja_de_ferro/
│   ├── __init__.py
│   ├── backup_ops.py
│   ├── dashboard.py
│   ├── db_ops.py
│   ├── ods_ops.py
│   ├── telegram_poller.py
│   └── video_ops.py
└── tests/
    ├── backup_export_test.py
    ├── dashboard_test.py
    ├── regras_treino_test.py
    ├── smoke_test.py
    ├── telegram_falhas_test.py
    ├── video_ops_test.py
    └── e2e_training_flow_test.py
```

## Regra De Imports

Codigo de aplicacao deve ser importado pelo pacote:

```python
from forja_de_ferro import db_ops
from forja_de_ferro import ods_ops
from forja_de_ferro import telegram_poller
```

Evite novos modulos de aplicacao na raiz. A raiz deve ficar para launchers,
configuracao, docs e testes.

## Direcao De Dependencias

```text
start_bot.py
  -> forja_de_ferro.telegram_poller
       -> forja_de_ferro.ods_ops
       -> forja_de_ferro.db_ops
  -> forja_de_ferro.ods_ops
       -> forja_de_ferro.db_ops

gerar_dashboard.py
  -> forja_de_ferro.dashboard
       -> SQLite

gerenciar_dados.py
  -> forja_de_ferro.backup_ops
       -> SQLite

gerar_frames.py
  -> forja_de_ferro.video_ops
       -> ffmpeg
```

`db_ops.py` fica na base e nao deve importar a camada do bot.

`db_ops.init_db()` tambem controla a evolucao do esquema. Cada migracao e
aplicada em ordem e registrada em `schema_migrations`; um banco com versao mais
nova que o codigo e rejeitado para evitar alteracoes incompativeis.

## Inicializacao

`python start_bot.py`:

1. importa o poller Telegram
2. chama `telegram_poller.main()`

A saida de terminal do launcher deve ser minimalista. O bot registra apenas logs
operacionais e erros uteis para diagnostico.

## Polling

O bot usa long polling. Isso significa:

- nao precisa de servidor publico
- nao precisa abrir porta
- precisa apenas de internet de saida
- chama `getUpdates` periodicamente

Falhas temporarias de rede usam espera gradual de 3 ate 60 segundos. Erros
permanentes de token encerram o polling. Os logs registram horario, nivel,
comando e `session_id`, mas nunca devem incluir token ou URL completa da API.

## Estado Local

Versionado:

- codigo
- docs
- testes
- `requirements.txt`
- `data/forja_de_ferro.db`

Nao versionado:

- `.env`
- `session.json`
- `pending_log.csv`
- `temp/`
- `backups/`
- `exportacoes/`
- `data/*.db-shm`
- `data/*.db-wal`
- `__pycache__/`
- `videos/`

## Por Que `session.json` Existe

O banco guarda o historico duravel. `session.json` so aponta qual sessao esta
ativa e quais `log_id` devem receber as proximas cargas.

O arquivo funciona como cache recuperavel. O carregamento valida `session_id` e
`log_id` no SQLite; quando o cache esta ausente, corrompido ou antigo,
`ods_ops.recover_active_session()` reconstrui a sessao mais recente com logs
pendentes. Sessoes completas nao sao reabertas.

## Por Que O Pacote Chama `forja_de_ferro`

O app se chama Forja de Ferro no README e no banco `forja_de_ferro.db`.
`forja_de_ferro` tambem e um nome valido e limpo para pacote Python.

## O Que Evitar

Nao:

- tirar exercicios do SQLite para voltar a ODS
- versionar `.env`
- versionar `session.json`
- versionar sidecars SQLite
- recriar wrappers na raiz sem necessidade
- voltar a interface principal para ingles
- criar servidor web para Telegram sem motivo claro
- fazer teste mutar o banco real sem isolamento
