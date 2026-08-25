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
import unicodedata
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

# Todas as instrucoes assumem destro (guarda esquerda a frente). Canhoto inverte
# tudo: onde se le "esquerda" leia "direita".
LATERALIDADE = ("Instrucoes escritas para destro (pe e mao esquerdos a frente). "
                "Se voce for canhoto, inverta todos os lados.")

# Biblioteca de execucao. Cada bloco do roteiro aponta para as chaves usadas nele,
# e /como <chave> devolve o passo a passo. Fica separado dos roteiros de proposito:
# a mesma tecnica aparece em terca, quinta e sabado -- descrever em cada lugar
# geraria tres versoes que divergem na primeira correcao.
TECNICAS = {
    "base": {
        "nome": "Base e guarda",
        "passos": [
            "Pes na largura dos ombros; recue o pe direito cerca de um passo e meio.",
            "Pe da frente apontando ~45 graus para dentro; pe de tras ~45 a 70 graus para fora.",
            "Calcanhar de tras levemente levantado. Peso 50/50 entre as pernas.",
            "Joelhos levemente flexionados — nunca travados.",
            "Queixo para baixo, olhando por cima das sobrancelhas.",
            "Mao esquerda na altura da bochecha, um palmo a frente do rosto.",
            "Mao direita colada na bochecha direita, nao encostada no queixo.",
            "Cotovelos fechados para dentro, cobrindo costelas e figado.",
            "Ombros levemente elevados, protegendo a lateral do queixo.",
        ],
        "erros": [
            "Pes na mesma linha: perde equilibrio lateral e cai com qualquer empurrao.",
            "Base larga demais: fica estavel mas nao consegue se mover.",
            "Queixo levantado.",
            "Cotovelos abertos, deixando o tronco descoberto.",
        ],
    },
    "passos": {
        "nome": "Deslocamento",
        "passos": [
            "Para frente: pe da frente sai primeiro, pe de tras acompanha na mesma medida.",
            "Para tras: pe de tras sai primeiro, pe da frente acompanha.",
            "Para a direita: pe direito primeiro. Para a esquerda: pe esquerdo primeiro.",
            "Passos curtos, de 10 a 20 cm, deslizando pelo chao.",
            "A base recompoe imediatamente depois de cada passo.",
            "A guarda nao se mexe enquanto os pes trabalham.",
        ],
        "erros": [
            "Cruzar os pes: e o momento em que voce esta mais vulneravel.",
            "Saltar em vez de deslizar.",
            "Passos largos que desmontam a base.",
            "Deixar as maos cairem enquanto anda.",
        ],
    },
    "jab": {
        "nome": "Jab (1) — soco reto da mao da frente",
        "passos": [
            "Sai direto da guarda, sem puxar a mao para tras antes.",
            "Empurre o punho esquerdo em linha reta a partir da altura do queixo.",
            "Gire o punho no trajeto: a palma termina virada para baixo.",
            "O ombro esquerdo sobe e cobre o queixo no momento do impacto.",
            "Pequeno giro de tronco e quadril; o pe da frente pivota de leve.",
            "Contato com os dois primeiros nos (indicador e medio), punho reto.",
            "Recolha pelo mesmo caminho, mais rapido do que foi.",
        ],
        "erros": [
            "Telegrafar: puxar a mao para tras antes de bater.",
            "Punho dobrado no impacto — e assim que se machuca o pulso.",
            "Deixar a mao direita cair enquanto o jab sai.",
            "Estender o cotovelo ate travar.",
        ],
    },
    "direto": {
        "nome": "Direto (2) — soco reto da mao de tras",
        "passos": [
            "Comeca no chao: gire o pe direito para dentro como se esmagasse um cigarro.",
            "A forca sobe em ordem: pe, quadril, tronco, ombro e so entao o braco.",
            "O punho sai do queixo em linha reta; palma vira para baixo no impacto.",
            "A mao esquerda fica colada no rosto o tempo todo.",
            "O peso transfere para a perna da frente, sem passar a linha do pe da frente.",
            "Recolha girando de volta para a base, nao apenas puxando o braco.",
        ],
        "erros": [
            "Bater so com o braco, sem girar quadril: e o erro que tira toda a potencia.",
            "Manter o calcanhar de tras plantado no chao.",
            "Inclinar o tronco a frente e expor o queixo.",
            "Esquecer a guarda esquerda no caminho de volta.",
        ],
    },
    "gancho": {
        "nome": "Gancho (3) — soco circular da mao da frente",
        "passos": [
            "Cotovelo travado em ~90 graus, na mesma altura do alvo.",
            "O golpe vem da rotacao do corpo: pe da frente, quadril e tronco giram juntos.",
            "Punho, cotovelo e ombro permanecem na mesma linha horizontal.",
            "Palma pode ficar virada para dentro ou para baixo — escolha uma e mantenha.",
            "Contato com os nos, punho reto e firme.",
            "Volte a guarda desfazendo a rotacao.",
        ],
        "erros": [
            "Abrir o braco: vira tapa e machuca o ombro.",
            "Baixar o ombro do lado que bate.",
            "Perder completamente a guarda do outro lado.",
        ],
    },
    "jabcorpo": {
        "nome": "Jab no corpo",
        "passos": [
            "Mesma mecanica do jab, mas voce desce flexionando os JOELHOS.",
            "A coluna permanece reta; quem desce sao as pernas.",
            "A cabeca sai da linha central ao descer.",
            "Alvo na altura do plexo solar / figado.",
            "Suba imediatamente de volta a guarda alta.",
        ],
        "erros": [
            "Curvar as costas em vez de dobrar os joelhos.",
            "Olhar para o chao ao descer.",
            "Ficar embaixo depois do golpe.",
        ],
    },
    "saidalateral": {
        "nome": "Saida lateral",
        "passos": [
            "Termine a combinacao e imediatamente de 1 ou 2 passos para o lado.",
            "Nunca recue em linha reta — e a trajetoria que o adversario ja esta seguindo.",
            "Guarda alta durante todo o deslocamento.",
            "Recomponha a base antes de pensar no proximo golpe.",
        ],
        "erros": [
            "Parar para admirar o saco depois de bater.",
            "Sair de guarda baixa.",
        ],
    },
    "teep": {
        "nome": "Teep — chute frontal de empurrao",
        "passos": [
            "Levante o joelho ate a altura do quadril, bem a frente do corpo.",
            "Puxe a ponta do pe para cima: o contato e com a SOLA do pe.",
            "Estenda o quadril a frente — e um empurrao, nao um chute de impacto.",
            "Recolha o pe pela mesma trajetoria, de volta a base.",
            "As maos ficam em guarda do inicio ao fim.",
        ],
        "erros": [
            "Bater com os dedos do pe.",
            "Jogar a perna sem levantar o joelho primeiro.",
            "Deixar o pe cair no chao a frente, virando um passo.",
        ],
    },
    "joelho": {
        "nome": "Joelhada frontal",
        "passos": [
            "Levante o joelho na diagonal, de baixo para cima e a frente.",
            "Estenda o quadril a frente; a ponta do pe aponta para baixo.",
            "Contato com a parte de cima da canela, logo abaixo do joelho.",
            "Os bracos descem em oposicao, como se puxassem o alvo para baixo.",
            "O pe de apoio pivota de leve, acompanhando o quadril.",
            "Recolha e recomponha a base.",
        ],
        "erros": [
            "Bater com a rotula (patela) — dano articular direto.",
            "Nao avancar o quadril: vira levantamento de perna sem forca.",
            "Segurar as correntes ou o topo do saco com violencia.",
        ],
    },
    "chutebaixo": {
        "nome": "Chute baixo (low kick)",
        "passos": [
            "Passo curto de abertura com o pe da frente, ligeiramente para fora da linha.",
            "GIRE o pe de apoio ate o calcanhar apontar para o alvo — sem isso nao ha potencia e o joelho sofre.",
            "A perna vem como um taco de beisebol, joelho levemente flexionado.",
            "Contato com o terco inferior da CANELA, na coxa do alvo.",
            "O braco do mesmo lado desce e vai para tras, como contrapeso.",
            "Recolha pelo mesmo caminho ou complete o giro — nunca deixe a perna morta.",
        ],
        "erros": [
            "Nao girar o pe de apoio: principal causa de lesao de joelho em iniciante.",
            "Bater com o peito do pe em vez da canela.",
            "Chutar como chute de futebol, com a perna estendida.",
            "Ficar de costas para o saco depois do chute.",
        ],
    },
    "girodope": {
        "nome": "Giro do pe de apoio (drill isolado)",
        "passos": [
            "Sem chutar: apenas levante o calcanhar do pe de apoio e gire ate ele apontar para o alvo.",
            "Os bracos acompanham a rotacao naturalmente.",
            "20 a 30 repeticoes lentas por lado.",
            "So depois que o giro sair automatico voce adiciona a perna que chuta.",
        ],
        "erros": [
            "Girar o joelho em vez do pe — e exatamente o movimento que lesiona.",
        ],
    },
    "bloqueio": {
        "nome": "Bloqueio e resposta",
        "passos": [
            "Contra soco alto: o cotovelo sobe, a luva encosta na tempora, voce olha por cima.",
            "Contra chute baixo: levante a canela, joelho apontando um pouco para fora, pe flexionado.",
            "Estrutura firme — nunca receba com o braco solto.",
            "Imediatamente apos bloquear, responda com um jab. Bloqueio sem resposta e so apanhar organizado.",
        ],
        "erros": [
            "Fechar os olhos.",
            "Afastar a mao do rosto para 'ir buscar' o golpe.",
            "Ficar so bloqueando, sem devolver.",
        ],
    },
    "sombra": {
        "nome": "Boxe-sombra",
        "passos": [
            "Sem saco, de frente para um espelho ou gravando com o celular.",
            "Comece so com base e passos; depois adicione jab; depois combinacoes.",
            "Prioridade e forma perfeita, nao velocidade.",
            "Toda mao que sai volta para a guarda antes da proxima.",
        ],
        "erros": [
            "Acelerar antes de a forma estar limpa.",
            "Bater no ar travando o cotovelo.",
        ],
    },
    "prancha": {
        "nome": "Prancha",
        "passos": [
            "Antebracos no chao, cotovelos exatamente sob os ombros.",
            "Corpo em linha reta: calcanhar, quadril, ombro e cabeca alinhados.",
            "Contraia gluteo e abdomen como se fosse levar um soco na barriga.",
            "Respire normalmente durante os 30 s.",
        ],
        "erros": [
            "Quadril subindo (virou triangulo) ou afundando (lombar sofre).",
            "Prender a respiracao.",
            "Olhar para frente em vez de para o chao.",
        ],
    },
    "bandagem": {
        "nome": "Bandagem de 5 m",
        "passos": [
            "Polegar na alca, bandagem passando pelo DORSO da mao.",
            "3 voltas no punho.",
            "3 voltas na palma, subindo em direcao aos dedos.",
            "Entre os dedos: mindinho/anelar, anelar/medio, medio/indicador — subindo pelo dorso, voltando pela palma.",
            "Volte ao punho e cruze pelo dorso em X, 2 ou 3 vezes.",
            "3 voltas cobrindo os nos dos dedos.",
            "Termine no punho e feche o velcro.",
            "Teste: feche o punho. Firme, sem formigar.",
        ],
        "erros": [
            "Apertada demais: mao esfria, formiga ou perde cor — refaca mais folgada.",
            "Frouxa no punho: nao protege exatamente onde a lesao acontece.",
            "Pular a passagem entre os dedos, deixando os nos sem colchao.",
        ],
    },
    "elevacaojoelhos": {
        "nome": "Elevacao alternada dos joelhos",
        "passos": [
            "Em pe, guarda alta, como se fosse bater.",
            "Levante alternadamente o joelho ate a altura do quadril.",
            "Estenda o quadril no topo: e o mesmo padrao da joelhada, sem o impacto.",
            "Ritmo controlado — nao e corrida no lugar.",
            "Abdomen contraido, tronco vertical.",
        ],
        "erros": [
            "Correr no lugar sem realmente levantar o joelho.",
            "Inclinar o tronco para tras para 'ajudar' a perna a subir.",
            "Joelho parando abaixo da linha do quadril.",
        ],
    },
    "corda": {
        "nome": "Pular corda",
        "passos": [
            "Altura certa: pisando no meio da corda, as alcas chegam a axila.",
            "Saltos baixos, 2 a 3 cm do chao — o objetivo e ritmo, nao altura.",
            "Aterrisse na ponta dos pes, joelho levemente flexionado para absorver.",
            "O giro vem do PUNHO; os cotovelos ficam proximos ao corpo.",
            "Se errar, recomece sem parar o ritmo do corpo.",
        ],
        "erros": [
            "Saltos altos: sobrecarrega panturrilha e tendao de aquiles, e a lesao "
            "mais comum de quem volta a pular corda.",
            "Aterrissar de calcanhar.",
            "Girar com o ombro e o braco inteiro.",
        ],
    },
    "controlarsaco": {
        "nome": "Controlar o saco",
        "passos": [
            "Controlar = manter distancia e ritmo enquanto o saco balanca, sem bater forte.",
            "Acompanhe o saco com passos curtos, guarda sempre alta.",
            "Espere o saco passar o ponto mais proximo antes de voltar a bater.",
            "Use jabs leves para amortecer e reposicionar o saco.",
            "Se precisar para-lo, use a palma aberta na LATERAL do saco.",
        ],
        "erros": [
            "Agarrar o topo do saco ou a corrente com violencia — quem paga e o ombro.",
            "Bater de frente no saco enquanto ele volta em sua direcao.",
            "Parar de se mover e ficar so esperando o saco.",
        ],
    },
    "respiracao": {
        "nome": "Respiracao",
        "passos": [
            "Durante os rounds: expire curto e forte a cada golpe. Nunca prenda o ar.",
            "Na volta a calma: inspire pelo nariz 4 s, segure 2 s, expire pela boca 6 s.",
            "8 a 10 ciclos, em pe com as maos no quadril ou sentado.",
            "Se estiver ofegante demais para falar uma frase, reduza a intensidade.",
        ],
        "erros": [
            "Prender a respiracao durante o round: principal causa de cansaco precoce.",
            "Respirar so pela boca, ofegando, entre os rounds.",
        ],
    },
    "mobilidade": {
        "nome": "Mobilidade de aquecimento",
        "passos": [
            "Ombros: 10 circulos grandes para tras e 10 para frente.",
            "Quadril: joelho elevado, 10 circulos por lado.",
            "Tornozelo: circulos em cada lado e um agachamento profundo mantido por 20 s.",
            "Coluna toracica: maos na nuca, 10 rotacoes para cada lado.",
            "Tudo em movimento — sem alongamento estatico longo antes de bater.",
        ],
        "erros": [
            "Alongar parado por muito tempo antes do treino: reduz forca e nao previne lesao.",
        ],
    },
}

