"""Dashboard local de volume de treino."""

from __future__ import annotations

import html
import json
import sqlite3
from collections import defaultdict
from datetime import date
from pathlib import Path

from forja_de_ferro import db_ops

ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT_DIR / "temp" / "dashboard-treino.html"
MUSCLE_MAP_ASSET = (
    ROOT_DIR / "forja_de_ferro" / "assets" / "mapa_muscular_body_muscles.json"
)

MUSCLE_IDS_BY_GROUP = {
    "Peitoral": (
        "chest-upper-left",
        "chest-upper-right",
        "chest-lower-left",
        "chest-lower-right",
    ),
    "Deltoide anterior": ("shoulder-front-left", "shoulder-front-right"),
    "Deltoide lateral": ("shoulder-side-left", "shoulder-side-right"),
    "Deltoide posterior": ("deltoid-rear-left", "deltoid-rear-right"),
    "Biceps": ("biceps-left", "biceps-right"),
    "Triceps": (
        "triceps-long-left",
        "triceps-lateral-left",
        "triceps-long-right",
        "triceps-lateral-right",
    ),
    "Antebraco": (
        "forearm-left",
        "forearm-right",
        "forearm-flexors-left",
        "forearm-extensors-left",
        "forearm-flexors-right",
        "forearm-extensors-right",
    ),
    "Core": (
        "abs-upper-left",
        "abs-upper-right",
        "abs-lower-left",
        "abs-lower-right",
        "obliques-left",
        "obliques-right",
    ),
    "Quadriceps": ("quads-left", "quads-right"),
    "Gluteos": (
        "gluteus-medius-left",
        "gluteus-maximus-left",
        "gluteus-medius-right",
        "gluteus-maximus-right",
    ),
    "Posteriores": (
        "hamstrings-medial-left",
        "hamstrings-lateral-left",
        "hamstrings-medial-right",
        "hamstrings-lateral-right",
    ),
    "Dorsais": (
        "lats-upper-left",
        "lats-mid-left",
        "lats-lower-left",
        "lats-upper-right",
        "lats-mid-right",
        "lats-lower-right",
    ),
    "Trapezio": (
        "traps-upper-left",
        "traps-mid-left",
        "traps-lower-left",
        "traps-upper-right",
        "traps-mid-right",
        "traps-lower-right",
    ),
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
    muscle_groups = db_ops.list_muscle_groups()

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
        exercise_groups = muscle_groups.get(row["exercise_name"], [])
        group_names = [item["muscle_group"] for item in exercise_groups] or ["Outros"]
        for grupo in group_names:
            grupos[grupo]["grupo"] = grupo
            grupos[grupo]["volume"] += volume
            grupos[grupo]["series"] += int(row["sets"])

    volume_por_sessao = list(sessoes.values())
    for sessao in volume_por_sessao:
        rpes = sessao.get("rpes", [])
        sessao["rpe_medio"] = sum(rpes) / len(rpes) if rpes else None
    mapa_ultima_sessao = _calcular_mapa_muscular(
        volume_por_sessao[-1] if volume_por_sessao else None,
        muscle_groups,
    )

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
        "mapa_ultima_sessao": mapa_ultima_sessao,
        "prs": _calcular_prs(volume_por_exercicio),
        "alertas": _calcular_alertas(volume_por_sessao, volume_por_exercicio),
        "top_evolucoes": _calcular_top_evolucoes(volume_por_exercicio),
        "media_movel": _calcular_media_movel(volume_por_sessao),
        "consistencia": _calcular_consistencia(volume_por_sessao),
        "analises": _calcular_analises(volume_por_sessao, volume_por_exercicio),
    }


def _estimar_1rm(carga, reps):
    return carga * (1 + reps / 30)


def _media(valores):
    lista = [v for v in valores if v is not None]
    return sum(lista) / len(lista) if lista else None


