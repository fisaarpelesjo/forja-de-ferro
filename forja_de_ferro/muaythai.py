"""Roteiros de Muay Thai, entregues bloco a bloco pelo Telegram.

Por que NAO usa o banco: o modelo de treino existente e serie x repeticao x
carga (`training_plan_exercises`, `training_logs`), construido para musculacao.
Muay Thai e round x tempo, com foco tecnico e percentual de potencia -- nao ha
carga para progredir nem repeticao para contar. Encaixar um no outro faria o
banco mentir e contaminaria o volume por carga que o dashboard soma.

Entao este modulo e puramente roteiro: entrega o treino do dia, bloco a bloco,
sem registrar nada. O estado (qual roteiro, qual bloco) vive em `mt_session.json`,
arquivo SEPARADO de `session.json` -- assim uma sessao de musculacao ativa e um
roteiro de Muay Thai em andamento nao se atropelam.

Bloco de 8 semanas, iniciante, treinando saco em terca/quinta/sabado, com
musculacao em segunda/quarta/sexta. Quinta e propositalmente leve para nao
prejudicar a musculacao de sexta.
"""
import json
from datetime import date
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
MT_SESSION_FILE = BASE_DIR / "mt_session.json"

# Progressao das 8 semanas: (rounds de saco, duracao do round, potencia maxima,
# objetivo). Nao ultrapassar 70% de potencia neste primeiro ciclo.
PROGRESSAO = {
    (1, 2): ("6 rounds", "2 min", "30-40%", "aprender os movimentos"),
    (3, 4): ("8 rounds", "2 min", "40-50%", "fluidez e equilibrio"),
    (5, 6): ("6 rounds", "3 min", "50-60%", "aumentar resistencia"),
    (7, 8): ("8 rounds", "3 min", "60-70%", "condicionamento e combinacoes"),
}

# Numeracao usada nas combinacoes.
NUMERACAO = "1 = jab (mao da frente) · 2 = direto (mao de tras) · 3 = gancho da frente"


def parametros_da_semana(semana):
    """Rounds, duracao, potencia e objetivo da semana. Fora de 1-8, usa a faixa
    mais proxima -- o roteiro nao deve quebrar so porque o operador digitou 9."""
    semana = max(1, min(8, int(semana)))
    for (ini, fim), params in PROGRESSAO.items():
        if ini <= semana <= fim:
            return params
    return PROGRESSAO[(1, 2)]


def _bloco(titulo, duracao, itens, nota=None):
    return {"titulo": titulo, "duracao": duracao, "itens": itens, "nota": nota}


# ----------------------------------------------------------------- TERCA

TERCA = {
    "nome": "Terca — fundamentos e socos",
    "intensidade": "moderada",
    "blocos": [
        _bloco("Aquecimento", "10 min", [
            "3 min caminhando rapido ao redor do saco",
            "2 min de mobilidade de ombros, quadril e tornozelos",
            "3 min de boxe-sombra leve",
            "2 min so postura e guarda",
        ]),
        _bloco("Tecnica sem potencia", "15 min", [
            "1) Base, guarda e passos para frente e para tras",
            "2) Jab parado",
            "3) Direto parado",
            "4) Jab + direto",
            "5) Jab + direto saindo lateralmente",
        ], nota=f"5 blocos de 2 min, 1 min de descanso entre eles.\n{NUMERACAO}"),
        _bloco("Saco", None, [
            "1) Apenas jab",
            "2) Jab + direto",
            "3) Jab + direto + saida lateral",
            "4) Jab no corpo + direto na cabeca",
            "5) Jab + direto + gancho",
            "6) Golpes leves circulando o saco",
            "7) Combinacoes livres de 2 ou 3 socos",
            "8) Condicionamento: 20 s trabalhando / 20 s controlando",
        ], nota="1 min de descanso entre rounds. Priorize acertar com os nos dos "
                "dedos alinhados, pulso reto e mao voltando imediatamente para a guarda."),
        _bloco("Condicionamento", "5 min", [
            "5 ciclos de:",
            "  30 s de socos retos rapidos e leves",
            "  30 s andando e respirando",
        ]),
        _bloco("Volta a calma", "6 min", [
            "Caminhada leve",
            "Respiracao",
            "Mobilidade suave dos ombros",
        ]),
    ],
}

# ---------------------------------------------------------------- QUINTA