# Como o operador pode digitar cada tecnica.
ALIASES = {
    "guarda": "base", "postura": "base",
    "deslocamento": "passos", "passo": "passos", "movimentacao": "passos",
    "1": "jab",
    "2": "direto", "cross": "direto",
    "3": "gancho", "hook": "gancho",
    "jabnocorpo": "jabcorpo", "soconocorpo": "jabcorpo", "corpo": "jabcorpo",
    "saida": "saidalateral", "sair": "saidalateral",
    "pushkick": "teep", "chutefrontal": "teep",
    "joelhada": "joelho",
    "lowkick": "chutebaixo", "chute": "chutebaixo", "chutebaixodaperna": "chutebaixo",
    "giro": "girodope", "pedeapoio": "girodope",
    "defesa": "bloqueio", "bloquear": "bloqueio",
    "shadow": "sombra", "boxesombra": "sombra",
    "core": "prancha", "abdomen": "prancha",
    "bandagens": "bandagem", "enfaixar": "bandagem", "atadura": "bandagem",
    "aquecimento": "mobilidade", "alongamento": "mobilidade",
    "joelhos": "elevacaojoelhos", "elevacaodejoelhos": "elevacaojoelhos",
    "pularcorda": "corda",
    "controlar": "controlarsaco", "saco": "controlarsaco",
    "respirar": "respiracao", "folego": "respiracao",
}