def _calcular_mapa_muscular(sessao, muscle_groups):
    if not sessao:
        return {"data": None, "volume_maximo": 0.0, "grupos": []}

    volumes = defaultdict(float)
    for log in sessao["logs"]:
        grupos = muscle_groups.get(log["nome"], [])
        for grupo in grupos:
            volumes[grupo["muscle_group"]] += log["volume"]

    volume_maximo = max(volumes.values(), default=0.0)
    return {
        "data": sessao["data"],
        "volume_maximo": volume_maximo,
        "grupos": [
            {
                "grupo": grupo,
                "volume": volume,
                "intensidade": volume / volume_maximo if volume_maximo else 0.0,
            }
            for grupo, volume in sorted(
                volumes.items(), key=lambda item: item[1], reverse=True
            )
        ],
    }


def _grupo_muscular(nome):
    groups = db_ops.get_muscle_groups(nome)
    return groups[0]["muscle_group"] if groups else "Outros"


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
    if len(ultimos_rpes) >= 3 and all(rpe >= 10 for rpe in ultimos_rpes):
        alertas.append("RPE medio chegou a 10 nas ultimas 3 sessoes; acompanhe a recuperacao.")
    for item in exercicios:
        pontos = item["pontos"][-3:]
        if len(pontos) < 2:
            continue

        anterior, atual = pontos[-2:]
        if (
            atual["carga"] == anterior["carga"]
            and anterior["rpe"] is not None
            and atual["rpe"] is not None
            and anterior["rpe"] >= 9
            and atual["rpe"] <= 8
        ):
            alertas.append(
                f"{item['nome']} consolidou {atual['carga']:g} kg: "
                f"RPE {anterior['rpe']:g} -> {atual['rpe']:g}."
            )
        elif (
            atual["carga"] < anterior["carga"]
            and anterior["rpe"] is not None
            and anterior["rpe"] >= 10
        ):
            alertas.append(
                f"{item['nome']} teve reducao de carga apos RPE "
                f"{anterior['rpe']:g}, conforme a regra de progressao."
            )
        elif (
            len(pontos) == 3
            and all(ponto["rpe"] is not None and ponto["rpe"] >= 10 for ponto in pontos)
        ):
            alertas.append(
                f"{item['nome']} ficou em RPE 10 nas ultimas 3 entradas; "
                "acompanhe tecnica e recuperacao."
            )

        if len(alertas) >= 5:
            break
    return alertas


def _calcular_analises(sessoes, exercicios):
    rpe_distribuicao = defaultdict(int)
    volume_grupo_semana = defaultdict(lambda: {"periodo": "", "grupo": "", "volume": 0.0})
    carga_rpe = []

    muscle_groups = db_ops.list_muscle_groups()
    for sessao in sessoes:
        data_sessao = _parse_data(sessao["data"])
        ano, semana, _ = data_sessao.isocalendar()
        periodo = f"{ano}-S{semana:02d}"
        for log in sessao["logs"]:
            if log["rpe"] is not None:
                rpe_distribuicao[str(int(round(log["rpe"])))] += 1
            groups = muscle_groups.get(log["nome"], [])
            group_names = [item["muscle_group"] for item in groups] or ["Outros"]
            for grupo in group_names:
                chave = (periodo, grupo)
                volume_grupo_semana[chave]["periodo"] = periodo
                volume_grupo_semana[chave]["grupo"] = grupo
                volume_grupo_semana[chave]["volume"] += log["volume"]

    for item in exercicios:
        ultimo = item["pontos"][-1]
        carga_rpe.append(
            {
                "nome": item["nome"],
                "carga": ultimo["carga"],
                "rpe": ultimo["rpe"],
                "volume": ultimo["volume"],
                "um_rm": ultimo["um_rm"],
            }
        )

    comparacao_media3 = []
    if sessoes:
        ultima = sessoes[-1]
        historico = sessoes[-4:-1]
        medias = defaultdict(list)
        for sessao in historico:
            for log in sessao["logs"]:
                medias[log["nome"]].append(log)
        for log in ultima["logs"]:
            anteriores = medias.get(log["nome"], [])
            if not anteriores:
                continue
            media_volume = sum(item["volume"] for item in anteriores) / len(anteriores)
            media_carga = sum(item["carga"] for item in anteriores) / len(anteriores)
            comparacao_media3.append(
                {
                    "nome": log["nome"],
                    "volume_atual": log["volume"],
                    "media_volume": media_volume,
                    "delta_volume": log["volume"] - media_volume,
                    "carga_atual": log["carga"],
                    "media_carga": media_carga,
                    "delta_carga": log["carga"] - media_carga,
                    "rpe": log["rpe"],
                }
            )

    return {
        "volume_rpe_sessao": [
            {
                "data": sessao["data"],
                "volume": sessao["volume"],
                "rpe_medio": sessao["rpe_medio"],
            }
            for sessao in sessoes
            if sessao["rpe_medio"] is not None
        ],
        "carga_rpe_exercicio": sorted(carga_rpe, key=lambda item: item["volume"], reverse=True),
        "volume_grupo_semana": sorted(volume_grupo_semana.values(), key=lambda item: (item["periodo"], item["grupo"])),
        "rpe_distribuicao": [
            {"rpe": rpe, "quantidade": rpe_distribuicao[rpe]}
            for rpe in sorted(rpe_distribuicao, key=lambda valor: int(valor))
        ],
        "ultima_vs_media3": comparacao_media3,
    }


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


