# Bot Telegram

O bot Telegram fica em:

```text
forja_de_ferro/telegram_poller.py
```

Ele usa long polling pela API HTTP do Telegram. Nao ha webhook nem servidor web.

## Logs E Falhas De Rede

O terminal mostra logs com data, hora, nivel e contexto. Comandos sao
identificados pelo nome; entradas de peso aparecem apenas como
`registro_carga`, sem registrar o valor enviado. Quando existe sessao ativa, o
log inclui `session_id`.

O token e a URL completa da API nunca devem aparecer nos logs.

- falha temporaria no polling: espera 3 segundos e dobra gradualmente ate 60
- falha temporaria ao enviar: repete depois de 1 e 2 segundos
- token invalido ou bot inexistente: registra erro permanente e encerra
- resposta temporariamente invalida: trata como falha de rede e tenta novamente

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
/treinob        mostra o treino B de garagem
/exercicios     lista exercicios atuais
/aquecimento    mostra o aquecimento
/volume         mostra volume por musculo
/dashboard      atualiza o dashboard local
/planos         lista planos de treino
/plano NOME     seleciona o plano ativo
/peso VALOR     registra o peso corporal
/peso           mostra o peso atual e o historico
/cintura VALOR  registra a circunferencia da cintura em cm
/cintura        mostra a cintura atual e o historico
/status         mostra progresso
/desfazer       apaga o ultimo registro
/ajuda          mostra ajuda
```

Todos os comandos textuais exigem `/` e usam somente os nomes oficiais em
PT-BR. Entradas numericas continuam reservadas para carga e RPE.

## `/peso`

`/peso 118`, `/peso 118,5` e `/peso 118.5` registram uma nova medicao em
quilogramas com data e horario. O valor deve ficar entre 30 e 400 kg.

`/peso` sem valor mostra o peso atual, a variacao desde a medicao anterior e as
cinco entradas mais recentes. Cada registro e preservado no historico.

## `/cintura`

`/cintura 110`, `/cintura 110,5` e `/cintura 110.5` registram uma nova
medicao em centimetros com data e horario. O valor deve ficar entre 40 e
250 cm.

`/cintura` sem valor mostra a circunferencia atual, a variacao desde a medicao
anterior e as cinco entradas mais recentes. Cada registro e preservado no
historico.

## Startup

Fluxo normal:

```text
start_bot.py
  -> telegram_poller.main()
```

O launcher nao imprime banner. A saida de terminal fica restrita aos logs do
polling e a erros de configuracao.

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
  -> send("Agora faca..." com o primeiro exercicio)
```

O primeiro exercicio gerado atualmente e `Agachamento com barra nas costas` (`3x5`).
O segundo e `Agachamento sumô com barra à frente` (`3x10`), com foco principal
nos adutores.

O texto enviado lista cada exercicio com series, repeticoes, carga alvo e
descanso sugerido. Depois da lista, o bot envia tambem o primeiro exercicio a
executar no mesmo formato usado para indicar o proximo exercicio apos um
registro de carga. Quando existe carga anterior para o exercicio, o alvo e
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

`Rosca martelo (barra H)` tem alvo inicial de 16 kg e `Supino inclinado (barra)`
tem alvo inicial de 41 kg quando ainda nao houver historico proprio. Depois do
primeiro registro, seguem a progressao normal por RPE.

O descanso sugerido tambem vai em `session.json` como `rest_interval` e aparece
no `/status` e na indicacao do proximo exercicio.

Quando o exercicio atual ou o proximo exercicio tiver equipamento de peso fixo,
o bot tambem mostra a montagem da carga. Nos supinos com barra, `Agachamento com barra nas costas`,
`Agachamento sumô com barra à frente`, `Remada curvada (barra)`,
`Desenvolvimento (barra em pé)`, `Levantamento Terra Romeno` e `Remada curvada
alta no peito (barra)`, a barra reta de 2,20 m pesa 11 kg. Um alvo de 40 kg
aparece como:

```text
barra reta 2,20 m 11kg + 29kg de anilhas
```