def _normalizar(texto):
    """Minusculo, sem acento e sem espaco/pontuacao -- '/como Chute Baixo',
    '/como chute-baixo' e '/como CHUTEBAIXO' precisam cair na mesma chave."""
    texto = unicodedata.normalize("NFKD", str(texto))
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return "".join(c for c in texto.lower() if c.isalnum())


def buscar_tecnica(termo):
    """Chave da tecnica, ou None. Aceita nome exato, alias e prefixo."""
    chave = _normalizar(termo)
    if not chave:
        return None
    if chave in TECNICAS:
        return chave
    if chave in ALIASES:
        return ALIASES[chave]
    # Prefixo so resolve se for inequivoco -- 'j' nao pode virar jab por sorte.
    candidatos = [k for k in TECNICAS if k.startswith(chave)]
    if len(candidatos) == 1:
        return candidatos[0]
    return None


def parametros_da_semana(semana):
    """Rounds, duracao, potencia e objetivo da semana. Fora de 1-8, usa a faixa
    mais proxima -- o roteiro nao deve quebrar so porque o operador digitou 9."""
    semana = max(1, min(8, int(semana)))
    for (ini, fim), params in PROGRESSAO.items():
        if ini <= semana <= fim:
            return params
    return PROGRESSAO[(1, 2)]