def _render_mapa_muscular(mapa):
    grupos = {item["grupo"]: item for item in mapa["grupos"]}
    dados_anatomicos = json.loads(MUSCLE_MAP_ASSET.read_text(encoding="utf-8"))
    grupo_por_musculo = {
        muscle_id: grupo
        for grupo, muscle_ids in MUSCLE_IDS_BY_GROUP.items()
        for muscle_id in muscle_ids
    }

    def render_vista(vista):
        caminhos = []
        for musculo in dados_anatomicos[vista]:
            grupo = grupo_por_musculo.get(musculo["id"])
            item = grupos.get(grupo)
            if item:
                opacidade = 0.22 + (0.73 * item["intensidade"])
                preenchimento = f"rgba(239, 68, 68, {opacidade:.3f})"
                titulo = (
                    f"{grupo}: {_fmt_numero(item['volume'])} kg "
                    f"({item['intensidade'] * 100:.0f}% do maior volume muscular)"
                )
                dados = (
                    f'data-grupo="{html.escape(grupo, quote=True)}" '
                    f'data-volume="{item["volume"]:.1f}"'
                )
            else:
                preenchimento = "rgba(148, 163, 184, 0.08)"
                titulo = musculo["nome"]
                dados = ""
            caminhos.append(
                f'<path d="{html.escape(musculo["caminho"], quote=True)}" '
                f'class="musculo" style="fill: {preenchimento}" {dados}>'
                f"<title>{html.escape(titulo)}</title></path>"
            )
        return "\n".join(caminhos)

    anterior = render_vista("front")
    posterior = render_vista("back")
    legenda = "\n".join(
        f"""
        <div class="mapa-legenda-item">
          <span class="mapa-cor" style="opacity: {0.22 + item['intensidade'] * 0.73:.3f}"></span>
          <span>{html.escape(item["grupo"])}</span>
          <strong>{_fmt_numero(item["volume"])} kg</strong>
        </div>
        """
        for item in mapa["grupos"]
    )
    data = html.escape(mapa["data"] or "-")
    return f"""
    <div class="mapa-muscular-layout">
      <div class="mapa-vistas">
        <figure>
          <svg class="mapa-corpo" viewBox="0 0 35 93" role="img"
               aria-label="Mapa muscular anterior da ultima sessao">
            {anterior}
          </svg>
          <figcaption>Anterior</figcaption>
        </figure>
        <figure>
          <svg class="mapa-corpo" viewBox="37 0 35 93" role="img"
               aria-label="Mapa muscular posterior da ultima sessao">
            {posterior}
          </svg>
          <figcaption>Posterior</figcaption>
        </figure>
      </div>
      <div class="mapa-legenda">
        <p>Sessao de <strong>{data}</strong>. A opacidade e relativa ao maior
        volume muscular desse treino.</p>
        {legenda or '<p class="vazio">Sem grupos musculares registrados.</p>'}
      </div>
    </div>
    <p class="mapa-fonte">
      Anatomia vetorial adaptada de body-muscles, por Ivan Vulovic,
      licenciada sob Apache-2.0.
    </p>
    """


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


