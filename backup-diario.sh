#!/bin/bash
# Backup diario da Forja de Ferro: SQLite consistente + exportacao JSON,
# com rotacao (mantem os N mais recentes de cada tipo).
# Chamado pelo cron; ver 'crontab -l'.
set -euo pipefail

PROJETO=/root/forja-de-ferro
MANTER=14

cd "$PROJETO"
.venv/bin/python gerenciar_dados.py backup   >/dev/null
.venv/bin/python gerenciar_dados.py exportar >/dev/null

# Rotacao: remove os mais antigos alem de $MANTER, por tipo.
ls -1t backups/*.db      2>/dev/null | tail -n +$((MANTER+1)) | xargs -r rm --
ls -1t exportacoes/*.json 2>/dev/null | tail -n +$((MANTER+1)) | xargs -r rm --

echo "[$(date -Iseconds)] backup ok | $(ls -1 backups/*.db | wc -l) db, $(ls -1 exportacoes/*.json | wc -l) json"