def _bloco(titulo, duracao, itens, nota=None, tecnicas=()):
    """`tecnicas`: chaves de TECNICAS usadas neste bloco. Viram atalhos /como no
    fim da mensagem, em vez de inflar o bloco com o passo a passo inteiro (o
    Telegram corta mensagem em 4096 caracteres)."""
    faltando = [t for t in tecnicas if t not in TECNICAS]
    if faltando:
        raise KeyError(f"bloco '{titulo}' referencia tecnica inexistente: {faltando}")
    return {"titulo": titulo, "duracao": duracao, "itens": itens, "nota": nota,
            "tecnicas": list(tecnicas)}


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
        ], tecnicas=("mobilidade", "sombra", "base")),
        _bloco("Tecnica sem potencia", "15 min", [
            "1) Base, guarda e passos para frente e para tras",
            "2) Jab parado",
            "3) Direto parado",
            "4) Jab + direto",
            "5) Jab + direto saindo lateralmente",
        ], nota=f"5 blocos de 2 min, 1 min de descanso entre eles.\n{NUMERACAO}",
           tecnicas=("base", "passos", "jab", "direto", "saidalateral")),
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
                "dedos alinhados, pulso reto e mao voltando imediatamente para a guarda.",
           tecnicas=("jab", "direto", "gancho", "jabcorpo", "saidalateral",
                     "passos", "controlarsaco")),
        _bloco("Condicionamento", "5 min", [
            "5 ciclos de:",
            "  30 s de socos retos rapidos e leves",
            "  30 s andando e respirando",
        ], tecnicas=("jab", "direto")),
        _bloco("Volta a calma", "6 min", [
            "Caminhada leve",
            "Respiracao",
            "Mobilidade suave dos ombros",
        ], tecnicas=("mobilidade", "respiracao")),
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
        ], tecnicas=("mobilidade", "sombra", "base", "elevacaojoelhos")),
        _bloco("Tecnica", "15 min", [
            "1) Guarda e deslocamento",
            "2) Bloqueio imaginario e resposta com jab",
            "3) Teep sem forca, primeiro no ar",
            "4) Joelho frontal alternado no ar",
            "5) Jab + direto + joelho",
        ], nota="5 blocos de 2 min, 1 min de descanso.",
           tecnicas=("base", "passos", "bloqueio", "teep", "joelho")),
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
                "violencia as correntes nem a parte superior do saco.",
           tecnicas=("jab", "direto", "teep", "joelho", "saidalateral",
                     "controlarsaco")),
        _bloco("Estabilidade", "5 min", [
            "Prancha: 3 x 30 s (30 s de descanso entre elas)",
            "Tempo restante: respiracao e caminhada",
        ], tecnicas=("prancha",)),
        _bloco("Volta a calma", "6 min", [
            "Caminhada leve",
            "Respiracao",
            "Mobilidade suave dos ombros",
        ], nota="A sessao inteira deve ficar em RPE 5-6/10 — ela existe leve de "
                "proposito, para nao prejudicar a musculacao de sexta.",
           tecnicas=("mobilidade", "respiracao")),
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
        ], tecnicas=("mobilidade", "sombra", "girodope", "corda", "chutebaixo")),
        _bloco("Tecnica", "12 min", [
            "1) Giro do pe de apoio, sem chutar",
            "2) Chute baixo com a perna de tras, no ar",
            "3) Chute baixo com a perna da frente, no ar",
            "4) Jab + direto + chute baixo",
        ], nota="4 blocos de 2 min, 1 min de descanso.",
           tecnicas=("girodope", "chutebaixo", "jab", "direto")),
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
                "Nunca chute a parte metalica, a corrente ou a extremidade inferior.",
           tecnicas=("jab", "direto", "chutebaixo", "joelho", "controlarsaco")),
        _bloco("Finalizacao", "6 min", [
            "6 ciclos de:",
            "  30 s trabalhando no saco",
            "  30 s caminhando",
        ], tecnicas=("jab", "direto", "chutebaixo")),
        _bloco("Volta a calma", "6 min", [
            "Caminhada leve",
            "Respiracao",
            "Mobilidade suave dos ombros",
        ], tecnicas=("mobilidade", "respiracao")),
    ],
}