QUINTA = {
    "nome": "Quinta — defesa, teep e joelhos",
    "intensidade": "leve/moderada (RPE 5-6 de 10)",
    "blocos": [
        _bloco("Aquecimento", "10 min", [
            "3 min caminhando rapido ao redor do saco",
            "2 min de mobilidade de ombros, quadril e tornozelos",
            "3 min de boxe-sombra leve",
            "2 min so postura e guarda",
            "Elevacao alternada dos joelhos",
        ]),
        _bloco("Tecnica", "15 min", [
            "1) Guarda e deslocamento",
            "2) Bloqueio imaginario e resposta com jab",
            "3) Teep sem forca, primeiro no ar",
            "4) Joelho frontal alternado no ar",
            "5) Jab + direto + joelho",
        ], nota="5 blocos de 2 min, 1 min de descanso."),
        _bloco("Saco", None, [
            "1) Jab + saida",
            "2) Jab + direto + saida",
            "3) Teep alternado, devagar",
            "4) Jab + teep",
            "5) Direto + joelho de tras",
            "6) Jab + direto + joelho de tras",
            "7) Joelho alternado, controlando o saco",
            "8) Tecnica livre leve",
        ], nota="No joelho, NAO bata com a patela. O contato e na parte frontal/superior "
                "da canela, proxima ao joelho, com o quadril avancando. Nao segure com "
                "violencia as correntes nem a parte superior do saco."),
        _bloco("Estabilidade", "5 min", [
            "Prancha: 3 x 30 s (30 s de descanso entre elas)",
            "Tempo restante: respiracao e caminhada",
        ]),
        _bloco("Volta a calma", "6 min", [
            "Caminhada leve",
            "Respiracao",
            "Mobilidade suave dos ombros",
        ], nota="A sessao inteira deve ficar em RPE 5-6/10 — ela existe leve de "
                "proposito, para nao prejudicar a musculacao de sexta."),
    ],
}

# ---------------------------------------------------------------- SABADO

SABADO = {
    "nome": "Sabado — chutes baixos e condicionamento",
    "intensidade": "moderada/forte",
    "blocos": [
        _bloco("Aquecimento", "12 min", [
            "4 min de caminhada rapida ou corda sem saltos excessivos",
            "3 min de mobilidade de tornozelo e quadril",
            "3 min de boxe-sombra",
            "2 min simulando chutes lentamente, sem saco",
        ]),
        _bloco("Tecnica", "12 min", [
            "1) Giro do pe de apoio, sem chutar",
            "2) Chute baixo com a perna de tras, no ar",
            "3) Chute baixo com a perna da frente, no ar",
            "4) Jab + direto + chute baixo",
        ], nota="4 blocos de 2 min, 1 min de descanso."),
        _bloco("Saco", None, [
            "1) Jab + direto",
            "2) Chute baixo da perna de tras",
            "3) Jab + chute baixo",
            "4) Jab + direto + chute baixo",
            "5) Direto + chute baixo",
            "6) Jab + direto + joelho",
            "7) Combinacoes livres",
            "8) Condicionamento: 20 s de golpes / 20 s movimentando",
        ], nota="Nas primeiras semanas, apenas 5 a 8 chutes por perna em cada round "
                "especifico, com forca baixa. Acerte com a CANELA, nao com o pe. "
                "Nunca chute a parte metalica, a corrente ou a extremidade inferior."),
        _bloco("Finalizacao", "6 min", [
            "6 ciclos de:",
            "  30 s trabalhando no saco",
            "  30 s caminhando",
        ]),
        _bloco("Volta a calma", "6 min", [
            "Caminhada leve",
            "Respiracao",
            "Mobilidade suave dos ombros",
        ]),
    ],
}

ROTEIROS = {"terca": TERCA, "quinta": QUINTA, "sabado": SABADO}

# Dia da semana (segunda=0) -> roteiro. Segunda/quarta/sexta sao musculacao,
# domingo e descanso completo.
POR_DIA_DA_SEMANA = {1: "terca", 3: "quinta", 5: "sabado"}

