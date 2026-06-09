# Testes

Os testes ficam em:

```text
tests/
```

Eles sao scripts Python simples. Nao exigem pytest.

Rode a partir da raiz do repositorio.

## Teste De Fumaca

```bash
python tests/smoke_test.py
```

Objetivo:

- validar Python 3.10+
- validar imports de dependencias
- validar imports dos modulos principais
- validar existencia de `data/forja_de_ferro.db`

Saida esperada:

```text
Teste de fumaca passou.
```

## Teste Ponta A Ponta

```bash
python tests/e2e_training_flow_test.py
```

Saida esperada:

```text
Teste ponta a ponta do fluxo de treino passou.
```

O teste:

- cria SQLite temporario
- cria `session.json` temporario
- substitui `telegram_poller.send` por lista em memoria
- roda `handle_generate()`
- registra `80 8`
- consulta `/status`
- roda `/desfazer`
- registra `80,5`

Ele nao chama a API real do Telegram e nao mexe no banco real.

## Teste Das Regras De Treino

```bash
python tests/regras_treino_test.py
```

O teste cobre:

- progressao completa para RPE 7, 8, 9 e 10
- carga sem RPE e carga anterior ausente
- alvo inicial da rosca martelo
- descansos e observacoes de montagem das barras W e H
- `/prever`, `/exercicios` e `/volume`
- entrada de carga invalida
- `/desfazer` sem registro e depois de registrar carga
- sessao completa e tentativa de registrar carga adicional

Todo o estado fica em diretorio temporario.

## Teste Do Dashboard

```bash
python tests/dashboard_test.py
```

Valida os calculos, alertas, analises e a geracao do HTML usando SQLite
temporario.

## Ordem Recomendada

```bash
pip install -r requirements.txt
python tests/smoke_test.py
python tests/regras_treino_test.py
python tests/e2e_training_flow_test.py
python tests/dashboard_test.py
```

Se o teste de fumaca falhar, corrija ambiente primeiro. Se ele passar e o E2E
falhar, o problema provavelmente esta em logica do app.

## Novos Testes

Preferir testes que:

- usem banco temporario
- nao chamem Telegram real
- nao mexam em `data/forja_de_ferro.db`
- nao alterem `session.json` real
- testem comportamento pelo estado do banco

Bons proximos testes:

- funcoes de dieta
- falhas temporarias da API do Telegram
- migracoes de bancos antigos
- backup, exportacao e restauracao