# ----------------------------------------------------- FUNDAMENTOS (sem saco)
#
# Fase anterior ao ciclo de 8 semanas: aprender cada movimento isolado, sem saco
# e sem combinacao. O motivo e motor, nao de conforto -- bater no saco antes de
# o padrao estar formado grava o padrao errado com impacto junto, e chute baixo
# sem giro do pe de apoio lesiona o joelho na primeira sessao.
#
# Por isso conta REPETICAO, nao round: sem impacto nao existe intensidade para
# dosar por tempo, e o que importa e o numero de execucoes limpas.
#
# Reusa as mesmas TECNICAS do ciclo com saco. Se uma instrucao mudar, muda nos
# dois lugares de uma vez.

SEM_COMBO = ("Um movimento por vez. Nao emende com nenhum outro golpe nesta "
             "fase — combinacao so depois que cada movimento sair sozinho.")

# Sem impacto nao ha o que proteger, e mao nua deixa o punho visivel para
# correcao. Bandagem, luva e corda so entram junto com o saco.
SEM_ACESSORIO = ("Nada nas maos e nada no chao: sem bandagem, sem luva, sem "
                 "corda, sem saco. So o corpo e um espelho ou o celular filmando.")

FUNDAMENTOS_A = {
    "nome": "Fundamentos A — postura, guarda e socos retos",
    "intensidade": "leve (aprendizado, sem impacto)",
    "usa_progressao": False,
    "blocos": [
        _bloco("Preparacao", "6 min", [
            "3 min de mobilidade de ombros, quadril e tornozelos",
            "2 min de caminhada leve pela sala",
            "1 min so respirando, decidindo em que voce vai prestar atencao hoje",
        ], nota=f"{SEM_ACESSORIO} Voce precisa enxergar a propria mao para "
                "corrigir punho e trajetoria.",
           tecnicas=("mobilidade", "respiracao")),
        _bloco("Base e guarda", "10 min", [
            "Monte a base do zero 20 vezes: pes juntos, recue o direito, ajuste os angulos",
            "Segure a guarda por 3 x 30 s de frente para o espelho",
            "1 min andando pela sala sem desmanchar a guarda",
        ], nota="Confira a cada repeticao: queixo baixo, cotovelos para dentro, "
                "joelhos moles, calcanhar de tras levantado.",
           tecnicas=("base", "sombra")),
        _bloco("Deslocamento", "7 min", [
            "Frente e tras: 20 idas e voltas",
            "Direita e esquerda: 20 para cada lado",
            "Quadrado: 10 voltas em cada sentido",
        ], nota="Regra unica desta fase: os pes nunca se cruzam.",
           tecnicas=("passos",)),
        _bloco("Jab isolado", "8 min", [
            "30 jabs LENTOS de frente para o espelho, um a cada 3 s",
            "30 jabs em ritmo medio, ainda sem forca",
            "20 jabs dando um passo a frente junto",
        ], nota=f"Pare a cada 10 e confira: punho reto, mao voltou ao rosto. {SEM_COMBO}",
           tecnicas=("jab",)),
        _bloco("Direto isolado", "8 min", [
            "20 giros de pe direito e quadril, SEM o braco",
            "30 diretos lentos, sentindo a ordem pe > quadril > tronco > braco",
            "30 diretos em ritmo medio",
            "10 diretos filmados de lado",
        ], nota=f"O giro vem primeiro; o braco e o ultimo elo. {SEM_COMBO}",
           tecnicas=("direto",)),
        _bloco("Volta a calma", "4 min", [
            "Caminhada leve",
            "Respiracao 4-2-6, 8 ciclos",
            "Anote qual movimento pareceu mais estranho hoje",
        ], tecnicas=("respiracao",)),
    ],
}