REGRAS = [
    "Bandagem de 5 m e luvas de 16 oz, sempre.",
    "Inspecione suporte, parabolts, corrente e mosquetao antes de cada sessao.",
    "Nao bata enquanto o saco estiver voltando com forca contra voce.",
    "Sem cotoveladas neste primeiro ciclo.",
    "Dor aguda em punho, polegar, cotovelo, joelho ou tornozelo = parar o golpe.",
    "Grave alguns rounds de frente e de lado: revela guarda baixa, desequilibrio e punho dobrado.",
    "Emagrecimento depende principalmente de deficit calorico — o treino ajuda, mas nao substitui.",
]


def roteiro_do_dia(hoje=None):
    """Roteiro sugerido para hoje, ou None em dia de musculacao/descanso."""
    hoje = hoje or date.today()
    return POR_DIA_DA_SEMANA.get(hoje.weekday())


# ------------------------------------------------------------- estado

def carregar_estado():
    if not MT_SESSION_FILE.exists():
        return None
    try:
        with open(MT_SESSION_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        # Estado corrompido nao pode derrubar o bot -- tratar como "sem roteiro".
        return None


def salvar_estado(estado):
    with open(MT_SESSION_FILE, "w", encoding="utf-8") as f:
        json.dump(estado, f, ensure_ascii=False, indent=2)


def limpar_estado():
    MT_SESSION_FILE.unlink(missing_ok=True)


def iniciar(chave, semana=1):
    if chave not in ROTEIROS:
        raise ValueError(f"roteiro '{chave}' nao existe")
    estado = {"roteiro": chave, "bloco": 0, "semana": max(1, min(8, int(semana))),
              "iniciado_em": date.today().isoformat()}
    salvar_estado(estado)
    return estado


def avancar():
    """Proximo bloco. Retorna None quando o roteiro acabou (e limpa o estado)."""
    estado = carregar_estado()
    if estado is None:
        return None
    estado["bloco"] += 1
    if estado["bloco"] >= len(ROTEIROS[estado["roteiro"]]["blocos"]):
        limpar_estado()
        return None
    salvar_estado(estado)
    return estado


# ---------------------------------------------------------- formatacao

def formatar_bloco(estado):
    roteiro = ROTEIROS[estado["roteiro"]]
    idx = estado["bloco"]
    bloco = roteiro["blocos"][idx]
    total = len(roteiro["blocos"])
    rounds, duracao_round, potencia, _ = parametros_da_semana(estado["semana"])

    # O bloco do saco e o unico cuja duracao vem da progressao, nao do roteiro.
    duracao = bloco["duracao"] or f"{rounds} de {duracao_round}"

    linhas = [
        f"<b>{roteiro['nome']}</b>",
        f"<i>semana {estado['semana']} · bloco {idx + 1} de {total}</i>",
        "",
        f"<b>{bloco['titulo']}</b> — {duracao}",
        "",
    ]
    linhas += [f"• {item}" if not item.startswith("  ") else f"   {item.strip()}"
               for item in bloco["itens"]]

    if bloco["titulo"] == "Saco":
        linhas += ["", f"<i>Potencia maxima desta semana: {potencia}</i>"]
    if bloco["nota"]:
        linhas += ["", f"<i>{bloco['nota']}</i>"]

    if idx + 1 < total:
        proximo = roteiro["blocos"][idx + 1]["titulo"]
        linhas += ["", f"Proximo: {proximo} — envie /proximo"]
    else:
        linhas += ["", "Ultimo bloco. /proximo encerra o roteiro."]

    return "\n".join(linhas)


def formatar_resumo(chave, semana=1):
    """Visao geral do treino, sem iniciar roteiro -- para consultar antes de ir."""
    roteiro = ROTEIROS[chave]
    rounds, duracao_round, potencia, objetivo = parametros_da_semana(semana)

    linhas = [
        f"<b>{roteiro['nome']}</b>",
        f"<i>intensidade: {roteiro['intensidade']}</i>",
        f"<i>semana {semana}: {rounds} de {duracao_round}, ate {potencia} — {objetivo}</i>",
        "",
    ]
    for i, bloco in enumerate(roteiro["blocos"], 1):
        duracao = bloco["duracao"] or f"{rounds} de {duracao_round}"
        linhas.append(f"{i}. <b>{bloco['titulo']}</b> — {duracao}")
    linhas += ["", "Envie /proximo para comecar bloco a bloco."]
    return "\n".join(linhas)


def formatar_regras():
    return "<b>Regras do ciclo</b>\n\n" + "\n".join(f"• {r}" for r in REGRAS)