def _render_barras_simples(itens, chave_rotulo, chave_valor, unidade=""):
    if not itens:
        return "<p class=\"vazio\">Sem dados suficientes.</p>"
    maximo = max(item[chave_valor] for item in itens) or 1
    barras = []
    for item in itens:
        largura = max((item[chave_valor] / maximo) * 100, 2)
        barras.append(
            f"""
            <div class="barra-horizontal">
              <span>{html.escape(str(item[chave_rotulo]))}</span>
              <div><i style="width: {largura:.1f}%"></i></div>
              <strong>{_fmt_numero(item[chave_valor])}{unidade}</strong>
            </div>
            """
        )
    return "\n".join(barras)


def _render_dispersao_volume_rpe(pontos):
    if not pontos:
        return "<p class=\"vazio\">Sem RPE registrado para cruzar com volume.</p>"
    width, height, padding = 760, 300, 36
    volumes = [p["volume"] for p in pontos]
    rpes = [p["rpe_medio"] for p in pontos]
    min_volume, max_volume = min(volumes), max(volumes)
    min_rpe, max_rpe = min(rpes), max(rpes)
    span_volume = max(max_volume - min_volume, 1)
    span_rpe = max(max_rpe - min_rpe, 1)
    circulos = []
    for ponto in pontos:
        x = padding + ((ponto["volume"] - min_volume) / span_volume) * (width - padding * 2)
        y = height - padding - ((ponto["rpe_medio"] - min_rpe) / span_rpe) * (height - padding * 2)
        circulos.append(
            f"""
            <circle class="ponto-analise" cx="{x:.1f}" cy="{y:.1f}" r="5"></circle>
            <text class="rotulo-data" x="{x:.1f}" y="{y + 18:.1f}" text-anchor="middle">{html.escape(ponto["data"][5:])}</text>
            """
        )
    return f"""
    <svg viewBox="0 0 {width} {height}" role="img" aria-label="Dispersao de volume por RPE medio">
      <line class="eixo" x1="{padding}" y1="{height - padding}" x2="{width - padding}" y2="{height - padding}"></line>
      <line class="eixo" x1="{padding}" y1="{padding}" x2="{padding}" y2="{height - padding}"></line>
      <text class="rotulo-data" x="{width - padding}" y="{height - 8}" text-anchor="end">volume</text>
      <text class="rotulo-data" x="{padding}" y="18" text-anchor="start">RPE</text>
      {''.join(circulos)}
    </svg>
    """


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
    analises = dados["analises"]
    mapa_muscular = _render_mapa_muscular(dados["mapa_ultima_sessao"])
    grafico_volume_rpe = _render_dispersao_volume_rpe(analises["volume_rpe_sessao"])
    grafico_rpe = _render_barras_simples(analises["rpe_distribuicao"], "rpe", "quantidade")
    grafico_grupos_semana = _render_barras_simples(
        analises["volume_grupo_semana"][-12:], "grupo", "volume", " kg"
    )
    tabela_carga_rpe_analise = _linhas_tabela(
        analises["carga_rpe_exercicio"][:12],
        [
            {"valor": lambda item: html.escape(item["nome"])},
            {"valor": lambda item: f"{_fmt_decimal(item['carga'])} kg"},
            {"valor": lambda item: _fmt_decimal(item["rpe"])},
            {"valor": lambda item: f"{_fmt_numero(item['volume'])} kg"},
            {"valor": lambda item: f"{_fmt_decimal(item['um_rm'])} kg"},
        ],
    )
    tabela_media3 = _linhas_tabela(
        analises["ultima_vs_media3"],
        [
            {"valor": lambda item: html.escape(item["nome"])},
            {"valor": lambda item: f"{_fmt_numero(item['volume_atual'])} kg"},
            {"valor": lambda item: f"{_fmt_numero(item['media_volume'])} kg"},
            {
                "valor": lambda item: _fmt_delta(item["delta_volume"]),
                "classe": lambda item: _classe_delta(item["delta_volume"]),
            },
            {
                "valor": lambda item: _fmt_delta(item["delta_carga"]),
                "classe": lambda item: _classe_delta(item["delta_carga"]),
            },
            {"valor": lambda item: _fmt_decimal(item["rpe"])},
        ],
    )

    return f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Dashboard de treino - Forja de Ferro</title>
  <style>
    :root {{
      color-scheme: dark;
      --fundo: #090909;
      --texto: #e7e7e7;
      --muted: #8d8d8d;
      --linha: #2a2a2a;
      --painel: #111111;
      --painel-2: #161616;
      --verde: #62c370;
      --azul: #d8d8d8;
      --vermelho: #e05d5d;
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
      padding: 24px 0 44px;
    }}
    header {{
      display: flex;
      align-items: end;
      justify-content: space-between;
      gap: 24px;
      border-bottom: 1px solid var(--linha);
      margin-bottom: 16px;
      padding-bottom: 16px;
    }}
    h1, h2 {{ margin: 0; letter-spacing: 0; }}
    h1 {{ font-size: 30px; line-height: 1.08; }}
    h2 {{ font-size: 17px; }}
    .subtitulo {{ color: var(--muted); margin: 8px 0 0; }}
    .grade-resumo {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 10px;
      margin-bottom: 12px;
    }}
    .indicador, .painel {{
      background: var(--painel);
      border: 1px solid var(--linha);
      border-radius: 2px;
    }}
    .indicador {{ padding: 14px; min-height: 96px; }}
    .rotulo {{
      display: block;
      color: var(--muted);
      font-size: 11px;
      text-transform: uppercase;
      margin-bottom: 8px;
    }}
    .valor {{ font-size: 25px; font-weight: 700; }}
    .valor-menor {{ font-size: 19px; }}
    .positivo {{ color: var(--verde); }}
    .negativo {{ color: var(--vermelho); }}
    .layout {{
      display: block;
    }}
    .duas-colunas {{
      display: block;
    }}
    .painel {{ padding: 16px; margin-top: 12px; }}
    .abas {{
      display: flex;
      gap: 6px;
      overflow-x: auto;
      border-bottom: 1px solid var(--linha);
      padding: 0 0 12px;
      margin-bottom: 2px;
    }}
    .aba-botao {{
      border: 1px solid var(--linha);
      border-radius: 2px;
      background: transparent;
      color: var(--texto);
      cursor: pointer;
      font: inherit;
      padding: 9px 12px;
      white-space: nowrap;
    }}
    .aba-botao.ativa {{
      background: var(--texto);
      border-color: var(--texto);
      color: #080808;
    }}
    .aba-conteudo {{ display: none; }}
    .aba-conteudo.ativa {{ display: block; }}
    .filtros {{
      display: grid;
      grid-template-columns: repeat(3, minmax(150px, 1fr));
      gap: 10px;
      margin-bottom: 14px;
    }}
    label {{
      display: grid;
      gap: 6px;
      color: var(--muted);
      font-size: 11px;
      text-transform: uppercase;
    }}
    select {{
      width: 100%;
      border: 1px solid var(--linha);
      border-radius: 2px;
      background: var(--painel-2);
      color: var(--texto);
      font: inherit;
      padding: 8px 10px;
      text-transform: none;
    }}
    .linha-topo {{
      display: flex;
      align-items: baseline;
      justify-content: space-between;
      gap: 16px;
      border-bottom: 1px solid var(--linha);
      margin-bottom: 12px;
      padding-bottom: 10px;
    }}
    .linha-topo span {{ color: var(--muted); font-size: 13px; }}
    svg {{ width: 100%; height: auto; display: block; }}
    .eixo {{ stroke: var(--linha); stroke-width: 1; }}
    .linha-volume {{ fill: none; stroke: var(--azul); stroke-width: 3; }}
    .ponto-volume {{ fill: var(--fundo); stroke: var(--azul); stroke-width: 2; }}
    .ponto-analise {{ fill: var(--texto); stroke: var(--fundo); stroke-width: 2; }}
    .rotulo-volume {{
      fill: var(--texto);
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
      gap: 6px;
      align-items: end;
      padding-top: 12px;
    }}
    .barra-item {{
      height: 100%;
      min-width: 0;
      display: flex;
      flex-direction: column;
      justify-content: end;
      gap: 7px;
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
      background: var(--texto);
    }}
    .barra-horizontal {{
      display: grid;
      grid-template-columns: 120px minmax(0, 1fr) 90px;
      gap: 10px;
      align-items: center;
      border-bottom: 1px solid var(--linha);
      padding: 9px 0;
      color: var(--muted);
      font-size: 13px;
    }}
    .barra-horizontal div {{
      height: 10px;
      background: var(--painel-2);
      border: 1px solid var(--linha);
    }}
    .barra-horizontal i {{
      display: block;
      height: 100%;
      background: var(--texto);
    }}
    .barra-horizontal strong {{
      color: var(--texto);
      font-weight: 700;
      text-align: right;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }}
    th, td {{
      padding: 10px 8px;
      border-bottom: 1px solid var(--linha);
      text-align: right;
      white-space: nowrap;
    }}
    th:first-child, td:first-child {{
      text-align: left;
      white-space: normal;
    }}
    th {{ color: var(--muted); font-weight: 600; text-transform: uppercase; font-size: 11px; }}
    .vazio {{ color: var(--muted); }}
    .lista {{ margin: 0; padding-left: 18px; color: var(--texto); }}
    .lista li {{ margin: 8px 0; }}
    .mini-grade {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
    }}
    .mapa-muscular-layout {{
      display: grid;
      grid-template-columns: minmax(420px, 1.5fr) minmax(240px, 0.5fr);
      gap: 18px;
      align-items: center;
    }}
    .mapa-vistas {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 22px;
      min-width: 0;
    }}
    .mapa-vistas figure {{
      margin: 0;
      min-width: 0;
      text-align: center;
    }}
    .mapa-vistas figcaption {{
      color: var(--muted);
      font-size: 10px;
      letter-spacing: 2px;
      margin-top: 8px;
      text-transform: uppercase;
    }}
    .mapa-corpo {{
      max-height: 590px;
      overflow: visible;
      filter: drop-shadow(0 12px 24px rgba(0, 0, 0, 0.35));
    }}
    .musculo {{
      stroke: rgba(226, 232, 240, 0.34);
      stroke-width: 0.1;
      transition: filter 120ms ease, stroke 120ms ease;
    }}
    .musculo:hover {{
      filter: brightness(1.45);
      stroke: #fff;
      stroke-width: 0.2;
    }}
    .mapa-legenda {{
      display: grid;
      gap: 7px;
      align-content: center;
    }}
    .mapa-legenda > p {{
      color: var(--muted);
      font-size: 12px;
      line-height: 1.5;
      margin: 0 0 8px;
    }}
    .mapa-legenda-item {{
      display: grid;
      grid-template-columns: 14px minmax(0, 1fr) auto;
      gap: 9px;
      align-items: center;
      border-bottom: 1px solid var(--linha);
      padding: 6px 0;
      font-size: 12px;
    }}
    .mapa-legenda-item strong {{ color: var(--texto); }}
    .mapa-cor {{
      width: 12px;
      height: 12px;
      border: 1px solid #ef4444;
      background: #ef4444;
    }}
    .mapa-fonte {{
      color: #686868;
      font-size: 10px;
      margin: 12px 0 0;
      text-align: right;
    }}
    @media (max-width: 860px) {{
      header, .layout, .duas-colunas {{ display: block; }}
      header > div:last-child {{ margin-top: 12px; }}
      .grade-resumo {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      .painel {{ margin-bottom: 16px; }}
      h1 {{ font-size: 28px; }}
      .mapa-muscular-layout {{ grid-template-columns: 1fr; }}
    }}
    @media (max-width: 560px) {{
      main {{ width: min(100% - 20px, 1180px); padding-top: 20px; }}
      .grade-resumo {{ grid-template-columns: 1fr; }}
      .valor {{ font-size: 24px; }}
      th, td {{ font-size: 13px; padding: 10px 4px; }}
      .filtros, .mini-grade {{ grid-template-columns: 1fr; }}
      .mapa-vistas {{ gap: 10px; }}
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

    <nav class="abas" aria-label="Abas do dashboard">
      <button class="aba-botao ativa" type="button" data-aba="geral">Geral</button>
      <button class="aba-botao" type="button" data-aba="exercicios">Exercicios</button>
      <button class="aba-botao" type="button" data-aba="periodos">Periodos</button>
      <button class="aba-botao" type="button" data-aba="analises">Analises</button>
      <button class="aba-botao" type="button" data-aba="recordes">Recordes</button>
      <button class="aba-botao" type="button" data-aba="filtros">Filtros</button>
    </nav>

    <section class="aba-conteudo ativa" data-painel-aba="geral">
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
    </section>

    <section class="aba-conteudo" data-painel-aba="exercicios">
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
    </section>

    <section class="aba-conteudo" data-painel-aba="periodos">
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
    </section>

    <section class="aba-conteudo" data-painel-aba="analises">
      <article class="painel">
        <div class="linha-topo">
          <h2>Mapa muscular da ultima sessao</h2>
          <span>volume atribuido por grupo</span>
        </div>
        {mapa_muscular}
      </article>

      <article class="painel">
        <div class="linha-topo">
          <h2>Volume x RPE medio</h2>
          <span>por sessao</span>
        </div>
        {grafico_volume_rpe}
      </article>

      <article class="painel">
        <div class="linha-topo">
          <h2>Carga x RPE por exercicio</h2>
          <span>ultimo registro</span>
        </div>
        <table>
          <thead><tr><th>Exercicio</th><th>Carga</th><th>RPE</th><th>Volume</th><th>1RM</th></tr></thead>
          <tbody>{tabela_carga_rpe_analise}</tbody>
        </table>
      </article>

      <article class="painel">
        <div class="linha-topo">
          <h2>Volume semanal por grupo</h2>
          <span>ultimos grupos registrados</span>
        </div>
        {grafico_grupos_semana}
      </article>

      <article class="painel">
        <div class="linha-topo">
          <h2>Distribuicao de RPE</h2>
          <span>todos os registros</span>
        </div>
        {grafico_rpe}
      </article>

      <article class="painel">
        <div class="linha-topo">
          <h2>Ultima sessao vs media das 3 anteriores</h2>
          <span>por exercicio</span>
        </div>
        <table>
          <thead><tr><th>Exercicio</th><th>Volume atual</th><th>Media 3</th><th>Delta volume</th><th>Delta carga</th><th>RPE</th></tr></thead>
          <tbody>{tabela_media3}</tbody>
        </table>
      </article>
    </section>

    <section class="aba-conteudo" data-painel-aba="recordes">
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
    </section>

    <section class="aba-conteudo" data-painel-aba="filtros">
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
    const botoesAbas = document.querySelectorAll(".aba-botao");
    const paineisAbas = document.querySelectorAll(".aba-conteudo");

    botoesAbas.forEach((botao) => {{
      botao.addEventListener("click", () => {{
        const aba = botao.dataset.aba;
        botoesAbas.forEach((item) => item.classList.toggle("ativa", item === botao));
        paineisAbas.forEach((painel) =>
          painel.classList.toggle("ativa", painel.dataset.painelAba === aba)
        );
      }});
    }});

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