FUNDAMENTOS_B = {
    "nome": "Fundamentos B — socos circulares e defesa",
    "intensidade": "leve (aprendizado, sem impacto)",
    "usa_progressao": False,
    "blocos": [
        _bloco("Preparacao", "6 min", [
            "3 min de mobilidade de ombros, quadril e tornozelos",
            "Remonte a base 10 vezes",
            "20 jabs e depois 20 diretos lentos, so para reaquecer o padrao",
        ], nota=f"Jab e direto aqui sao revisao, ainda um de cada vez. {SEM_ACESSORIO}",
           tecnicas=("mobilidade", "base", "jab", "direto")),
        _bloco("Gancho isolado", "9 min", [
            "20 rotacoes de tronco com os bracos soltos, sem golpe",
            "30 ganchos lentos, cotovelo travado a 90 graus",
            "30 ganchos em ritmo medio",
        ], nota=f"No espelho: punho, cotovelo e ombro na mesma linha horizontal. {SEM_COMBO}",
           tecnicas=("gancho",)),
        _bloco("Jab no corpo", "8 min", [
            "20 descidas sem golpe: flexione os JOELHOS, coluna reta",
            "30 jabs no corpo lentos, descendo e subindo",
            "20 em ritmo medio",
        ], nota=f"A cabeca sai da linha central ao descer. {SEM_COMBO}",
           tecnicas=("jabcorpo",)),
        _bloco("Bloqueio e saida lateral", "9 min", [
            "Bloqueio alto: 30 repeticoes de cada lado",
            "Bloqueio de perna: 20 elevacoes de canela de cada lado",
            "Saida lateral: 20 para cada lado, depois de um unico jab",
        ], nota="Nunca recue em linha reta. O jab antes da saida existe so para "
                "dar o timing — continua sendo um golpe so.",
           tecnicas=("bloqueio", "saidalateral")),
        _bloco("Estabilidade", "5 min", [
            "Prancha: 3 x 30 s (30 s de descanso entre elas)",
        ], tecnicas=("prancha",)),
        _bloco("Volta a calma", "4 min", [
            "Caminhada leve",
            "Respiracao 4-2-6, 8 ciclos",
        ], tecnicas=("respiracao",)),
    ],
}

FUNDAMENTOS_C = {
    "nome": "Fundamentos C — pernas",
    "intensidade": "leve (aprendizado, sem impacto)",
    "usa_progressao": False,
    "blocos": [
        _bloco("Preparacao", "8 min", [
            "3 min de mobilidade de tornozelo e quadril",
            "2 min de elevacao alternada dos joelhos",
            "20 agachamentos livres lentos",
        ], nota=SEM_ACESSORIO,
           tecnicas=("mobilidade", "elevacaojoelhos")),
        _bloco("Giro do pe de apoio", "8 min", [
            "30 giros lentos por lado, SEM chutar",
            "20 giros por lado em ritmo medio",
        ], nota="Quem gira e o PE, nao o joelho. So passe para o chute quando o "
                "giro sair sem voce pensar — e a diferenca entre chutar e lesionar.",
           tecnicas=("girodope",)),
        _bloco("Teep isolado", "9 min", [
            "20 elevacoes de joelho na altura do quadril, sem estender",
            "30 teeps lentos por perna, ponta do pe puxada para cima",
            "20 por perna em ritmo medio",
        ], nota=f"Recolha o pe de volta a base; nunca deixe cair a frente. {SEM_COMBO}",
           tecnicas=("teep",)),
        _bloco("Joelhada isolada", "8 min", [
            "20 elevacoes diagonais de joelho, sem estender o quadril",
            "30 joelhadas lentas por perna, avancando o quadril",
            "20 por perna em ritmo medio",
        ], nota=f"O contato seria ACIMA da rotula, nunca nela. {SEM_COMBO}",
           tecnicas=("joelho",)),
        _bloco("Chute baixo isolado", "9 min", [
            "20 chutes baixos LENTOS por perna, no ar, atencao so no giro do pe de apoio",
            "20 por perna em ritmo medio",
            "10 por perna filmados de lado",
        ], nota=f"Sem forca e sem alvo: o objetivo e a trajetoria, nao o impacto. {SEM_COMBO}",
           tecnicas=("chutebaixo", "girodope")),
        _bloco("Volta a calma", "4 min", [
            "Caminhada leve",
            "Respiracao 4-2-6, 8 ciclos",
        ], tecnicas=("respiracao",)),
    ],
}

