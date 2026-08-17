# Operacao

Este documento explica como rodar, manter e depurar a Forja de Ferro.

## Uso Diario

1. Inicie o bot.
2. Abra o Telegram.
3. Envie `/gerar`.
4. Use `alvo` como carga sugerida e `descanso` como intervalo entre series.
5. Envie cargas conforme terminar os exercicios.
6. Use `/status` para ver progresso.
7. Use `/desfazer` se registrou algo errado.
8. Pare o bot com `Ctrl+C`.

## Iniciar O Bot

Multiplataforma:

```bash
python start_bot.py
```

Linux/macOS se necessario:

```bash
python3 start_bot.py
```

Windows:

```bat
start_bot.bat
```

## Primeiro Setup

```bash
pip install -r requirements.txt
copy .env.example .env
python tests/smoke_test.py
python tests/e2e_training_flow_test.py
```

Linux/macOS:

```bash
python3 -m pip install -r requirements.txt
cp .env.example .env
python3 tests/smoke_test.py
python3 tests/e2e_training_flow_test.py
```

Edite `.env` e configure:

```text
TELEGRAM_TOKEN=seu_token_real
```

## Comandos Do Bot

```text
/gerar          Cria uma nova sessao de treino
/prever         Mostra o treino sem salvar sessao ou logs
/treinob        Mostra o Treino B de garagem com pesos calculados
/exercicios     Lista exercicios ativos
/aquecimento    Mostra aquecimento
/volume         Mostra estimativa de volume
/status         Mostra progresso
/desfazer       Limpa o ultimo registro
/ajuda          Mostra ajuda
```

Entrada de carga:

```text
80
80 8
80,5
80,5 8
```

Use `/prever` quando quiser conferir formato, alvo e descanso sem iniciar uma
sessao real.

Use `/treinob` nos dias sem treino principal para receber o treino de garagem
com 10 voltas e peso unico por exercicio. Ele calcula os pesos a partir dos alvos atuais do
treino principal, mostra a montagem da carga e nao cria sessao, logs,
`session.json` nem registros de RPE.

Ao registrar o ultimo exercicio, o bot envia automaticamente o resumo da sessao.
Nao e necessario executar outro comando.

Para trabalhar com modelos A/B:

```text
/planos
/plano A
/plano B
```

O repositorio migra o treino atual como plano `A`. Um plano `B` so aparece
depois de ser cadastrado no SQLite; nenhum treino alternativo e inventado
automaticamente.

Para atualizar o dashboard pelo celular:

```text
/dashboard
```

O HTML continua salvo localmente em `temp/dashboard-treino.html`.

## Gerar Frames De Video

Quando quiser revisar uma execucao gravada, use o launcher local:

1. coloque o video em `videos/entrada/`
2. processe todos os arquivos com verificacao e instalacao do `ffmpeg`

```bash
python gerar_frames.py --todos --instalar-ffmpeg
```

Sem `--fps`, todos os frames sao extraidos. Use `--fps 1` para gerar uma imagem
por segundo. O launcher cria `videos/saida/<nome-do-video>/` para cada arquivo e
informa a quantidade gerada. JPG, JPEG, PNG, WebP e BMP sao aceitos.

No Windows, `--instalar-ffmpeg` usa o `winget` se a dependencia estiver ausente.
Frames anteriores daquele video sao removidos antes da nova extracao, evitando
arquivos obsoletos e contagem incorreta.

## Progressao De Carga Por RPE

Ao gerar treino, o bot sugere a proxima carga usando a ultima carga registrada
no exercicio e o RPE:

```text
RPE 7 ou menor  -> +4 kg
RPE 8           -> +2 kg
RPE 9           -> manter
RPE 10 ou maior -> -2 kg
Sem RPE         -> manter
```

RPE 9 e uma etapa de consolidacao, nao uma indicacao automatica de estagnacao.
Enquanto a carga ainda estiver em RPE 9, mantenha-a para melhorar tecnica,
amplitude, controle e qualidade das repeticoes. Quando a mesma carga passar a
RPE 8 ou menor, o proximo treino recebe o aumento previsto pela regra.

Considere uma sequencia de RPE 9 um ponto de atencao apenas se ela vier
acompanhada de perda tecnica, repeticoes incompletas, piora de amplitude ou
ausencia prolongada de melhora na execucao.

