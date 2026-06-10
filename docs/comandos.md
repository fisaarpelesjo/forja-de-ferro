# Catalogo De Comandos

Este arquivo e a referencia unica dos comandos da Forja de Ferro.

## Bot Do Telegram

Todos os comandos textuais devem ser enviados com `/`.

| Comando | Finalidade |
| --- | --- |
| `/gerar` | Cria uma sessao de treino no SQLite. |
| `/prever` | Mostra o proximo treino sem salvar sessao ou logs. |
| `/exercicios` | Lista os exercicios do plano ativo. |
| `/aquecimento` | Mostra a sequencia de aquecimento. |
| `/volume` | Mostra o volume por grupo muscular. |
| `/dashboard` | Atualiza o dashboard HTML local. |
| `/planos` | Lista os planos de treino cadastrados. |
| `/plano NOME` | Seleciona o plano ativo. |
| `/status` | Mostra o exercicio atual e o progresso da sessao. |
| `/desfazer` | Remove a carga e o RPE do ultimo registro preenchido. |
| `/ajuda` | Mostra a ajuda principal do bot. |
| `80` | Registra 80 kg no proximo exercicio pendente. |
| `80 8` | Registra 80 kg com RPE 8. |

Entradas numericas como `80` e `80 8` nao usam `/`, pois registram carga e RPE
em vez de acionar um comando textual.

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
