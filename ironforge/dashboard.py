"""Dashboard local de volume de treino."""

from __future__ import annotations

import html
import json
import sqlite3
from collections import defaultdict
from datetime import date
from pathlib import Path

from ironforge import db_ops

ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT_DIR / "temp" / "dashboard-treino.html"

GRUPOS_MUSCULARES = {
    "Agachamento": "Pernas",
    "Zercher": "Pernas",
    "Terra Romeno": "Posterior",
    "Supino": "Peito",
    "Remada": "Costas",
    "Pullover": "Costas",
    "Desenvolvimento": "Ombros",
    "Remada alta": "Ombros",
    "Rosca": "Bracos",
    "Triceps": "Bracos",
    "Tríceps": "Bracos",
    "Encolhimento": "Trapézio",
}


def _connect():
    db_ops.init_db()
    conn = sqlite3.connect(db_ops.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def carregar_dados():
    """Retorna os dados consolidados para o dashboard."""
    conn = _connect()
    try:
        rows = conn.execute(
            """
            SELECT
                s.id AS session_id,
                s.date,
                s.training_type,
                l.exercise_name,
                l.sets,
                l.reps,
                l.weight,
                l.rpe,
                l.sort_order
            FROM training_sessions s
            JOIN training_logs l ON l.session_id = s.id
            WHERE l.weight IS NOT NULL AND l.weight > 0
            ORDER BY s.date ASC, s.id ASC, l.sort_order ASC, l.id ASC
            """
        ).fetchall()
    finally:
        conn.close()

    sessoes = {}
    exercicios = defaultdict(list)
    grupos = defaultdict(lambda: {"grupo": "", "volume": 0.0, "series": 0})

    for row in rows:
        volume = float(row["sets"]) * float(row["reps"]) * float(row["weight"])
        session_id = int(row["session_id"])
        sessao = sessoes.setdefault(
            session_id,
            {
                "session_id": session_id,
                "data": row["date"],
                "tipo": row["training_type"],
                "volume": 0.0,
                "series": 0,
                "repeticoes": 0,
                "exercicios": 0,
            },
        )
        sessao["volume"] += volume
        sessao["series"] += int(row["sets"])
        sessao["repeticoes"] += int(row["sets"]) * int(row["reps"])
        sessao["exercicios"] += 1
        sessao.setdefault("rpes", [])
        sessao.setdefault("logs", [])
        if row["rpe"] is not None:
            sessao["rpes"].append(float(row["rpe"]))

        log = {
            "nome": row["exercise_name"],
            "data": row["date"],
            "session_id": session_id,
            "volume": volume,
            "carga": float(row["weight"]),
            "series": int(row["sets"]),
            "reps": int(row["reps"]),
            "repeticoes": int(row["sets"]) * int(row["reps"]),
            "um_rm": _estimar_1rm(float(row["weight"]), int(row["reps"])),
            "rpe": float(row["rpe"]) if row["rpe"] is not None else None,
        }
        sessao["logs"].append(log)
        exercicios[row["exercise_name"]].append(
            {
                "data": row["date"],
                "session_id": session_id,
                "volume": volume,
                "carga": float(row["weight"]),
                "series": int(row["sets"]),
                "reps": int(row["reps"]),
                "repeticoes": int(row["sets"]) * int(row["reps"]),
                "um_rm": _estimar_1rm(float(row["weight"]), int(row["reps"])),
                "rpe": float(row["rpe"]) if row["rpe"] is not None else None,
            }
        )
        grupo = _grupo_muscular(row["exercise_name"])
        grupos[grupo]["grupo"] = grupo
        grupos[grupo]["volume"] += volume
        grupos[grupo]["series"] += int(row["sets"])

    volume_por_sessao = list(sessoes.values())
    for sessao in volume_por_sessao:
        rpes = sessao.get("rpes", [])
        sessao["rpe_medio"] = sum(rpes) / len(rpes) if rpes else None

    volume_por_exercicio = []
    for nome, pontos in exercicios.items():
        primeiro = pontos[0]["volume"]
        ultimo = pontos[-1]["volume"]
        cargas = [p["carga"] for p in pontos]
        rpes = [p["rpe"] for p in pontos if p["rpe"] is not None]
        melhores_1rm = max(pontos, key=lambda p: p["um_rm"])
        volume_por_exercicio.append(
            {
                "nome": nome,
                "pontos": pontos,
                "volume_total": sum(p["volume"] for p in pontos),
                "ultimo_volume": ultimo,
                "variacao": ultimo - primeiro if len(pontos) > 1 else 0.0,
                "primeira_carga": cargas[0],
                "ultima_carga": cargas[-1],
                "melhor_carga": max(cargas),
                "variacao_carga": cargas[-1] - cargas[0] if len(cargas) > 1 else 0.0,
                "rpe_medio": sum(rpes) / len(rpes) if rpes else None,
                "melhor_1rm": melhores_1rm["um_rm"],
                "data_melhor_1rm": melhores_1rm["data"],
            }
        )

    volume_por_exercicio.sort(key=lambda item: item["volume_total"], reverse=True)
    total = sum(s["volume"] for s in volume_por_sessao)
    ultima = volume_por_sessao[-1] if volume_por_sessao else None
    anterior = volume_por_sessao[-2] if len(volume_por_sessao) > 1 else None

    return {
        "resumo": {
            "sessoes": len(volume_por_sessao),
            "volume_total": total,
            "ultimo_volume": ultima["volume"] if ultima else 0.0,
            "variacao_ultima": (
                ultima["volume"] - anterior["volume"] if ultima and anterior else 0.0
            ),
            "ultima_data": ultima["data"] if ultima else "-",
            "series_total": sum(s["series"] for s in volume_por_sessao),
            "repeticoes_total": sum(s["repeticoes"] for s in volume_por_sessao),
            "exercicios_total": sum(s["exercicios"] for s in volume_por_sessao),
            "volume_medio_exercicio": (
                total / sum(s["exercicios"] for s in volume_por_sessao)
                if volume_por_sessao else 0.0
            ),
            "rpe_medio": _media(
                rpe for sessao in volume_por_sessao for rpe in sessao.get("rpes", [])
            ),
        },
        "volume_por_sessao": volume_por_sessao,
        "volume_por_exercicio": volume_por_exercicio,
        "comparacao_ultima": _comparar_ultimas_sessoes(volume_por_sessao),
        "volume_semanal": _agrupar_periodo(volume_por_sessao, "semana"),
        "volume_mensal": _agrupar_periodo(volume_por_sessao, "mes"),
        "grupos_musculares": sorted(
            grupos.values(), key=lambda item: item["volume"], reverse=True
        ),
        "prs": _calcular_prs(volume_por_exercicio),
        "alertas": _calcular_alertas(volume_por_sessao, volume_por_exercicio),
        "top_evolucoes": _calcular_top_evolucoes(volume_por_exercicio),
        "media_movel": _calcular_media_movel(volume_por_sessao),
        "consistencia": _calcular_consistencia(volume_por_sessao),
    }


def _estimar_1rm(carga, reps):
    return carga * (1 + reps / 30)


def _media(valores):
    lista = [v for v in valores if v is not None]
    return sum(lista) / len(lista) if lista else None


def _grupo_muscular(nome):
    for trecho, grupo in GRUPOS_MUSCULARES.items():
        if trecho.lower() in nome.lower():
            return grupo
    return "Outros"


def _parse_data(data_iso):
    return date.fromisoformat(data_iso)


def _agrupar_periodo(sessoes, periodo):
    agrupado = {}
    for sessao in sessoes:
        data_sessao = _parse_data(sessao["data"])
        if periodo == "semana":
            ano, semana, _ = data_sessao.isocalendar()
            chave = f"{ano}-S{semana:02d}"
        else:
            chave = data_sessao.strftime("%Y-%m")
        item = agrupado.setdefault(
            chave,
            {"periodo": chave, "volume": 0.0, "series": 0, "sessoes": 0},
        )
        item["volume"] += sessao["volume"]
        item["series"] += sessao["series"]
        item["sessoes"] += 1
    return list(agrupado.values())


def _calcular_media_movel(sessoes, janela=3):
    medias = []
    for idx, sessao in enumerate(sessoes):
        inicio = max(0, idx - janela + 1)
        trecho = sessoes[inicio : idx + 1]
        medias.append(
            {
                "data": sessao["data"],
                "volume": sessao["volume"],
                "media": sum(item["volume"] for item in trecho) / len(trecho),
                "janela": len(trecho),
            }
        )
    return medias


def _calcular_consistencia(sessoes):
    if not sessoes:
        return {
            "semanas_com_treino": 0,
            "melhor_sequencia": 0,
            "sequencia_atual": 0,
            "dias_desde_ultimo": None,
            "media_sessoes_semana": 0.0,
        }

    semanas = sorted({_parse_data(sessao["data"]).isocalendar()[:2] for sessao in sessoes})
    semanas_inicio = [date.fromisocalendar(ano, semana, 1) for ano, semana in semanas]
    melhor = 1
    atual = 1
    for anterior, corrente in zip(semanas_inicio, semanas_inicio[1:]):
        if (corrente - anterior).days == 7:
            atual += 1
        else:
            melhor = max(melhor, atual)
            atual = 1
    melhor = max(melhor, atual)

    sequencia_atual = 1
    for anterior, corrente in zip(reversed(semanas_inicio[:-1]), reversed(semanas_inicio[1:])):
        if (corrente - anterior).days == 7:
            sequencia_atual += 1
        else:
            break

    primeira = _parse_data(sessoes[0]["data"])
    ultima = _parse_data(sessoes[-1]["data"])
    semanas_intervalo = max(((ultima - primeira).days // 7) + 1, 1)
    return {
        "semanas_com_treino": len(semanas_inicio),
        "melhor_sequencia": melhor,
        "sequencia_atual": sequencia_atual,
        "dias_desde_ultimo": (date.today() - ultima).days,
        "media_sessoes_semana": len(sessoes) / semanas_intervalo,
    }


def _comparar_ultimas_sessoes(sessoes):
    if len(sessoes) < 2:
        return []
    anterior = {log["nome"]: log for log in sessoes[-2]["logs"]}
    atual = {log["nome"]: log for log in sessoes[-1]["logs"]}
    linhas = []
    for nome, log_atual in atual.items():
        log_anterior = anterior.get(nome)
        if not log_anterior:
            continue
        linhas.append(
            {
                "nome": nome,
                "carga_anterior": log_anterior["carga"],
                "carga_atual": log_atual["carga"],
                "delta_carga": log_atual["carga"] - log_anterior["carga"],
                "volume_anterior": log_anterior["volume"],
                "volume_atual": log_atual["volume"],
                "delta_volume": log_atual["volume"] - log_anterior["volume"],
                "rpe_anterior": log_anterior["rpe"],
                "rpe_atual": log_atual["rpe"],
            }
        )
    return linhas


def _calcular_prs(exercicios):
    prs = []
    for item in exercicios:
        melhor_carga = max(item["pontos"], key=lambda p: p["carga"])
        melhor_volume = max(item["pontos"], key=lambda p: p["volume"])
        prs.append(
            {
                "nome": item["nome"],
                "melhor_carga": melhor_carga["carga"],
                "data_carga": melhor_carga["data"],
                "melhor_volume": melhor_volume["volume"],
                "data_volume": melhor_volume["data"],
            }
        )
    return sorted(prs, key=lambda item: item["melhor_volume"], reverse=True)


def _calcular_top_evolucoes(exercicios):
    por_carga = sorted(exercicios, key=lambda item: item["variacao_carga"], reverse=True)
    por_volume = sorted(exercicios, key=lambda item: item["variacao"], reverse=True)
    quedas = sorted(exercicios, key=lambda item: item["variacao"])
    return {
        "carga": por_carga[:5],
        "volume": por_volume[:5],
        "quedas": [item for item in quedas if item["variacao"] < 0][:5],
    }


def _calcular_alertas(sessoes, exercicios):
    alertas = []
    if len(sessoes) >= 2:
        anterior = sessoes[-2]["volume"]
        atual = sessoes[-1]["volume"]
        if anterior and (atual - anterior) / anterior > 0.2:
            alertas.append("Volume da ultima sessao subiu mais de 20% vs. sessao anterior.")
    ultimos_rpes = [
        sessao["rpe_medio"] for sessao in sessoes[-3:] if sessao.get("rpe_medio") is not None
    ]
    if len(ultimos_rpes) >= 3 and all(rpe >= 9 for rpe in ultimos_rpes):
        alertas.append("RPE medio ficou alto nas ultimas 3 sessoes.")
    for item in exercicios:
        pontos = item["pontos"][-3:]
        if len(pontos) == 3 and pontos[-1]["carga"] <= pontos[0]["carga"]:
            alertas.append(f"{item['nome']} sem aumento de carga nas ultimas 3 entradas.")
            if len(alertas) >= 5:
                break
    return alertas


def _fmt_numero(valor):
    return f"{valor:,.0f}".replace(",", ".")


def _fmt_delta(valor):
    sinal = "+" if valor > 0 else ""
    return f"{sinal}{_fmt_numero(valor)} kg"


def _fmt_decimal(valor, casas=1):
    if valor is None:
        return "-"
    return f"{valor:.{casas}f}".replace(".", ",")


def _json(data):
    return html.escape(json.dumps(data, ensure_ascii=False), quote=False)


def _line_points(points, width=760, height=300, padding=28):
    if not points:
        return []
    if len(points) == 1:
        x_values = [width / 2]
    else:
        step = (width - padding * 2) / (len(points) - 1)
        x_values = [padding + idx * step for idx in range(len(points))]

    min_y = min(points)
    max_y = max(points)
    span = max(max_y - min_y, 1)
    coords = []
    for x, value in zip(x_values, points):
        chart_bottom = height - 68
        y = chart_bottom - ((value - min_y) / span) * (chart_bottom - padding)
        coords.append({"x": x, "y": y, "valor": value})
    return coords


def _polyline(points):
    return " ".join(f"{p['x']:.1f},{p['y']:.1f}" for p in points)


def _rotulos_linha(points, sessoes):
    rotulos = []
    for idx, point in enumerate(points):
        label = _fmt_numero(point["valor"])
        x = point["x"]
        if idx == 0:
            x = max(point["x"], 36)
        elif idx == len(points) - 1:
            x = min(point["x"], 724)
        anchor = "middle"
        data = sessoes[idx]["data"][5:] if idx < len(sessoes) else ""
        rotulos.append(
            f"""
            <circle class="ponto-volume" cx="{point['x']:.1f}" cy="{point['y']:.1f}" r="4"></circle>
            <text class="rotulo-volume" x="{x:.1f}" y="264" text-anchor="{anchor}">{label}</text>
            <text class="rotulo-data" x="{x:.1f}" y="284" text-anchor="{anchor}">{html.escape(data)}</text>
            """
        )
    return "\n".join(rotulos)


def _barras_sessoes(sessoes):
    if not sessoes:
        return "<p class=\"vazio\">Ainda nao ha cargas registradas.</p>"

    max_volume = max(sessao["volume"] for sessao in sessoes) or 1
    itens = []
    for sessao in sessoes[-12:]:
        altura = max((sessao["volume"] / max_volume) * 100, 3)
        titulo = (
            f"{sessao['data']} - volume "
            f"{_fmt_numero(sessao['volume'])} kg"
        )
        itens.append(
            f"""
            <div class="barra-item" title="{html.escape(titulo)}">
              <strong>{_fmt_numero(sessao['volume'])}</strong>
              <div class="barra" style="height: {altura:.1f}%"></div>
              <span>{html.escape(sessao['data'][5:])}</span>
            </div>
            """
        )
    return "\n".join(itens)


def _classe_delta(valor):
    return "positivo" if valor >= 0 else "negativo"


def _linhas_tabela(linhas, colunas, vazio="Sem dados suficientes."):
    if not linhas:
        return f"<tr><td colspan=\"{len(colunas)}\">{vazio}</td></tr>"
    html_linhas = []
    for linha in linhas:
        celulas = []
        for coluna in colunas:
            valor = coluna["valor"](linha)
            classe = coluna.get("classe", lambda _linha: "")(linha)
            class_attr = f" class=\"{classe}\"" if classe else ""
            celulas.append(f"<td{class_attr}>{valor}</td>")
        html_linhas.append(f"<tr>{''.join(celulas)}</tr>")
    return "\n".join(html_linhas)


def _render_periodos(periodos):
    return _linhas_tabela(
        periodos[-8:],
        [
            {"valor": lambda item: html.escape(item["periodo"])},
            {"valor": lambda item: f"{_fmt_numero(item['volume'])} kg"},
            {"valor": lambda item: str(item["sessoes"])},
            {"valor": lambda item: str(item["series"])},
        ],
    )


def _render_lista_simples(itens):
    if not itens:
        return "<p class=\"vazio\">Sem alertas relevantes agora.</p>"
    return "<ul class=\"lista\">" + "".join(
        f"<li>{html.escape(item)}</li>" for item in itens
    ) + "</ul>"


def _opcoes_exercicios(exercicios):
    opcoes = ['<option value="">Todos</option>']
    for item in sorted(exercicios, key=lambda ex: ex["nome"]):
        nome = html.escape(item["nome"])
        valor = html.escape(item["nome"], quote=True)
        opcoes.append(f'<option value="{valor}">{nome}</option>')
    return "\n".join(opcoes)


def gerar_html(dados):
    resumo = dados["resumo"]
    sessoes = dados["volume_por_sessao"]
    exercicios = dados["volume_por_exercicio"]
    pontos_linha = _line_points([s["volume"] for s in sessoes])
    linha = _polyline(pontos_linha)
    rotulos_linha = _rotulos_linha(pontos_linha, sessoes)
    barras = _barras_sessoes(sessoes)

    linhas_exercicios = []
    for item in exercicios[:12]:
        classe = "positivo" if item["variacao"] >= 0 else "negativo"
        linhas_exercicios.append(
            f"""
            <tr>
              <td>{html.escape(item["nome"])}</td>
              <td>{_fmt_numero(item["volume_total"])} kg</td>
              <td>{_fmt_numero(item["ultimo_volume"])} kg</td>
              <td class="{classe}">{_fmt_delta(item["variacao"])}</td>
            </tr>
            """
        )

    tabela = "\n".join(linhas_exercicios) or (
        "<tr><td colspan=\"4\">Ainda nao ha dados de treino registrados.</td></tr>"
    )
    tabela_cargas = _linhas_tabela(
        exercicios[:12],
        [
            {"valor": lambda item: html.escape(item["nome"])},
            {"valor": lambda item: f"{_fmt_decimal(item['ultima_carga'])} kg"},
            {"valor": lambda item: f"{_fmt_decimal(item['melhor_carga'])} kg"},
            {
                "valor": lambda item: _fmt_delta(item["variacao_carga"]),
                "classe": lambda item: _classe_delta(item["variacao_carga"]),
            },
            {"valor": lambda item: _fmt_decimal(item["rpe_medio"])},
        ],
    )
    tabela_comparacao = _linhas_tabela(
        dados["comparacao_ultima"],
        [
            {"valor": lambda item: html.escape(item["nome"])},
            {
                "valor": lambda item: (
                    f"{_fmt_decimal(item['carga_anterior'])} -> "
                    f"{_fmt_decimal(item['carga_atual'])} kg"
                )
            },
            {
                "valor": lambda item: _fmt_delta(item["delta_carga"]),
                "classe": lambda item: _classe_delta(item["delta_carga"]),
            },
            {
                "valor": lambda item: _fmt_delta(item["delta_volume"]),
                "classe": lambda item: _classe_delta(item["delta_volume"]),
            },
            {
                "valor": lambda item: (
                    f"{_fmt_decimal(item['rpe_anterior'])} -> "
                    f"{_fmt_decimal(item['rpe_atual'])}"
                )
            },
        ],
    )
    tabela_grupos = _linhas_tabela(
        dados["grupos_musculares"],
        [
            {"valor": lambda item: html.escape(item["grupo"])},
            {"valor": lambda item: f"{_fmt_numero(item['volume'])} kg"},
            {"valor": lambda item: str(item["series"])},
        ],
    )
    tabela_prs = _linhas_tabela(
        dados["prs"][:10],
        [
            {"valor": lambda item: html.escape(item["nome"])},
            {
                "valor": lambda item: (
                    f"{_fmt_decimal(item['melhor_carga'])} kg em "
                    f"{html.escape(item['data_carga'])}"
                )
            },
            {
                "valor": lambda item: (
                    f"{_fmt_numero(item['melhor_volume'])} kg em "
                    f"{html.escape(item['data_volume'])}"
                )
            },
        ],
    )
    top_carga = _linhas_tabela(
        dados["top_evolucoes"]["carga"],
        [
            {"valor": lambda item: html.escape(item["nome"])},
            {
                "valor": lambda item: _fmt_delta(item["variacao_carga"]),
                "classe": lambda item: _classe_delta(item["variacao_carga"]),
            },
        ],
    )
    top_volume = _linhas_tabela(
        dados["top_evolucoes"]["volume"],
        [
            {"valor": lambda item: html.escape(item["nome"])},
            {
                "valor": lambda item: _fmt_delta(item["variacao"]),
                "classe": lambda item: _classe_delta(item["variacao"]),
            },
        ],
    )
    quedas = _linhas_tabela(
        dados["top_evolucoes"]["quedas"],
        [
            {"valor": lambda item: html.escape(item["nome"])},
            {
                "valor": lambda item: _fmt_delta(item["variacao"]),
                "classe": lambda item: _classe_delta(item["variacao"]),
            },
        ],
    )
    evolucao_exercicios = _linhas_tabela(
        exercicios[:8],
        [
            {"valor": lambda item: html.escape(item["nome"])},
            {
                "valor": lambda item: " -> ".join(
                    _fmt_numero(ponto["volume"]) for ponto in item["pontos"][-4:]
                )
            },
            {"valor": lambda item: _fmt_delta(item["variacao"])},
        ],
    )
    tabela_1rm = _linhas_tabela(
        sorted(exercicios, key=lambda item: item["melhor_1rm"], reverse=True)[:12],
        [
            {"valor": lambda item: html.escape(item["nome"])},
            {"valor": lambda item: f"{_fmt_decimal(item['melhor_1rm'])} kg"},
            {"valor": lambda item: f"{_fmt_decimal(item['melhor_carga'])} kg"},
            {"valor": lambda item: html.escape(item["data_melhor_1rm"])},
        ],
    )
    tabela_media_movel = _linhas_tabela(
        dados["media_movel"][-10:],
        [
            {"valor": lambda item: html.escape(item["data"])},
            {"valor": lambda item: f"{_fmt_numero(item['volume'])} kg"},
            {"valor": lambda item: f"{_fmt_numero(item['media'])} kg"},
            {"valor": lambda item: f"{item['janela']} sessoes"},
        ],
    )
    consistencia = dados["consistencia"]
    opcoes_exercicios = _opcoes_exercicios(exercicios)

    return f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Dashboard de treino - IronForge</title>
  <style>
    :root {{
      color-scheme: light;
      --fundo: #f6f5f2;
      --texto: #1e2528;
      --muted: #697579;
      --linha: #d9dedb;
      --painel: #ffffff;
      --verde: #2f8f72;
      --azul: #3269a8;
      --vermelho: #a84c4c;
      --sombra: 0 14px 36px rgba(31, 42, 46, 0.10);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Arial, Helvetica, sans-serif;
      background: var(--fundo);
      color: var(--texto);
    }}
    main {{
      width: min(1180px, calc(100% - 32px));
      margin: 0 auto;
      padding: 32px 0 48px;
    }}
    header {{
      display: flex;
      align-items: end;
      justify-content: space-between;
      gap: 24px;
      margin-bottom: 24px;
    }}
    h1, h2 {{ margin: 0; letter-spacing: 0; }}
    h1 {{ font-size: 34px; line-height: 1.08; }}
    h2 {{ font-size: 18px; }}
    .subtitulo {{ color: var(--muted); margin: 8px 0 0; }}
    .grade-resumo {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 12px;
      margin-bottom: 18px;
    }}
    .indicador, .painel {{
      background: var(--painel);
      border: 1px solid var(--linha);
      border-radius: 8px;
      box-shadow: var(--sombra);
    }}
    .indicador {{ padding: 16px; min-height: 102px; }}
    .rotulo {{
      display: block;
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      margin-bottom: 10px;
    }}
    .valor {{ font-size: 27px; font-weight: 700; }}
    .valor-menor {{ font-size: 20px; }}
    .positivo {{ color: var(--verde); }}
    .negativo {{ color: var(--vermelho); }}
    .layout {{
      display: grid;
      grid-template-columns: minmax(0, 1.45fr) minmax(320px, 0.85fr);
      gap: 16px;
    }}
    .duas-colunas {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 16px;
      margin-top: 16px;
    }}
    .painel {{ padding: 18px; }}
    .filtros {{
      display: grid;
      grid-template-columns: repeat(3, minmax(150px, 1fr));
      gap: 12px;
      margin-bottom: 16px;
    }}
    label {{
      display: grid;
      gap: 6px;
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
    }}
    select {{
      width: 100%;
      border: 1px solid var(--linha);
      border-radius: 6px;
      background: #fff;
      color: var(--texto);
      font: inherit;
      padding: 9px 10px;
      text-transform: none;
    }}
    .linha-topo {{
      display: flex;
      align-items: baseline;
      justify-content: space-between;
      gap: 16px;
      margin-bottom: 14px;
    }}
    .linha-topo span {{ color: var(--muted); font-size: 13px; }}
    svg {{ width: 100%; height: auto; display: block; }}
    .eixo {{ stroke: var(--linha); stroke-width: 1; }}
    .linha-volume {{ fill: none; stroke: var(--azul); stroke-width: 4; }}
    .ponto-volume {{ fill: var(--painel); stroke: var(--azul); stroke-width: 3; }}
    .rotulo-volume {{
      fill: var(--azul);
      font-size: 14px;
      font-weight: 700;
    }}
    .rotulo-data {{
      fill: var(--muted);
      font-size: 11px;
    }}
    .barras {{
      height: 238px;
      display: grid;
      grid-template-columns: repeat(12, minmax(18px, 1fr));
      gap: 8px;
      align-items: end;
      padding-top: 12px;
    }}
    .barra-item {{
      height: 100%;
      min-width: 0;
      display: flex;
      flex-direction: column;
      justify-content: end;
      gap: 8px;
      text-align: center;
      color: var(--muted);
      font-size: 11px;
    }}
    .barra-item span {{
      display: block;
      white-space: nowrap;
      font-size: 10px;
      line-height: 1;
    }}
    .barra-item strong {{
      color: var(--texto);
      display: block;
      font-size: 12px;
      line-height: 1.1;
      writing-mode: vertical-rl;
      transform: rotate(180deg);
      align-self: center;
      max-height: 72px;
    }}
    .barra {{
      min-height: 8px;
      border-radius: 5px 5px 2px 2px;
      background: var(--verde);
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 14px;
    }}
    th, td {{
      padding: 12px 8px;
      border-bottom: 1px solid var(--linha);
      text-align: right;
      white-space: nowrap;
    }}
    th:first-child, td:first-child {{
      text-align: left;
      white-space: normal;
    }}
    th {{ color: var(--muted); font-weight: 600; }}
    .vazio {{ color: var(--muted); }}
    .lista {{ margin: 0; padding-left: 18px; color: var(--texto); }}
    .lista li {{ margin: 8px 0; }}
    .mini-grade {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
    }}
    @media (max-width: 860px) {{
      header, .layout, .duas-colunas {{ display: block; }}
      header > div:last-child {{ margin-top: 12px; }}
      .grade-resumo {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      .painel {{ margin-bottom: 16px; }}
      h1 {{ font-size: 28px; }}
    }}
    @media (max-width: 560px) {{
      main {{ width: min(100% - 20px, 1180px); padding-top: 20px; }}
      .grade-resumo {{ grid-template-columns: 1fr; }}
      .valor {{ font-size: 24px; }}
      th, td {{ font-size: 13px; padding: 10px 4px; }}
      .filtros, .mini-grade {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <main>
    <header>
      <div>
        <h1>Dashboard de treino</h1>
        <p class="subtitulo">Evolucao do volume calculada por series x repeticoes x carga.</p>
      </div>
      <div class="subtitulo">Ultima sessao: {html.escape(str(resumo["ultima_data"]))}</div>
    </header>

    <section class="grade-resumo" aria-label="Resumo">
      <div class="indicador">
        <span class="rotulo">Sessoes</span>
        <span class="valor">{resumo["sessoes"]}</span>
      </div>
      <div class="indicador">
        <span class="rotulo">Volume total</span>
        <span class="valor">{_fmt_numero(resumo["volume_total"])} kg</span>
      </div>
      <div class="indicador">
        <span class="rotulo">Ultima sessao</span>
        <span class="valor">{_fmt_numero(resumo["ultimo_volume"])} kg</span>
      </div>
      <div class="indicador">
        <span class="rotulo">Variacao recente</span>
        <span class="valor valor-menor {'positivo' if resumo["variacao_ultima"] >= 0 else 'negativo'}">{_fmt_delta(resumo["variacao_ultima"])}</span>
      </div>
      <div class="indicador">
        <span class="rotulo">Series totais</span>
        <span class="valor">{resumo["series_total"]}</span>
      </div>
      <div class="indicador">
        <span class="rotulo">Repeticoes totais</span>
        <span class="valor">{resumo["repeticoes_total"]}</span>
      </div>
      <div class="indicador">
        <span class="rotulo">Media por exercicio</span>
        <span class="valor valor-menor">{_fmt_numero(resumo["volume_medio_exercicio"])} kg</span>
      </div>
      <div class="indicador">
        <span class="rotulo">RPE medio</span>
        <span class="valor">{_fmt_decimal(resumo["rpe_medio"])}</span>
      </div>
    </section>

    <section class="layout">
      <article class="painel">
        <div class="linha-topo">
          <h2>Volume por sessao</h2>
          <span>{len(sessoes)} sessoes registradas</span>
        </div>
        <svg viewBox="0 0 760 300" role="img" aria-label="Linha de evolucao do volume por sessao">
          <line class="eixo" x1="28" y1="232" x2="732" y2="232"></line>
          <line class="eixo" x1="28" y1="28" x2="28" y2="232"></line>
          <polyline class="linha-volume" points="{linha}"></polyline>
          {rotulos_linha}
        </svg>
      </article>

      <article class="painel">
        <div class="linha-topo">
          <h2>Ultimas sessoes</h2>
          <span>ate 12 treinos</span>
        </div>
        <div class="barras">{barras}</div>
      </article>
    </section>

    <section class="painel" style="margin-top: 16px;">
      <div class="linha-topo">
        <h2>Exercicios por volume acumulado</h2>
        <span>top 12</span>
      </div>
      <table>
        <thead>
          <tr>
            <th>Exercicio</th>
            <th>Total</th>
            <th>Ultimo</th>
            <th>Variacao</th>
          </tr>
        </thead>
        <tbody>
          {tabela}
        </tbody>
      </table>
    </section>

    <section class="duas-colunas">
      <article class="painel">
        <div class="linha-topo">
          <h2>Carga e RPE por exercicio</h2>
          <span>top 12</span>
        </div>
        <table>
          <thead><tr><th>Exercicio</th><th>Ultima</th><th>Melhor</th><th>Variacao</th><th>RPE</th></tr></thead>
          <tbody>{tabela_cargas}</tbody>
        </table>
      </article>
      <article class="painel">
        <div class="linha-topo">
          <h2>Ultima vs anterior</h2>
          <span>mesmos exercicios</span>
        </div>
        <table>
          <thead><tr><th>Exercicio</th><th>Carga</th><th>Delta carga</th><th>Delta volume</th><th>RPE</th></tr></thead>
          <tbody>{tabela_comparacao}</tbody>
        </table>
      </article>
    </section>

    <section class="duas-colunas">
      <article class="painel">
        <div class="linha-topo">
          <h2>1RM estimado</h2>
          <span>formula de Epley</span>
        </div>
        <table>
          <thead><tr><th>Exercicio</th><th>1RM est.</th><th>Melhor carga</th><th>Data</th></tr></thead>
          <tbody>{tabela_1rm}</tbody>
        </table>
      </article>
      <article class="painel">
        <div class="linha-topo">
          <h2>Media movel de volume</h2>
          <span>janela de 3 sessoes</span>
        </div>
        <table>
          <thead><tr><th>Data</th><th>Volume</th><th>Media</th><th>Janela</th></tr></thead>
          <tbody>{tabela_media_movel}</tbody>
        </table>
      </article>
    </section>

    <section class="duas-colunas">
      <article class="painel">
        <div class="linha-topo">
          <h2>Consistencia</h2>
          <span>semanas com treino</span>
        </div>
        <div class="mini-grade">
          <div class="indicador"><span class="rotulo">Semanas ativas</span><span class="valor">{consistencia["semanas_com_treino"]}</span></div>
          <div class="indicador"><span class="rotulo">Melhor sequencia</span><span class="valor">{consistencia["melhor_sequencia"]}</span></div>
          <div class="indicador"><span class="rotulo">Sequencia atual</span><span class="valor">{consistencia["sequencia_atual"]}</span></div>
          <div class="indicador"><span class="rotulo">Dias desde ultimo</span><span class="valor">{consistencia["dias_desde_ultimo"] if consistencia["dias_desde_ultimo"] is not None else "-"}</span></div>
        </div>
      </article>
      <article class="painel">
        <div class="linha-topo">
          <h2>Filtros rapidos</h2>
          <span>periodo e exercicio</span>
        </div>
        <div class="filtros">
          <label>Periodo
            <select id="filtro-periodo">
              <option value="todos">Tudo</option>
              <option value="7">7 dias</option>
              <option value="30">30 dias</option>
              <option value="90">90 dias</option>
            </select>
          </label>
          <label>Exercicio
            <select id="filtro-exercicio">
              {opcoes_exercicios}
            </select>
          </label>
          <label>Ordenar
            <select id="filtro-ordem">
              <option value="data">Data</option>
              <option value="volume">Volume</option>
              <option value="carga">Carga</option>
            </select>
          </label>
        </div>
        <table>
          <thead><tr><th>Data</th><th>Exercicio</th><th>Carga</th><th>Volume</th><th>1RM</th><th>RPE</th></tr></thead>
          <tbody id="tabela-filtrada"></tbody>
        </table>
      </article>
    </section>

    <section class="duas-colunas">
      <article class="painel">
        <div class="linha-topo">
          <h2>Evolucao por exercicio</h2>
          <span>ultimos 4 volumes</span>
        </div>
        <table>
          <thead><tr><th>Exercicio</th><th>Sequencia</th><th>Variacao</th></tr></thead>
          <tbody>{evolucao_exercicios}</tbody>
        </table>
      </article>
      <article class="painel">
        <div class="linha-topo">
          <h2>Grupos musculares</h2>
          <span>volume e series</span>
        </div>
        <table>
          <thead><tr><th>Grupo</th><th>Volume</th><th>Series</th></tr></thead>
          <tbody>{tabela_grupos}</tbody>
        </table>
      </article>
    </section>

    <section class="duas-colunas">
      <article class="painel">
        <div class="linha-topo">
          <h2>Volume semanal</h2>
          <span>ultimas 8 semanas</span>
        </div>
        <table>
          <thead><tr><th>Periodo</th><th>Volume</th><th>Sessoes</th><th>Series</th></tr></thead>
          <tbody>{_render_periodos(dados["volume_semanal"])}</tbody>
        </table>
      </article>
      <article class="painel">
        <div class="linha-topo">
          <h2>Volume mensal</h2>
          <span>ultimos 8 meses</span>
        </div>
        <table>
          <thead><tr><th>Periodo</th><th>Volume</th><th>Sessoes</th><th>Series</th></tr></thead>
          <tbody>{_render_periodos(dados["volume_mensal"])}</tbody>
        </table>
      </article>
    </section>

    <section class="duas-colunas">
      <article class="painel">
        <div class="linha-topo">
          <h2>Maiores evolucoes</h2>
          <span>carga e volume</span>
        </div>
        <h3>Carga</h3>
        <table><tbody>{top_carga}</tbody></table>
        <h3>Volume</h3>
        <table><tbody>{top_volume}</tbody></table>
        <h3>Quedas</h3>
        <table><tbody>{quedas}</tbody></table>
      </article>
      <article class="painel">
        <div class="linha-topo">
          <h2>Recordes pessoais</h2>
          <span>carga e volume</span>
        </div>
        <table>
          <thead><tr><th>Exercicio</th><th>Maior carga</th><th>Maior volume</th></tr></thead>
          <tbody>{tabela_prs}</tbody>
        </table>
      </article>
    </section>

    <section class="painel" style="margin-top: 16px;">
      <div class="linha-topo">
        <h2>Alertas</h2>
        <span>regras simples</span>
      </div>
      {_render_lista_simples(dados["alertas"])}
    </section>
  </main>
  <script type="application/json" id="dados-dashboard">{_json(dados)}</script>
  <script>
    const dados = JSON.parse(document.getElementById("dados-dashboard").textContent);
    const linhas = dados.volume_por_sessao.flatMap((sessao) =>
      sessao.logs.map((log) => ({{ ...log, data: sessao.data }}))
    );
    const fmtInteiro = (valor) => Math.round(valor).toLocaleString("pt-BR");
    const fmtDecimal = (valor) => valor == null ? "-" : Number(valor).toLocaleString("pt-BR", {{ maximumFractionDigits: 1 }});
    const filtroPeriodo = document.getElementById("filtro-periodo");
    const filtroExercicio = document.getElementById("filtro-exercicio");
    const filtroOrdem = document.getElementById("filtro-ordem");
    const tabelaFiltrada = document.getElementById("tabela-filtrada");

    function renderFiltrada() {{
      const dias = filtroPeriodo.value;
      const exercicio = filtroExercicio.value;
      const ordem = filtroOrdem.value;
      const datas = linhas.map((linha) => new Date(linha.data + "T00:00:00"));
      const dataMax = datas.length ? new Date(Math.max(...datas)) : null;
      let filtradas = linhas.filter((linha) => {{
        const noPeriodo = dias === "todos" || !dataMax ||
          ((dataMax - new Date(linha.data + "T00:00:00")) / 86400000) <= Number(dias);
        const noExercicio = !exercicio || linha.nome === exercicio;
        return noPeriodo && noExercicio;
      }});
      filtradas.sort((a, b) => {{
        if (ordem === "volume") return b.volume - a.volume;
        if (ordem === "carga") return b.carga - a.carga;
        return a.data.localeCompare(b.data);
      }});
      tabelaFiltrada.innerHTML = filtradas.slice(-40).map((linha) => `
        <tr>
          <td>${{linha.data}}</td>
          <td>${{linha.nome}}</td>
          <td>${{fmtDecimal(linha.carga)}} kg</td>
          <td>${{fmtInteiro(linha.volume)}} kg</td>
          <td>${{fmtDecimal(linha.um_rm)}} kg</td>
          <td>${{fmtDecimal(linha.rpe)}}</td>
        </tr>
      `).join("") || "<tr><td colspan=\\"6\\">Sem registros nesse filtro.</td></tr>";
    }}
    [filtroPeriodo, filtroExercicio, filtroOrdem].forEach((controle) =>
      controle.addEventListener("change", renderFiltrada)
    );
    renderFiltrada();
  </script>
</body>
</html>
"""


def salvar_dashboard(output_path=DEFAULT_OUTPUT):
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    dados = carregar_dados()
    output.write_text(gerar_html(dados), encoding="utf-8")
    return output
