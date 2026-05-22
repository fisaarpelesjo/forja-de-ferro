# Portabilidade

A Forja de Ferro foi feito para rodar em maquinas comuns e fracas.

Runtime:

```text
Python 3.10+
SQLite
requests
rich
internet de saida
```

Nao precisa de Docker, servidor web ou banco externo.

## Ambientes Esperados

Deve funcionar em:

- Windows
- Linux
- macOS
- WSL
- Raspberry Pi ou Linux pequeno com Python 3.10+
- VPS barata
- notebook antigo com Python moderno

Pode dar trabalho em:

- sistema sem Python 3.10+
- maquina sem internet
- ambiente sem permissao para instalar pacote
- terminal sem suporte ANSI
- pasta sincronizada com lock agressivo

## Comandos Python

Windows:

```bat
py -3 start_bot.py
python start_bot.py
```

Linux/macOS:

```bash
python3 start_bot.py
```

Verifique:

```bash
python --version
python3 --version
py -3 --version
```

## Instalar Dependencias

```bash
pip install -r requirements.txt
```

Se `pip` apontar para Python errado:

```bash
python -m pip install -r requirements.txt
python3 -m pip install -r requirements.txt
py -3 -m pip install -r requirements.txt
```

## Cor No Terminal

O banner usa `rich`. Se o terminal nao renderizar cor, o bot ainda funciona. Cor
e cosmetica.

## Maquina Fraca

O app faz:

- requests HTTP simples
- leituras/escritas SQLite
- JSON local
- sleep entre polls

Gargalos provaveis:

- internet ruim
- Python mal instalado
- permissao de arquivo
- lock do SQLite
- OneDrive ou sincronizador

## OneDrive

SQLite costuma funcionar em pasta sincronizada, mas locks podem acontecer.

Se travar:

1. feche visualizadores SQLite
2. pare outros bots/processos Python
3. pause sincronizacao
4. mova o repo para pasta nao sincronizada se persistir

## Checklist De Maquina Nova

```bash
pip install -r requirements.txt
copy .env.example .env
python tests/smoke_test.py
python tests/e2e_training_flow_test.py
python start_bot.py
```

Linux/macOS:

```bash
python3 -m pip install -r requirements.txt
cp .env.example .env
python3 tests/smoke_test.py
python3 tests/e2e_training_flow_test.py
python3 start_bot.py
```
