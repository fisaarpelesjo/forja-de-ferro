# Arquitetura

A Forja de Ferro e um pacote Python pequeno com entry points de script. A ideia e
manter tudo simples: Python, SQLite e API HTTP do Telegram.

## Estrutura

```text
.
├── start_bot.py
├── start_bot.bat
├── data/
│   └── forja_de_ferro.db
├── docs/
├── forja_de_ferro/
│   ├── __init__.py
│   ├── banner.py
│   ├── db_ops.py
│   ├── ods_ops.py
│   └── telegram_poller.py
└── tests/
    ├── smoke_test.py
    └── e2e_training_flow_test.py
```

## Regra De Imports

Codigo de aplicacao deve ser importado pelo pacote:

```python
from forja_de_ferro import db_ops
from forja_de_ferro import ods_ops
from forja_de_ferro import telegram_poller
from forja_de_ferro import banner
```

Evite novos modulos de aplicacao na raiz. A raiz deve ficar para launchers,
configuracao, docs e testes.

## Direcao De Dependencias

```text
start_bot.py
  -> forja_de_ferro.banner
  -> forja_de_ferro.telegram_poller
       -> forja_de_ferro.ods_ops
       -> forja_de_ferro.db_ops
  -> forja_de_ferro.ods_ops
       -> forja_de_ferro.db_ops
```

`db_ops.py` fica na base e nao deve importar a camada do bot.

## Inicializacao

`python start_bot.py`:

1. importa o banner
2. importa o poller Telegram
3. imprime o banner
4. imprime mensagem de inicio em PT-BR
5. chama `telegram_poller.main()`

## Polling

O bot usa long polling. Isso significa:

- nao precisa de servidor publico
- nao precisa abrir porta
- precisa apenas de internet de saida
- chama `getUpdates` periodicamente

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
- `data/*.db-shm`
- `data/*.db-wal`
- `__pycache__/`

## Por Que `session.json` Existe

O banco guarda o historico duravel. `session.json` so aponta qual sessao esta
ativa e quais `log_id` devem receber as proximas cargas.

## Por Que O Pacote Chama `forja_de_ferro`

O app se chama Forja de Ferro no README, no banner e no banco `forja_de_ferro.db`.
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
