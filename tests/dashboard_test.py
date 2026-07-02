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
from forja_de_ferro import telegram_poller


def main():
    original_db_path = db_ops.DB_PATH
    original_data_dir = db_ops.DATA_DIR
    original_output = telegram_poller.DASHBOARD_OUTPUT
    original_send = telegram_poller.send

    with tempfile.TemporaryDirectory(prefix="forja-de-ferro-dashboard-") as temp_dir:
        temp_path = Path(temp_dir)
        test_db = temp_path / "forja_de_ferro.db"
        output = temp_path / "dashboard.html"
        bot_output = temp_path / "dashboard-bot.html"
        sent_messages = []

        try:
            db_ops.DATA_DIR = temp_path
            db_ops.DB_PATH = test_db
            telegram_poller.DASHBOARD_OUTPUT = bot_output
            telegram_poller.send = sent_messages.append
            db_ops.init_db()

            leite_id = db_ops.upsert_food(
                "Leite semidesnatado",
                "copo",
                250,
                protein_g=8,
                carbo_g=12,
                fat_g=3,
                calories=105,
                potassium_mg=375,
                magnesium_mg=25,
                zinc_mg=1,
                vitamin_d_ui=100,
                vitamin_b6_mg=0.1,
            )
            frango_id = db_ops.upsert_food(
                "Peito de frango",
                "g",
                100,
                protein_g=23,
                fat_g=1,
                calories=101,
                potassium_mg=256,
                magnesium_mg=29,
                zinc_mg=1,
                vitamin_b6_mg=0.6,
            )
            db_ops.add_diet_entry("Cafe", leite_id, 1, 1)
            db_ops.add_diet_entry("Almoco", frango_id, 200, 2)
            db_ops.add_diet_entry("Janta", leite_id, 2, 3)
            db_ops.set_diet_targets(
                protein_g=100,
                carbo_g=150,
                fat_g=60,
                calories=2000,
                potassium_mg=3400,
                magnesium_mg=400,
                zinc_mg=11,
                vitamin_d_ui=1000,
                vitamin_b6_mg=1.3,
            )
            db_ops.set_body_profile(183, 30)
            db_ops.add_body_weight(
                118,
                source="teste",
                recorded_at="2026-05-07 08:00:00",
            )
            db_ops.add_body_weight(
                117.5,
                source="teste",
                recorded_at="2026-05-08 08:00:00",
            )
            db_ops.add_waist_measurement(
                112,
                source="teste",
                recorded_at="2026-05-07 08:00:00",
            )
            db_ops.add_waist_measurement(
                110.5,
                source="teste",
                recorded_at="2026-05-08 08:00:00",
            )

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
            assert dados["equilibrio_muscular"]
            assert dados["prs_expandidos"]
            assert dados["heatmap_sessoes"]
            assert dados["relatorio_semanal"]["sessoes"] > 0
            assert dados["mapa_ultima_sessao"]["data"] == "2026-05-08"
            assert len(dados["dieta"]["itens"]) == 2
            assert dados["dieta"]["itens"][0]["name"] == "Leite semidesnatado"
            assert dados["dieta"]["itens"][0]["quantity"] == 3.0
            assert dados["dieta"]["itens"][0]["protein_g"] == 24.0
            assert dados["dieta"]["itens"][1]["protein_g"] == 46.0
            assert dados["dieta"]["totais"]["calories"] == 517.0
            assert dados["dieta"]["metas"]["protein_g"] == 100.0
            assert dados["peso_corporal"]["atual"]["weight_kg"] == 117.5
            assert dados["peso_corporal"]["variacao"] == -0.5
            assert dados["cintura"]["atual"]["circumference_cm"] == 110.5
            assert dados["cintura"]["variacao"] == -1.5
            assert dados["perfil_corporal"]["height_cm"] == 183.0
            assert dados["perfil_corporal"]["age_years"] == 30
            assert round(dados["composicao_corporal"]["imc"], 1) == 35.1
            assert round(dados["composicao_corporal"]["meta_peso_kg"], 1) == 83.4
            assert (
                dados["composicao_corporal"]["meta_cintura_cm"]
                == 91.5
            )
            assert round(
                dados["composicao_corporal"]["progresso_peso"],
                1,
            ) == 71.0
            assert round(
                dados["composicao_corporal"]["progresso_cintura"],
                1,
            ) == 82.8
            assert (
                round(
                    dados["composicao_corporal"]["relacao_cintura_altura"],
                    2,
                )
                == 0.60
            )
            grupos_mapa = {
                item["grupo"]: item
                for item in dados["mapa_ultima_sessao"]["grupos"]
            }
            assert round(grupos_mapa["Peitoral superior"]["volume"], 1) == 132.0
            assert round(grupos_mapa["Peitoral inferior"]["volume"], 1) == 264.0
            assert round(grupos_mapa["Deltoide anterior"]["volume"], 1) == 99.0
            assert round(grupos_mapa["Triceps cabeca longa"]["volume"], 1) == 79.2
            assert round(grupos_mapa["Serratil anterior"]["volume"], 1) == 33.0
            assert round(grupos_mapa["Dorsal superior"]["volume"], 1) == 180.0
            assert round(grupos_mapa["Dorsal medio"]["volume"], 1) == 240.0
            assert round(grupos_mapa["Dorsal inferior"]["volume"], 1) == 120.0
            assert round(grupos_mapa["Trapezio medio"]["volume"], 1) == 144.0
            assert round(grupos_mapa["Deltoide posterior"]["volume"], 1) == 180.0
            assert round(grupos_mapa["Eretores lombares"]["volume"], 1) == 96.0
            assert grupos_mapa["Peitoral inferior"]["intensidade"] == 1.0

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
            assert "Carga, RPE e 1RM" in html
            assert "Ultima vs anterior" in html
            assert "Recordes pessoais" in html
            assert "PRs expandidos" in html
            assert "Carga vs RPE" in html
            assert "Equilibrio muscular" in html
            assert "Calendario de carga" in html
            assert "Relatorio semanal" in html
            assert "Alertas" in html
            assert "Filtros rapidos" in html
            assert 'id="filtro-grupo"' in html
            assert "Maiores evolucoes" in html
            assert "Grupos musculares" in html
            assert "Volume semanal" in html
            assert "Mapa muscular da ultima sessao" in html
            assert "Mapa muscular anterior da ultima sessao" in html
            assert "Mapa muscular posterior da ultima sessao" in html
            assert "Dieta atual" in html
            assert "alimentos e metas diarias" in html
            assert 'class="grade-dieta grade-dieta-macros"' in html
            assert 'class="grade-dieta grade-dieta-micros"' in html
            assert html.count('class="dieta-indicador"') == 11
            assert "Leite semidesnatado" in html
            assert "Peito de frango" in html
            assert "46,0 g" in html
            assert "3 copos" in html
            assert "517 / 2.000 kcal" in html
            assert "Potassio" in html
            assert "Magnesio" in html
            assert "Zinco" in html
            assert "Vitamina D" in html
            assert "Vitamina B6" in html
            assert "V. D" in html
            assert "V. B6" in html
            assert "1637 mg" in html
            assert "133 mg" in html
            assert "5,0 mg" in html
            assert "300 UI" in html
            assert "1,5 mg" in html
            assert html.index("Filtros rapidos") < html.index("Dieta atual")
            assert "Peso corporal" in html
            assert "117,5 kg" in html
            assert "Cintura / altura" in html
            assert "IMC" in html
            assert "35,1" in html
            assert "1,83 m | 30 anos" in html
            assert "Meta de referencia: ate 83,4 kg" in html
            assert "Meta de referencia: abaixo de 91,5 cm" in html
            assert "Meta de referencia: 18,5 a 24,9" in html
            assert "Meta de referencia: abaixo de 0,50" in html
            assert html.count('role="progressbar"') == 4
            assert "71,0% de proximidade da meta" in html
            assert "82,8% de proximidade da meta" in html
            assert "chart.js@4.5.1/dist/chart.umd.min.js" in html
            assert html.count('class="minigrafico grafico-chartjs"') == 4
            assert 'id="grafico-volume-sessao"' in html
            assert 'id="grafico-carga-rpe"' in html
            assert "Evolucao historica do peso corporal" in html
            assert "Evolucao historica da cintura" in html
            assert "Evolucao historica do IMC" in html
            assert "Evolucao historica da relacao cintura por altura" in html
            assert "maxTicksLimit: 3" in html
            assert 'callback: (value) => formatoDecimal.format(value)' in html
            assert "grade-resumo-treino" in html
            assert "grade-resumo-corporal" in html
            assert ".valor,\n    .valor-menor" in html
            assert "font-size: var(--tipo-xl)" in html
            assert "@carbon/web-components" not in html
            assert "carbon/web-components/tag/v2/latest/tile.min.js" in html
            assert "carbon/web-components/tag/v2/latest/theme.min.js" in html
            assert "carbon/web-components/tag/v2/latest/select.min.js" in html
            assert "@carbon/styles@1.109.0/css/styles.css" in html
            assert 'class="cds--g100"' in html
            assert '<cds-theme theme="g100">' in html
            assert "<cds-tile class=\"indicador\">" in html
            assert "<cds-select id=\"filtro-periodo\"" in html
            assert "<cds-select-item value=\"todos\" text=\"Tudo\">" in html
            assert "cds--data-table cds--data-table--lg" in html
            assert "IBM Plex Sans" in html
            assert "grid-template-columns: repeat(6, minmax(0, 1fr))" in html
            assert "grid-template-columns: repeat(4, minmax(0, 1fr))" in html
            assert 'data-grupo="Dorsal superior"' in html
            assert "body-muscles" in html
            assert "mapa-anatomia-vetorial" in html
            assert "musculo com-volume" in html
            assert "data:image/" not in html
            assert "<image" not in html
            assert "Supino reto (barra)" in html
            assert "2.460 kg" in html

            conn = sqlite3.connect(test_db)
            try:
                assert conn.execute("SELECT COUNT(*) FROM training_sessions").fetchone()[0] == 2
            finally:
                conn.close()

            telegram_poller.handle_dashboard()
            assert bot_output.is_file()
            assert "Dashboard atualizado em" in sent_messages[-1]
            assert "Volume: <b>1.860 kg</b>" in sent_messages[-1]
            assert str(bot_output) not in sent_messages[-1]
            conn = sqlite3.connect(test_db)
            try:
                assert conn.execute(
                    "SELECT COUNT(*) FROM training_sessions"
                ).fetchone()[0] == 2
            finally:
                conn.close()

            print("Teste do dashboard passou.")
        finally:
            db_ops.DB_PATH = original_db_path
            db_ops.DATA_DIR = original_data_dir
            telegram_poller.DASHBOARD_OUTPUT = original_output
            telegram_poller.send = original_send
            gc.collect()


if __name__ == "__main__":
    main()