ROTEIROS = {"terca": TERCA, "quinta": QUINTA, "sabado": SABADO,
            "fundamentos_a": FUNDAMENTOS_A,
            "fundamentos_b": FUNDAMENTOS_B,
            "fundamentos_c": FUNDAMENTOS_C}

# Sessao de fundamentos sugerida por dia, espelhando ter/qui/sab do ciclo com
# saco -- assim a rotina semanal ja fica montada antes de o saco entrar.
FUNDAMENTOS_POR_DIA = {1: "fundamentos_a", 3: "fundamentos_b", 5: "fundamentos_c"}

FUNDAMENTOS_LETRAS = {"a": "fundamentos_a", "b": "fundamentos_b", "c": "fundamentos_c"}

# Quando parar de fazer fundamentos e comecar o ciclo com saco.
CRITERIO_DE_PASSAGEM = [
    "Voce monta a base e a guarda sem pensar em cada detalhe.",
    "Jab e direto voltam sozinhos para o rosto, sem voce lembrar.",
    "O pe de apoio gira sozinho no chute baixo.",
    "Voce consegue se ver filmado sem enxergar punho dobrado ou guarda caida.",
    "Nenhum movimento causa dor em punho, ombro, joelho ou tornozelo.",
]

# O que so aparece quando o saco entra. Fica explicito para a fase de
# fundamentos poder ser feita em qualquer lugar, sem comprar nada.
ENTRA_COM_O_SACO = [
    "Bandagem de 5 m — pratique com /como bandagem no dia anterior.",
    "Luvas de 16 oz.",
    "Corda, se quiser usar no aquecimento de sabado — veja /como corda.",
    "O saco propriamente dito, inspecionado antes da primeira sessao.",
]

# Dia da semana (segunda=0) -> roteiro. Segunda/quarta/sexta sao musculacao,
# domingo e descanso completo.
POR_DIA_DA_SEMANA = {1: "terca", 3: "quinta", 5: "sabado"}