Para `Tríceps testa` e `Pullover (barra)`, a barra W pesa 6 kg, entao um alvo
de 18 kg aparece como:

```text
barra W 6kg + 12kg de anilhas
```

Essa observacao nao aparece na lista `/exercicios`.

Os nomes exibidos podem omitir qualificadores de equipamento, como `(barra)`,
`(barra H)` e `(barra em pé)`. Essa limpeza e apenas visual; o SQLite conserva
os nomes completos para historico e progressao.

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

## `/treinob`

Mostra o Treino B de garagem com 10 voltas fixas, sem criar sessao, logs ou
`session.json`.

Fluxo:

```text
handle_training_b()
  -> ods_ops.build_training_b()
  -> _format_training_b_msg(exercises)
  -> send(texto do treino B)
```

O Treino B usa pesos unicos calculados pelos alvos atuais do treino principal,
sem pedir nem registrar RPE:

```text
Farmer walk ida e volta             -> 45% do Levantamento Terra Romeno
Remada leve com barra               -> 60% da Remada curvada
```

Os pesos sao arredondados para carga montavel. Quando houver carga, o bot
mostra a montagem: barra reta de 2,50 m com 9 kg para remada com barra, e barra
de 40 cm para farmer walk. Marcha forte no lugar, agachamento com pausa,
flexao e sombra de boxe ou corda sem corda usam peso corporal.

## Descanso Entre Series

Intervalos atuais:

```text
Agachamento com barra nas costas, Supino reto principal, Supino reto back-off, Supino inclinado (barra), Desenvolvimento, Levantamento Terra Romeno: 4 min
Remada curvada, Rosca martelo (barra H): 3 min
Acessorios restantes: 2 min
```

## `/exercicios`

Le os exercicios ativos do SQLite e envia uma tabela compacta.

## `/aquecimento`

Mostra um aquecimento dinamico curto de corpo todo, pensado para durar cerca
de 5 minutos sem virar um segundo treino:

```text
1. Marcha rapida ou polichinelo leve — 60s
2. Circulos de braco e abrir/fechar bracos — 30s
3. Rotacao de tronco — 30s
4. Agachamento livre — 1x10
5. Afundo alternado ou passada para tras — 1x6 por perna
6. Bom dia sem peso ou com barra vazia — 1x10
7. Flexao facil — 1x5-8
8. Prancha com toque no ombro — 10 toques
```

## `/volume`

Le exercicios ativos e consulta `exercise_muscle_groups` no SQLite para calcular
series por grupo principal e secundario. A estimativa semanal usa
aproximadamente `3.5x` sessoes por semana. Bot e dashboard usam essa mesma fonte.

## `/planos` E `/plano NOME`

`/planos` lista os modelos cadastrados, quantidade de exercicios e qual esta
ativo. `/plano NOME` troca o plano ativo.

O plano selecionado passa a ser usado por:

- `/gerar`
- `/prever`
- `/exercicios`
- `/volume`

A troca nao altera sessoes antigas nem uma sessao ja gerada. Novos planos sao
cadastrados por `db_ops.replace_training_plan()`.

## `/dashboard`

Executa `dashboard.salvar_dashboard()` e atualiza
`temp/dashboard-treino.html`. A resposta informa horario, ultima sessao, volume
e RPE medio geral.

O comando:

- nao cria ou altera sessoes e logs
- nao envia o caminho local do arquivo
- nao envia o HTML completo
- registra falhas no terminal e responde de forma curta no Telegram

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

### Resumo Ao Concluir

Quando o ultimo exercicio recebe carga, a mesma resposta inclui:

- volume total e RPE medio
- diferenca de volume para a sessao anterior compativel
- aumentos e reducoes de carga
- consolidacoes confirmadas
- cargas mantidas em RPE 9
- recordes de carga ou volume

Uma sessao e compativel para comparacao quando possui a mesma sequencia de
exercicios preenchidos. Manter RPE 9 nao e chamado de consolidacao confirmada;
essa classificacao exige queda do RPE 9 para 8 ou menos com a mesma carga.

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
