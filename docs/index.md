# Documentacao Da Forja de Ferro

Esta pasta contem a documentacao detalhada do projeto.

As referencias cientificas e notas de treino ficam separadas em
[`referencias-treino/`](referencias-treino/). A raiz de `docs/` fica focada
na documentacao do software.

## Documentos Do Projeto

- [Visao geral do sistema](visao-geral.md): o que o projeto faz, quais
  arquivos importam e como os dados circulam.
- [Arquitetura](arquitetura.md): layout do pacote, fronteiras de modulos,
  launchers, estado local e direcao de dependencias.
- [Banco de dados](banco-de-dados.md): SQLite, tabelas, relacoes, fonte da verdade e
  comandos seguros de inspecao, incluindo o dashboard local de volume.
- [Bot Telegram](bot-telegram.md): comandos, parsing de entrada, fluxo de
  mensagens, polling e falhas comuns.
- [Testes](testes.md): smoke test, teste ponta a ponta, o que cada um garante e
  como adicionar novos testes.
- [Portabilidade](portabilidade.md): Windows, Linux, macOS, WSL, maquinas fracas,
  terminal, Python e problemas comuns de ambiente.
- [Operacao](operacao.md): uso diario, setup limpo, backup, troubleshooting e
  checklist de manutencao.
- [Melhorias futuras](melhorias-futuras.md): roadmap tecnico priorizado, riscos,
  criterios de conclusao e itens que nao sao prioridade.

## Referencias De Treino

A pasta `referencias-treino/` contem notas de pesquisa e material de treino que
apoiam o projeto, mas nao fazem parte da arquitetura do software:

- [Forca e hipertrofia: carga baixa vs alta](referencias-treino/forca_hipertrofia_carga_baixa_vs_alta.md)
- [Forca e hipertrofia: versao aceita](referencias-treino/forca_hipertrofia_carga_baixa_vs_alta_versao_aceita.md)
- [Frequencia de treino e hipertrofia](referencias-treino/frequencia_treino_hipertrofia.md)
- [Maximizando forca em atletas](referencias-treino/maximizando_forca_atletas.md)
- [Periodizacao nao linear flexivel](referencias-treino/periodizacao_nao_linear_flexivel.md)
- [Agachamento Zercher e eletromiografia em variacoes de agachamento](referencias-treino/agachamento_zercher_eletromiografia_variacoes.md)
- [Agachamento Zercher em forca de costas e pernas de jogadores de basquete](referencias-treino/agachamento_zercher_forca_basquete.md)
- [Forca e alongamento dos isquiotibiais: levantamento terra romeno e corrida](referencias-treino/forca_alongamento_isquiotibiais_levantamento_terra_romeno_corrida.md)
- [Agachamento, levantamento terra romeno e elevacao pelvica](referencias-treino/agachamento_levantamento_terra_romeno_elevacao_pelvica_eletromiografia.md)
- [Levantamento terra romeno, romeno em plataforma e pernas estendidas](referencias-treino/levantamento_terra_romeno_plataforma_pernas_estendidas_eletromiografia.md)
- [Levantamento terra convencional vs. levantamento terra romeno](referencias-treino/levantamento_terra_convencional_vs_romeno_eletromiografia_cinetica.md)
- [Levantamento terra e suas variacoes: revisao sistematica](referencias-treino/levantamento_terra_variacoes_eletromiografia_revisao_sistematica.md)

## Caminho Rapido

Na raiz do repositorio:

```bash
pip install -r requirements.txt
python tests/smoke_test.py
python tests/regras_treino_test.py
python tests/e2e_training_flow_test.py
python tests/dashboard_test.py
python tests/backup_export_test.py
python tests/telegram_falhas_test.py
python start_bot.py
```

No Linux/macOS, use `python3` se necessario:

```bash
python3 tests/smoke_test.py
python3 tests/regras_treino_test.py
python3 tests/e2e_training_flow_test.py
python3 tests/dashboard_test.py
python3 tests/backup_export_test.py
python3 tests/telegram_falhas_test.py
python3 start_bot.py
```
