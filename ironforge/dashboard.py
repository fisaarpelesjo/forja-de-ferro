"""Dashboard local de volume de treino."""

from __future__ import annotations

import html
import json
import sqlite3
from collections import defaultdict
from pathlib import Path

from ironforge import db_ops

ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT_DIR / "temp" / "dashboard-treino.html"


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

        exercicios[row["exercise_name"]].append(
            {
                "data": row["date"],
                "session_id": session_id,
                "volume": volume,
                "carga": float(row["weight"]),
                "series": int(row["sets"]),
                "reps": int(row["reps"]),
                "rpe": float(row["rpe"]) if row["rpe"] is not None else None,
            }
        )

    volume_por_sessao = list(sessoes.values())
    volume_por_exercicio = []
    for nome, pontos in exercicios.items():
        primeiro = pontos[0]["volume"]
        ultimo = pontos[-1]["volume"]
        volume_por_exercicio.append(
            {
                "nome": nome,
                "pontos": pontos,
                "volume_total": sum(p["volume"] for p in pontos),
                "ultimo_volume": ultimo,
                "variacao": ultimo - primeiro if len(pontos) > 1 else 0.0,
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
        },
        "volume_por_sessao": volume_por_sessao,
        "volume_por_exercicio": volume_por_exercicio,
    }


def _fmt_numero(valor):
    return f"{valor:,.0f}".replace(",", ".")


def _fmt_delta(valor):
    sinal = "+" if valor > 0 else ""
    return f"{sinal}{_fmt_numero(valor)} kg"


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
    .painel {{ padding: 18px; }}
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
    @media (max-width: 860px) {{
      header, .layout {{ display: block; }}
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
  </main>
  <script type="application/json" id="dados-dashboard">{_json(dados)}</script>
</body>
</html>
"""


def salvar_dashboard(output_path=DEFAULT_OUTPUT):
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    dados = carregar_dados()
    output.write_text(gerar_html(dados), encoding="utf-8")
    return output
