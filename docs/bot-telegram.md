# Bot Telegram

O bot Telegram fica em:

```text
forja_de_ferro/telegram_poller.py
```

Ele usa long polling pela API HTTP do Telegram. Nao ha webhook nem servidor web.

## Configuracao

O token fica em:

```text
.env
```

Formato esperado:

```text
TELEGRAM_TOKEN=seu_token_aqui
```

O bot so responde ao `CHAT_ID` configurado no codigo.

## Comandos Principais

```text
/gerar          cria uma sessao de treino
/prever         mostra uma previa sem salvar
/exercicios     lista exercicios atuais
/aquecimento    mostra o aquecimento
/volume         mostra volume por musculo
/status         mostra progresso
/desfazer       apaga o ultimo registro
/ajuda          mostra ajuda
```

Aliases em ingles podem continuar funcionando por compatibilidade:

```text
/generate
/exercises
/warmup
/undo
/help
```

## Startup

Fluxo normal:

```text
start_bot.py
  -> banner.print_banner()
  -> telegram_poller.main()
```

Se o token estiver ausente, o bot imprime:

```text
TELEGRAM_TOKEN nao encontrado no .env
```

e nao inicia o polling.

## Loop De Polling

`main()`:

1. inicia `offset = 0`
2. chama `get_updates(offset)`
3. atualiza `offset` para `update_id + 1`
4. ignora mensagens de outros chats
5. despacha comandos ou entrada de carga
6. dorme 3 segundos

`Ctrl+C` encerra o processo.

## `/gerar`

Cria uma nova sessao de treino.

Fluxo:

```text
handle_generate()
  -> ods_ops.generate_training()
  -> ods_ops.write_session(exercises, session_id)
  -> _format_training_msg(exercises)
  -> send(texto do treino)
  -> send("Sessao de treino gerada...")
```

O primeiro exercicio gerado atualmente e `Agachamento Zercher` (`3x5`).

O texto enviado lista cada exercicio com series, repeticoes, carga alvo e
descanso sugerido. Quando existe carga anterior para o exercicio, o alvo e
calculado pela ultima carga registrada e pelo RPE:

```text
RPE 7 ou menor  -> +4 kg
RPE 8           -> +2 kg
RPE 9           -> manter
RPE 10 ou maior -> -2 kg
Sem RPE         -> manter
```

No metodo adotado pelo projeto, RPE 9 mantem a carga para consolidar tecnica,
amplitude, controle e qualidade das repeticoes. Isso nao caracteriza estagnacao
por si so. Quando a mesma carga passar a RPE 8 ou menor, o bot sugere o aumento
correspondente no proximo treino.

Uma sequencia de RPE 9 so deve ser tratada como sinal de atencao quando houver
perda tecnica, repeticoes incompletas, piora de amplitude ou ausencia prolongada
de melhora na execucao.

Exemplo: se o treino anterior registrou `40 8`, o proximo `/gerar` mostra
`alvo: 42kg`. Se registrou `40 10`, o proximo `/gerar` mostra `alvo: 38kg`.

`Rosca martelo (barra H)` tem alvo inicial de 16 kg quando ainda nao houver
historico proprio. Depois do primeiro registro, ela segue a progressao normal
por RPE.

O descanso sugerido tambem vai em `session.json` como `rest_interval` e aparece
no `/status` e na indicacao do proximo exercicio.

Quando o exercicio atual ou o proximo exercicio tiver equipamento de peso fixo,
o bot tambem mostra a montagem da carga. Para `Tríceps testa` e
`Pullover (barra)`, a barra W pesa 6 kg, entao um alvo de 18 kg aparece como:

```text
barra W 6kg + 12kg de anilhas
```

Essa observacao nao aparece na lista `/exercicios`.

Para `Rosca martelo (barra H)`, a barra H pesa 9 kg. Um alvo de 18 kg aparece
como:

```text
barra H 9kg + 9kg de anilhas
```

## `/prever`

