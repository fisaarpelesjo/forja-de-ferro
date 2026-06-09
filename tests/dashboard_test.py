import gc
import sqlite3
import sys
import tempfile
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from forja_de_ferro import dashboard
from forja_de_ferro import db_ops


def main():
    original_db_path = db_ops.DB_PATH
    original_data_dir = db_ops.DATA_DIR

    with tempfile.TemporaryDirectory(prefix="forja-de-ferro-dashboard-") as temp_dir:
        temp_path = Path(temp_dir)
        test_db = temp_path / "forja_de_ferro.db"
        output = temp_path / "dashboard.html"

        try:
            db_ops.DATA_DIR = temp_path
            db_ops.DB_PATH = test_db
            db_ops.init_db()

            sessao_1 = db_ops.create_session("2026-05-01")
            log_1 = db_ops.log_exercise(sessao_1, "Supino reto (barra)", 3, 5, 1)
            db_ops.update_log_weight(log_1, 40, 8)

            sessao_2 = db_ops.create_session("2026-05-08")
            log_2 = db_ops.log_exercise(sessao_2, "Supino reto (barra)", 3, 5, 1)
            db_ops.update_log_weight(log_2, 44, 9)
            log_3 = db_ops.log_exercise(sessao_2, "Remada curvada (barra)", 3, 8, 2)
            db_ops.update_log_weight(log_3, 50, None)

            dados = dashboard.carregar_dados()
            assert dados["resumo"]["sessoes"] == 2
            assert dados["resumo"]["volume_total"] == 2460.0
            assert dados["resumo"]["ultimo_volume"] == 1860.0
            assert dados["resumo"]["variacao_ultima"] == 1260.0
            assert dados["resumo"]["series_total"] == 9
            assert dados["resumo"]["repeticoes_total"] == 54
            assert dados["comparacao_ultima"][0]["delta_carga"] == 4.0
            assert dados["volume_semanal"]
            assert dados["volume_mensal"]
            assert dados["grupos_musculares"]
            assert dados["prs"]
            assert dados["media_movel"]
            assert dados["consistencia"]["semanas_com_treino"] == 2
            assert dados["volume_por_exercicio"][0]["melhor_1rm"] > 0
            assert dados["analises"]["volume_rpe_sessao"]
            assert dados["analises"]["rpe_distribuicao"]
            assert dados["analises"]["carga_rpe_exercicio"]

            alertas_rpe_9 = dashboard._calcular_alertas(
                [
                    {"volume": 1000, "rpe_medio": 9},
                    {"volume": 1000, "rpe_medio": 9},
                    {"volume": 1000, "rpe_medio": 9},
                ],
                [
                    {
                        "nome": "Supino reto (barra)",
                        "pontos": [
                            {"carga": 42, "rpe": 9},
                            {"carga": 42, "rpe": 9},
                            {"carga": 42, "rpe": 9},
                        ],
                    }
                ],
            )
            assert alertas_rpe_9 == []

            alertas_consolidacao = dashboard._calcular_alertas(
                [],
                [
                    {
                        "nome": "Supino reto (barra)",
                        "pontos": [
                            {"carga": 42, "rpe": 9},
                            {"carga": 42, "rpe": 8},
                        ],
                    }
                ],
            )
            assert "consolidou 42 kg" in alertas_consolidacao[0]

            alertas_reducao = dashboard._calcular_alertas(
                [],
                [
                    {
                        "nome": "Remada curvada (barra)",
                        "pontos": [
                            {"carga": 48, "rpe": 10},
                            {"carga": 46, "rpe": 9},
                        ],
                    }
                ],
            )
            assert "reducao de carga apos RPE 10" in alertas_reducao[0]

            caminho = dashboard.salvar_dashboard(output)
            html = caminho.read_text(encoding="utf-8")
            assert "Dashboard de treino" in html
            assert "Volume por sessao" in html
            assert "Carga e RPE por exercicio" in html
            assert "Ultima vs anterior" in html
            assert "Recordes pessoais" in html
            assert "Alertas" in html
            assert "1RM estimado" in html
            assert "Media movel de volume" in html
            assert "Consistencia" in html
            assert "Filtros rapidos" in html
            assert "data-aba=\"geral\"" in html
            assert "data-painel-aba=\"filtros\"" in html
            assert "data-aba=\"analises\"" in html
            assert "Volume x RPE medio" in html
            assert "Distribuicao de RPE" in html
            assert "Supino reto (barra)" in html
            assert "2.460 kg" in html

            conn = sqlite3.connect(test_db)
            try:
                assert conn.execute("SELECT COUNT(*) FROM training_sessions").fetchone()[0] == 2
            finally:
                conn.close()

            print("Teste do dashboard passou.")
        finally:
            db_ops.DB_PATH = original_db_path
            db_ops.DATA_DIR = original_data_dir
            gc.collect()


if __name__ == "__main__":
    main()
