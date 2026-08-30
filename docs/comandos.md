# Catalogo De Comandos

Este arquivo e a referencia unica dos comandos do Limulus.

## Bot Do Telegram

Todos os comandos textuais devem ser enviados com `/`.

| Comando | Finalidade |
| --- | --- |
| `/gerar` | Cria uma sessao de treino no SQLite. |
| `/prever` | Mostra o proximo treino sem salvar sessao ou logs. |
| `/treinob` | Mostra o Treino B de garagem com pesos calculados pelo treino principal. |
| `/exercicios` | Lista os exercicios do plano ativo. |
| `/aquecimento` | Mostra a sequencia de aquecimento. |
| `/volume` | Mostra o volume por grupo muscular. |
| `/dashboard` | Atualiza o dashboard HTML local. |
| `/planos` | Lista os planos de treino cadastrados. |
| `/plano NOME` | Seleciona o plano ativo. |
| `/peso VALOR` | Registra o peso corporal em quilogramas. |
| `/peso` | Mostra o peso atual, a variacao e as ultimas medicoes. |
| `/cintura VALOR` | Registra a circunferencia da cintura em centimetros. |
| `/cintura` | Mostra a cintura atual, a variacao e as ultimas medicoes. |
| `/status` | Mostra o exercicio atual e o progresso da sessao. |
| `/desfazer` | Remove a carga e o RPE do ultimo registro preenchido. |
| `/ajuda` | Mostra a ajuda principal do bot. |
| `80` | Registra 80 kg no proximo exercicio pendente. |
| `80 8` | Registra 80 kg com RPE 8. |

Entradas numericas como `80` e `80 8` nao usam `/`, pois registram carga e RPE
em vez de acionar um comando textual.

## Muay Thai — Fundamentos (Com Saco Leve)

Fase anterior ao ciclo de 8 semanas: aprender cada movimento isolado, sem
combinacao. Conta repeticao em vez de round, porque a dosagem aqui e numero de
execucoes limpas, nao tempo sob esforco.

Cada sessao tem **duas partes**. Os blocos de aprendizado sao de mao nua, de
frente para o espelho — sem impacto voce enxerga o punho e corrige. O bloco
final e no saco, com bandagem e luva, limitado a 20-30% de potencia: ali o saco
responde o que o espelho nao responde (distancia, alinhamento, ponto de
contato), sem que um erro vire lesao.

O bloco de saco da sessao C tem um **portao**: so acontece se o giro do pe de
apoio ja sair automatico. Chutar sem esse giro e o mecanismo de lesao de joelho
que a fase inteira existe para evitar.

A unica tecnica que continua fora dos fundamentos e `corda`, que e
condicionamento do aquecimento de sabado no ciclo de 8 semanas.

| Comando | Acao |
| --- | --- |
| `/fundamentos` | Explica a fase, marca a sessao de hoje e lista os criterios de passagem. |
| `/fundamentos a` | Postura, guarda, deslocamento, jab e direto. |
| `/fundamentos b` | Gancho, jab no corpo, bloqueio, saida lateral e prancha. |
| `/fundamentos c` | Giro do pe de apoio, teep, joelhada e chute baixo. |

`/proximo` e `/mtparar` funcionam igual aqui: e a mesma maquina de blocos. As
sessoes seguem terca, quinta e sabado, repetidas por 2 a 3 semanas.

Os roteiros de fundamentos carregam `usa_progressao: False`, e por isso nao
mostram semana nem potencia maxima — nao ha impacto para dosar.

## Muay Thai (Saco)

Ciclo de 8 semanas em terca, quinta e sabado, complementando a musculacao de
segunda, quarta e sexta. Nenhum comando desta secao grava no banco: o estado do
roteiro fica em `mt_session.json`, separado de `session.json`.