```text
Hoje: 40 8
Proximo /gerar: alvo 42 kg

Hoje: 40 10
Proximo /gerar: alvo 38 kg
```

Se nao houver historico para o exercicio, o alvo aparece como `-`. Registre
sempre a carga real feita; ela sera a base do proximo alvo.

## Descanso Entre Series

O `/gerar` mostra descanso fixo sugerido por exercicio. Use esses tempos como
base para preservar a qualidade tecnica:

```text
Compostos pesados, Supino reto back-off e Supino inclinado (barra): 4 min
Compostos medios e Rosca martelo (barra H): 3 min
Acessorios: 2 min
```

## Arquivos Para Backup

Principal:

```text
data/forja_de_ferro.db
```

Criar backup consistente:

```bash
python gerenciar_dados.py backup
```

Exportar o conteudo para JSON:

```bash
python gerenciar_dados.py exportar
```

Restaurar um backup:

```bash
python gerenciar_dados.py restaurar backups/arquivo.db --confirmar
```

Pare o bot antes de restaurar. A operacao valida o backup e cria uma copia de
seguranca do banco atual.

Estado local opcional:

```text
session.json
```

Se `session.json` for apagado ou corrompido durante um treino, envie `/status`
ou a proxima carga normalmente. O bot tenta reconstruir a sessao mais recente
que ainda possui logs pendentes no SQLite.

Segredo local:

```text
.env
```

Nao publique `.env`.

## Arquivos Que Ficam Locais

Nao commitar:

```text
.env
session.json
pending_log.csv
temp/
backups/
exportacoes/
data/*.db-shm
data/*.db-wal
__pycache__/
*.pyc
```

## Atualizar Exercicios

O catalogo de exercicios fica no SQLite.

Codigo:

```text
forja_de_ferro/db_ops.py
  -> tabela exercises
```

Use os helpers quando possivel:

```python
from forja_de_ferro import db_ops

db_ops.list_exercises()
db_ops.replace_exercises([...])
```

Nao substituir a fonte da verdade SQLite por planilha.

Catalogo atual:

- `Agachamento com barra nas costas` e o primeiro exercicio e esta como `3x5`.
- Ele usa a barra apoiada no trapezio/ombro.
- `Agachamento sumô com barra à frente` e o segundo exercicio e esta como `3x10`.
- `Remada curvada alta no peito (barra)` e o setimo exercicio e esta como `3x10`.
- `Rosca martelo (barra H)` e o decimo exercicio e esta como `3x8`.
- Ela substitui `Rosca direta` em sessoes futuras para usar a barra H de 9 kg.
- `Supino fechado (barra)` e `Remada alta (barra)` estao inativos para sessoes futuras.
- Historico antigo pode continuar com nomes antigos ou inativos.
- Se o catalogo mudar de novo, atualizar `data/forja_de_ferro.db` e `forja_de_ferro/db_ops.py`.

## Problemas Comuns

### Falha De Rede No Telegram

O bot registra a falha e aumenta gradualmente a espera entre tentativas, ate 60
segundos. Nao e necessario reiniciar para uma interrupcao temporaria.

### Token Invalido

O polling encerra com uma mensagem clara. Corrija `TELEGRAM_TOKEN` em `.env` e
inicie novamente. O token nunca deve aparecer no terminal ou em arquivos de log.

### `TELEGRAM_TOKEN nao encontrado no .env`

Crie `.env` a partir de `.env.example` e configure o token.

### Bot inicia mas ignora mensagens

Possiveis causas:

- `CHAT_ID` diferente
- token de outro bot
- updates antigos no Telegram

### `Nenhuma sessao ativa. Use /gerar.`

Voce enviou carga antes de gerar treino, ou `session.json` foi apagado.

### SQLite travado

Feche DB Browser, outros processos Python e pause sincronizacao de OneDrive se
isso persistir.

## Checklist De Manutencao

Antes de push:

```bash
python tests/smoke_test.py
python tests/e2e_training_flow_test.py
```

Checagem de sintaxe:

```bash
python -m py_compile start_bot.py forja_de_ferro/*.py tests/*.py
```

Antes de commitar:

```bash
git status --short
git diff --check
```