REGRAS = [
    "Bandagem de 5 m e luvas de 16 oz, sempre. Passo a passo em /como bandagem.",
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
    # Fundamentos nao tem progressao semanal: sem impacto nao ha potencia nem
    # round para dosar, entao mostrar "semana N" ali so confundiria.
    progride = roteiro.get("usa_progressao", True)
    rounds, duracao_round, potencia, _ = parametros_da_semana(estado["semana"])

    # O bloco do saco e o unico cuja duracao vem da progressao, nao do roteiro.
    duracao = bloco["duracao"] or f"{rounds} de {duracao_round}"

    subtitulo = (f"semana {estado['semana']} · bloco {idx + 1} de {total}"
                 if progride else f"bloco {idx + 1} de {total} · sem equipamento, sem combo")

    linhas = [
        f"<b>{roteiro['nome']}</b>",
        f"<i>{subtitulo}</i>",
        "",
        f"<b>{bloco['titulo']}</b> — {duracao}",
        "",
    ]
    linhas += [f"• {item}" if not item.startswith("  ") else f"   {item.strip()}"
               for item in bloco["itens"]]

    if progride and bloco["titulo"] == "Saco":
        linhas += ["", f"<i>Potencia maxima desta semana: {potencia}</i>"]
    if bloco["nota"]:
        linhas += ["", f"<i>{bloco['nota']}</i>"]

    if bloco["tecnicas"]:
        atalhos = " · ".join(f"/como {t}" for t in bloco["tecnicas"])
        linhas += ["", f"<b>Como executar:</b> {atalhos}"]

    if idx + 1 < total:
        proximo = roteiro["blocos"][idx + 1]["titulo"]
        linhas += ["", f"Proximo: {proximo} — envie /proximo"]
    else:
        linhas += ["", "Ultimo bloco. /proximo encerra o roteiro."]

    return "\n".join(linhas)


def formatar_resumo(chave, semana=1):
    """Visao geral do treino, sem iniciar roteiro -- para consultar antes de ir."""
    roteiro = ROTEIROS[chave]
    progride = roteiro.get("usa_progressao", True)
    rounds, duracao_round, potencia, objetivo = parametros_da_semana(semana)

    linhas = [
        f"<b>{roteiro['nome']}</b>",
        f"<i>intensidade: {roteiro['intensidade']}</i>",
    ]
    if progride:
        linhas.append(
            f"<i>semana {semana}: {rounds} de {duracao_round}, ate {potencia} — {objetivo}</i>")
    else:
        linhas.append("<i>sem equipamento, sem combinacao — um movimento por vez</i>")
    linhas.append("")

    for i, bloco in enumerate(roteiro["blocos"], 1):
        duracao = bloco["duracao"] or f"{rounds} de {duracao_round}"
        linhas.append(f"{i}. <b>{bloco['titulo']}</b> — {duracao}")
    linhas += ["", "Envie /proximo para comecar bloco a bloco."]
    return "\n".join(linhas)


def formatar_regras():
    return "<b>Regras do ciclo</b>\n\n" + "\n".join(f"• {r}" for r in REGRAS)


def formatar_tecnica(chave):
    """Passo a passo de uma tecnica. `chave` ja resolvida por buscar_tecnica."""
    tec = TECNICAS[chave]
    linhas = [f"<b>{tec['nome']}</b>", ""]
    linhas += [f"{i}. {passo}" for i, passo in enumerate(tec["passos"], 1)]
    linhas += ["", "<b>Erros comuns</b>"]
    linhas += [f"• {erro}" for erro in tec["erros"]]
    linhas += ["", f"<i>{LATERALIDADE}</i>"]
    return "\n".join(linhas)


def formatar_tecnica_nao_encontrada(termo):
    disponiveis = " · ".join(sorted(TECNICAS))
    return (f"Nao conheco '{termo}'.\n\n"
            f"<b>Tecnicas disponiveis</b>\n{disponiveis}\n\n"
            "<i>Use /como &lt;nome&gt;, por exemplo /como chute baixo</i>")


def fundamentos_do_dia(hoje=None):
    """Sessao de fundamentos sugerida para hoje, ou None em dia de musculacao."""
    hoje = hoje or date.today()
    return FUNDAMENTOS_POR_DIA.get(hoje.weekday())


def resolver_fundamentos(termo):
    """Aceita 'a'/'b'/'c', o nome completo e a chave. None se nao reconhecer."""
    chave = _normalizar(termo)
    if chave in FUNDAMENTOS_LETRAS:
        return FUNDAMENTOS_LETRAS[chave]
    if chave in ROTEIROS and not ROTEIROS[chave].get("usa_progressao", True):
        return chave
    if chave.startswith("fundamentos") and chave[-1:] in FUNDAMENTOS_LETRAS:
        return FUNDAMENTOS_LETRAS[chave[-1]]
    return None


def formatar_indice_fundamentos(hoje=None):
    sugerida = fundamentos_do_dia(hoje)
    linhas = [
        "<b>Fase de fundamentos — sem equipamento</b>",
        "",
        "Aprender cada movimento isolado antes de bater. Bater no saco antes de "
        "o padrao estar formado grava o padrao errado com impacto junto, e chute "
        "baixo sem giro do pe de apoio machuca o joelho logo na primeira sessao.",
        "",
        f"<b>Equipamento: nenhum.</b> {SEM_ACESSORIO}",
        "",
        "<b>Sessoes</b>",
    ]
    for letra, chave in FUNDAMENTOS_LETRAS.items():
        marca = "  ← hoje" if chave == sugerida else ""
        linhas.append(f"/fundamentos {letra} — {ROTEIROS[chave]['nome']}{marca}")
    linhas += [
        "",
        "Mesma rotina do ciclo: terca, quinta e sabado. Repita as tres sessoes "
        "por 2 a 3 semanas, ou ate os criterios abaixo baterem.",
        "",
        "<b>Quando passar para o saco</b>",
    ]
    linhas += [f"• {c}" for c in CRITERIO_DE_PASSAGEM]
    linhas += ["", "<b>So entao entra o equipamento</b>"]
    linhas += [f"• {e}" for e in ENTRA_COM_O_SACO]
    linhas += ["", "<i>Nao ha pressa aqui. Uma semana a mais de fundamento custa "
                   "uma semana; um padrao errado gravado custa meses para desfazer.</i>"]
    return "\n".join(linhas)


def formatar_indice_tecnicas():
    linhas = ["<b>Biblioteca de execucao</b>", ""]
    for chave in sorted(TECNICAS):
        linhas.append(f"• /como {chave} — {TECNICAS[chave]['nome']}")
    linhas += ["", f"<i>{LATERALIDADE}</i>"]
    return "\n".join(linhas)