| Comando | Acao |
| --- | --- |
| `/mt` | Roteiro de hoje. Em dia de musculacao, avisa e nao inicia. |
| `/mtterca` | Forca o roteiro de terca. Idem `/mtquinta` e `/mtsabado`. |
| `/mtterca 3` | Mesmo roteiro, na semana 3 da progressao (1 a 8). |
| `/proximo` | Avanca um bloco. No ultimo bloco, encerra o roteiro. |
| `/mtparar` | Encerra o roteiro em andamento. |
| `/mtregras` | Regras de seguranca do ciclo. |
| `/tecnicas` | Indice das 20 tecnicas da biblioteca de execucao. |
| `/como NOME` | O essencial do movimento: 2-3 pistas e os 2 piores erros. |
| `/como NOME tudo` | Passo a passo completo, com posicao inicial, rotacao e checagem. |

`/como NOME` responde curto (~340 caracteres): as 2-3 pistas que mantem o
movimento seguro e os dois piores erros. E a versao para consultar entre uma
serie e outra, que e quando a instrucao e realmente lida.

`/como NOME tudo` traz as seis secoes completas: posicao inicial, execucao
numerada, **o que gira / quanto / quando**, retorno, como conferir que esta
certo, e erros comuns. Aceita tambem `completo`, `detalhe` e `full` como
sufixo. As tecnicas estaticas (`prancha`, `respiracao`, `bandagem`) nao tem a
secao de giro. Instrucoes escritas para destro, declarado em toda resposta.

As respostas detalhadas podem passar do limite de 4096 caracteres do Telegram;
`muaythai.dividir_mensagem()` quebra em partes na linha em branco em vez de a
instrucao ser encurtada.

`/como` aceita acento, espaco, hifen e alias: `/como chute baixo`,
`/como low kick`, `/como guarda`, `/como 2` e `/como enfaixar` resolvem. Um
prefixo so resolve se for inequivoco, entao `/como j` devolve o indice em vez
de escolher `jab` por conta propria.

Cada bloco do roteiro termina com os atalhos `/como` dos movimentos que ele
usa, em vez de embutir o passo a passo inteiro, porque o Telegram corta
mensagem em 4096 caracteres.

## Iniciar O Bot

Multiplataforma:

```bash
python start_bot.py
```

Windows:

```powershell
.\start_bot.bat
```

## Dashboard

Gerar `temp/dashboard-treino.html`:

```bash
python gerar_dashboard.py
```

## Videos E Frames

Coloque os arquivos em `videos/entrada/`.

Processar todos os videos e instalar o `ffmpeg` quando necessario:

```bash
python gerar_frames.py --todos --instalar-ffmpeg
```

Gerar um frame por segundo:

```bash
python gerar_frames.py --todos --instalar-ffmpeg --fps 1
```

Processar apenas um video:

```bash
python gerar_frames.py video.mp4 --instalar-ffmpeg
```

Definir pasta base de saida:

```bash
python gerar_frames.py video.mp4 --saida temp/frames
```

Definir formato das imagens:

```bash
python gerar_frames.py video.mp4 --formato png
```

Formatos aceitos: `jpg`, `jpeg`, `png`, `webp` e `bmp`.

Exibir todas as opcoes:

```bash
python gerar_frames.py --help
```

## Backup, Exportacao E Restauracao

Criar backup:

```bash
python gerenciar_dados.py backup
python gerenciar_dados.py backup --destino backups
```

Exportar os dados para JSON:

```bash
python gerenciar_dados.py exportar
python gerenciar_dados.py exportar --destino exportacoes
```

Restaurar um backup:

```bash
python gerenciar_dados.py restaurar backups/arquivo.db --confirmar
```

Sem `--confirmar`, a restauracao e cancelada.

Exibir a ajuda:

```bash
python gerenciar_dados.py --help
```

## Testes

Teste de fumaca:

```bash
python tests/smoke_test.py
```

Regras de treino:

```bash
python tests/regras_treino_test.py
```

Videos e frames:

```bash
python tests/video_ops_test.py
```

Fluxo completo de treino:

```bash
python tests/e2e_training_flow_test.py
```

Dashboard:

```bash
python tests/dashboard_test.py
```

Backup e exportacao:

```bash
python tests/backup_export_test.py
```

Falhas do Telegram:

```bash
python tests/telegram_falhas_test.py
```

## Instalacao E Verificacao

Instalar dependencias Python:

```bash
python -m pip install -r requirements.txt
```

Verificar o `ffmpeg`:

```bash
ffmpeg -version
```

Verificar a versao do Python:

```bash
python --version
```