Mostra o treino no mesmo formato de `/gerar`, com alvo e descanso, mas nao
cria sessao real:

```text
handle_preview()
  -> ods_ops.preview_training()
  -> _format_training_msg(exercises)
  -> send(texto do treino)
  -> send("Previa do treino. Nada foi salvo...")
```

Esse comando nao cria linhas em `training_sessions`, nao cria `training_logs` e
nao escreve `session.json`. Ele pode inicializar o SQLite se o catalogo ainda
nao existir, porque le os exercicios ativos.

## Descanso Entre Series

Intervalos atuais:

```text
Agachamento Zercher, Supino reto principal, Levantamento Terra Romeno: 4 min
Remada curvada, Desenvolvimento: 3 min
Acessorios de tronco/ombro e supino reto back-off: 2 min
Rosca martelo (barra H), Triceps testa: 2 min
```

## `/exercicios`

Le os exercicios ativos do SQLite e envia uma tabela compacta.

## `/aquecimento`

Mostra um aquecimento curto, sem cargas prescritas, usando nomes em PT-BR:

```text
1. Agachamento livre — 1x10
2. Dobradiça de quadril — 1x10
3. Sustentação Zercher com barra vazia — 1x15s
4. Agachamento Zercher com barra vazia — 1x5
5. Agachamento Zercher leve — 1x3
6. Supino reto com barra vazia — 1x8
7. Supino reto leve — 1x3
```

## `/volume`

Le exercicios ativos, usa `ods_ops.MUSCLE_MAP` e calcula series por grupo
muscular. A estimativa semanal usa aproximadamente `3.5x` sessoes por semana.

## `/status`

Carrega `session.json`, conta quantos logs tem carga e informa:

- progresso atual
- exercicios ja feitos
- proximo exercicio
- treino completo quando todos os logs estao preenchidos

## `/desfazer`

Limpa o ultimo exercicio preenchido da sessao ativa.

Se nada foi preenchido, responde:

```text
Nada para desfazer.
```

## Entrada De Carga

Exemplos:

```text
80
80 8
80,5
80,5 8
```

Regras:

1. troca virgula por ponto
2. separa por espacos
3. primeiro valor vira `float`
4. segundo valor vira `int` se existir

Entrada invalida recebe:

```text
Formato: 80 8 (carga + RPE) ou 80 (somente carga)
```

## Formato Da Sessao Ativa

`session.json` contem:

```json
{
  "date": "YYYY-MM-DD",
  "session_id": 1,
  "exercises": [
    {
      "log_id": 1,
      "name": "Tríceps testa",
      "sets": 3,
      "reps": 8,
      "target_weight": 18.0,
      "rest_interval": "2 min",
      "loading_note": "barra W 6kg + 12kg de anilhas"
    }
  ]
}
```

Ao carregar o arquivo, o bot confirma que todos os logs pertencem a
`session_id` e que ainda existe pelo menos um exercicio pendente. Se o arquivo
nao existir, estiver corrompido ou apontar para uma sessao antiga, o bot
reconstroi o cache pela sessao SQLite mais recente com `weight IS NULL`.
Sessoes completas nao sao reabertas.

Se nao existir nenhuma sessao incompleta no SQLite, o bot pede `/gerar`.

## Falhas Comuns

Token ausente:

- bot nao inicia polling

Token errado:

- chamadas da API falham

Chat ID errado:

- bot recebe updates mas ignora mensagens

`session.json` ausente:

- o bot recupera a sessao SQLite mais recente com logs pendentes
- sem sessao incompleta, responde `Nenhuma sessao ativa. Use /gerar.`

SQLite travado:

- fechar visualizadores de banco
- parar outros processos Python
- pausar OneDrive se necessario

## Regra De Seguranca

O bot nao deixa o usuario escolher diretamente uma linha do banco. Ele usa os
`log_id` da sessao ativa e a contagem de linhas preenchidas para decidir qual
exercicio recebera a proxima carga.
