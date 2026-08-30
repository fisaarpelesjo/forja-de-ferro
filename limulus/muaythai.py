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
        "resumo": "A posicao de onde todo golpe sai e para onde todo golpe volta.",
        "inicio": [
            "De pe, pes na largura dos ombros, de frente para o alvo.",
            "Recue o pe direito um passo e meio (60 a 70 cm) para tras.",
            "Os pes ficam em DUAS linhas paralelas, separadas pela largura dos "
            "ombros. Nunca na mesma linha, como se estivesse em cima de um trilho.",
        ],
        "execucao": [
            "Pe esquerdo (frente): ponta apontando para o alvo, girada 20 a 30 graus para dentro.",
            "Pe direito (tras): ponta girada 45 a 70 graus para fora.",
            "Calcanhar direito levantado 2 a 3 cm do chao, o tempo todo.",
            "Peso 50/50. Voce tem de conseguir levantar qualquer um dos pes sem cambalear.",
            "Joelhos flexionados 10 a 15 graus. Nunca travados.",
            "Quadril neutro: nao empine nem enfie o bumbum.",
            "Queixo para baixo, quase encostando no peito. Olhe por cima das sobrancelhas.",
            "Mao esquerda na altura da bochecha, 15 cm a frente do rosto.",
            "Mao direita colada na bochecha direita, palma virada para dentro.",
            "Cotovelos apontando para o chao, colados as costelas.",
            "Ombros levemente elevados em direcao as orelhas.",
        ],
        "giro": [
            "O unico giro da base e o do TRONCO, e ele e estatico: voce fica cerca "
            "de 30 graus de perfil, nao de frente.",
            "O ombro esquerdo aponta mais para o alvo que o direito. Isso reduz a "
            "area do seu corpo exposta.",
            "Os pes NAO giram na base parada. Eles so giram quando um golpe pede.",
        ],
        "checagem": [
            "De frente para o espelho voce deve ver mais o seu lado esquerdo que o peito.",
            "Um empurrao leve no ombro nao deve te desequilibrar.",
            "Voce consegue dar um passo em qualquer direcao sem antes reajustar os pes.",
        ],
        "erros": [
            "Pes na mesma linha: perde equilibrio lateral e cai com qualquer empurrao.",
            "Base larga demais: fica estavel mas nao consegue se mover.",
            "Queixo levantado.",
            "Cotovelos abertos, deixando costelas e figado descobertos.",
            "Calcanhar de tras plantado no chao: mata o giro do direto antes de ele comecar.",
        ],
    },
    "passos": {
        "nome": "Deslocamento",
        "resumo": "Mover o corpo inteiro sem nunca desmontar a base.",
        "inicio": [
            "Monte a base e a guarda. Elas nao mudam durante o deslocamento.",
        ],
        "execucao": [
            "Para FRENTE: o pe esquerdo (da frente) sai primeiro; o direito "
            "acompanha na mesma medida, restaurando a distancia entre os pes.",
            "Para TRAS: o pe direito sai primeiro; o esquerdo acompanha.",
            "Para a DIREITA: o pe direito sai primeiro; o esquerdo acompanha.",
            "Para a ESQUERDA: o pe esquerdo sai primeiro; o direito acompanha.",
            "Regra unica: sai primeiro o pe do lado para onde voce vai.",
            "Passos curtos, de 10 a 20 cm, deslizando com a planta rente ao chao.",
            "Os dois pes nunca estao no ar ao mesmo tempo.",
            "A base se recompoe imediatamente ao fim de cada passo — voce nunca "
            "fica com os pes juntos nem esparramados.",
        ],
        "giro": [
            "Nao ha giro no deslocamento reto. Os pes mantem os mesmos angulos "
            "que tinham na base.",
            "Se voce precisar mudar de angulo em relacao ao alvo, faca isso com "
            "passos laterais, nao girando os pes no lugar.",
        ],
        "checagem": [
            "Filme de cima ou olhe no chao: a distancia entre os pes deve ser a "
            "mesma no inicio e no fim de cada passo.",
            "A guarda nao pode subir e descer junto com os passos.",
        ],
        "erros": [
            "Cruzar os pes: e o momento em que voce esta mais vulneravel.",
            "Saltar em vez de deslizar.",
            "Passos largos que desmontam a base.",
            "Mover o pe de tras primeiro para ir a frente (ou o inverso): voce "
            "fecha a base e perde a estabilidade no meio do caminho.",
            "Deixar as maos cairem enquanto anda.",
        ],
    },
    "jab": {
        "nome": "Jab (1) — soco reto da mao da frente",
        "resumo": "O golpe mais rapido e mais curto. Serve para medir distancia, "
                  "interromper e abrir caminho — nao para nocautear.",
        "inicio": [
            "Base e guarda montadas. Mao esquerda ja na altura da bochecha.",
        ],
        "execucao": [
            "O punho esquerdo sai em linha reta a partir da altura do queixo, "
            "sem recuar um centimetro antes.",
            "O cotovelo acompanha por baixo, colado ao trajeto — nao abre para fora.",
            "Na ultima terca parte do trajeto, gire o antebraco: a palma, que "
            "estava virada para dentro, termina virada para baixo.",
            "O ombro esquerdo sobe e encosta na lateral do queixo no instante do impacto.",
            "Contato com os dois primeiros nos (indicador e medio), punho, "
            "antebraco e cotovelo na mesma linha reta.",
            "O braco estende quase por completo, mas o cotovelo NUNCA trava.",
        ],
        "giro": [
            "O QUE GIRA: o tronco, poucos graus (10 a 15), e o pe da frente junto.",
            "COMO: o pe esquerdo pivota sobre a planta, o calcanhar sai levemente "
            "para fora. O quadril acompanha de leve.",
            "QUANDO: o giro comeca junto com a saida do punho, nunca antes. "
            "Se o corpo gira primeiro, voce avisou o golpe.",
            "QUANTO: pouco, de proposito. O jab nao usa o quadril inteiro — se "
            "usar, vira um direto lento e telegrafado.",
        ],
        "retorno": [
            "A mao volta pelo MESMO caminho, mais rapido do que foi.",
            "O tronco desfaz o giro junto com a volta da mao.",
            "A mao so termina o movimento quando encosta de volta na bochecha.",
        ],
        "checagem": [
            "Filme de frente: a mao direita nao pode se mexer enquanto o jab sai.",
            "Filme de lado: o punho deve percorrer uma linha reta, nao um arco.",
            "Pare no meio do movimento: o cotovelo tem de estar apontando para "
            "baixo, nao para o lado.",
        ],
        "erros": [
            "Telegrafar: puxar a mao para tras antes de bater.",
            "Punho dobrado no impacto — e assim que se machuca o pulso.",
            "Deixar a mao direita cair enquanto o jab sai.",
            "Estender o cotovelo ate travar.",
            "Girar o corpo demais e transformar o jab num soco lento.",
        ],
    },
    "direto": {
        "nome": "Direto (2) — soco reto da mao de tras",
        "resumo": "O golpe de forca dos socos. Toda a potencia vem da rotacao do "
                  "corpo; o braco so entrega o que as pernas produziram.",
        "inicio": [
            "Base e guarda montadas, calcanhar direito ja levantado do chao.",
        ],
        "execucao": [
            "Comeca no CHAO. Antes de o braco pensar em sair, o pe direito gira.",
            "O quadril direito vai a frente e roda para dentro.",
            "O tronco acompanha a rotacao do quadril.",
            "O ombro direito e levado a frente pela rotacao do tronco.",
            "So agora o punho sai, em linha reta, a partir do queixo.",
            "A palma gira e termina virada para baixo no impacto.",
            "O ombro direito sobe e cobre o queixo no instante do contato.",
            "A mao esquerda permanece colada no rosto do inicio ao fim.",
        ],
        "giro": [
            "O QUE GIRA, na ordem: pe direito > quadril > tronco > ombro > braco. "
            "Cada elo empurra o proximo. Essa ordem e o golpe inteiro.",
            "COMO GIRA O PE: sobre a PLANTA, nao sobre o calcanhar. O calcanhar "
            "sobe e vai para fora, a ponta do pe roda para dentro, como quem "
            "esmaga um cigarro no chao.",
            "QUANTO GIRA O PE: cerca de 90 graus. Ao final, o calcanhar direito "
            "aponta para tras/fora e o joelho direito aponta para dentro.",
            "QUANTO GIRA O QUADRIL: cerca de 45 graus. O umbigo, que apontava "
            "para o lado, termina apontando para o alvo. Se o umbigo ainda "
            "aponta para o lado, voce nao girou.",
            "QUANTO GIRA O TRONCO: acompanha o quadril. O ombro direito, que "
            "estava atras, chega a linha do ombro esquerdo.",
            "QUANDO: o pe inicia o movimento. Se o braco sai primeiro, voce bate "
            "so com o braco e a forca cai para um terco.",
            "O joelho direito acompanha o giro do pe. Pe e joelho apontam sempre "
            "para a mesma direcao — e a regra que protege a articulacao.",
        ],
        "retorno": [
            "Volte DESFAZENDO o giro, nao apenas puxando o braco.",
            "O quadril roda de volta e traz o ombro e a mao junto.",
            "Termine outra vez na base, com o peso 50/50 e o calcanhar levantado.",
        ],
        "checagem": [
            "Filme de lado: o calcanhar direito tem de estar apontando para fora "
            "no momento do impacto.",
            "Pare no fim do golpe e olhe o umbigo: ele aponta para o alvo?",
            "Se voce consegue dar o direto com os pes imoveis, nao e um direto.",
        ],
        "erros": [
            "Bater so com o braco, sem girar o quadril: tira toda a potencia.",
            "Manter o calcanhar de tras plantado no chao.",
            "Inclinar o tronco a frente e passar o peso da linha do pe da frente.",
            "Girar o JOELHO em vez do pe — torce a articulacao.",
            "Esquecer a guarda esquerda no caminho de volta.",
        ],
    },
    "gancho": {
        "nome": "Gancho (3) — soco circular da mao da frente",
        "resumo": "Golpe curto e lateral. O braco nao bate: ele e carregado pela "
                  "rotacao do corpo, com a forma travada.",
        "inicio": [
            "Base e guarda montadas.",
            "Antes de girar, TRAVE a forma: cotovelo a 90 graus, na mesma altura "
            "do alvo, punho firme.",
        ],
        "execucao": [
            "Trave o angulo do cotovelo em 90 graus e mantenha assim o golpe inteiro.",
            "Levante o cotovelo ate a altura do alvo — cabeca ou costelas.",
            "Gire o corpo. O braco vai junto, sem se mover em relacao ao tronco.",
            "Punho, cotovelo e ombro permanecem na MESMA linha horizontal.",
            "A palma pode ficar virada para dentro ou para baixo. Escolha uma e "
            "mantenha — trocar no meio do aprendizado confunde o punho.",
            "Contato com os nos, punho reto e firme.",
            "A mao direita fica colada no rosto o tempo inteiro.",
        ],
        "giro": [
            "O QUE GIRA: pe da frente, quadril e tronco, todos juntos, como um "
            "bloco unico. O braco NAO participa da rotacao — ele e carga.",
            "COMO GIRA O PE: o pe esquerdo pivota sobre a planta, o calcanhar sai "
            "para fora e o joelho esquerdo aponta para dentro.",
            "QUANTO: cerca de 90 graus de rotacao no pe da frente. E mais giro do "
            "que o direto usa, porque aqui o giro E o golpe.",
            "QUANDO: nao ha 'quando'. O giro nao acompanha o golpe, o giro produz "
            "o golpe. Se voce consegue dar o gancho sem girar, virou tapa.",
            "O peso transfere do pe da frente para o de tras durante a rotacao.",
        ],
        "retorno": [
            "Desfaca a rotacao e o braco volta sozinho para a guarda.",
            "Nao 'puxe' a mao de volta — deixe o giro reverso traze-la.",
        ],
        "checagem": [
            "Filme de cima ou de frente: o angulo do cotovelo tem de ser o mesmo "
            "no inicio, no impacto e no fim.",
            "Se o cotovelo abriu durante o movimento, foi tapa, nao gancho.",
        ],
        "erros": [
            "Abrir o braco: vira tapa e machuca o ombro.",
            "Baixar o ombro do lado que bate.",
            "Bater com o punho mais alto ou mais baixo que o cotovelo.",
            "Perder completamente a guarda do outro lado.",
        ],
    },
    "jabcorpo": {
        "nome": "Jab no corpo",
        "resumo": "O mesmo jab, entregue mais embaixo. O que muda e como voce "
                  "desce, nao como voce soca.",
        "inicio": [
            "Base e guarda montadas.",
        ],
        "execucao": [
            "Desca flexionando os JOELHOS, como um agachamento curto.",
            "A coluna permanece reta e o peito continua erguido.",
            "A cabeca sai da linha central ao descer — desloque-a alguns "
            "centimetros para fora, na direcao do seu lado esquerdo.",
            "So depois de descer, dispare o jab, com a mesma mecanica de sempre.",
            "Alvo na altura do plexo solar ou do figado.",
            "A mao direita continua colada no rosto, protegendo o queixo — que "
            "agora esta mais baixo e mais perto.",
            "Suba imediatamente, estendendo os joelhos, de volta a guarda alta.",
        ],
        "giro": [
            "O QUE GIRA: o mesmo pouco giro do jab normal — tronco e pe da frente, "
            "10 a 15 graus.",
            "QUANDO: o giro acontece durante o soco, ja embaixo. Primeiro voce "
            "desce, depois voce gira e soca. Nao faca as duas coisas ao mesmo tempo "
            "enquanto estiver aprendendo.",
        ],
        "retorno": [
            "Suba pelas pernas antes de recolher totalmente a mao.",
            "Nao fique embaixo: quem fica embaixo leva joelhada.",
        ],
        "checagem": [
            "Filme de lado: as costas devem estar retas na parte mais baixa do movimento.",
            "Se voce viu o chao em algum momento, a cabeca caiu.",
        ],
        "erros": [
            "Curvar as costas em vez de dobrar os joelhos.",
            "Olhar para o chao ao descer.",
            "Descer com a cabeca na mesma linha de antes.",
            "Ficar embaixo depois do golpe.",
        ],
    },
    "saidalateral": {
        "nome": "Saida lateral",
        "resumo": "Sair do lugar onde voce acabou de bater, porque e exatamente "
                  "para la que a resposta vem.",
        "inicio": [
            "Logo apos terminar um golpe, com a guarda ainda alta.",
        ],
        "execucao": [
            "Assim que a mao voltar a guarda, de 1 ou 2 passos laterais.",
            "Use a mecanica normal de deslocamento: sai primeiro o pe do lado "
            "para onde voce vai.",
            "Prefira sair para FORA do lado do golpe mais forte do adversario. "
            "Contra um destro, sair para a sua esquerda te tira da linha do direto dele.",
            "Guarda alta durante todo o deslocamento — ela nao desce nem por um instante.",
            "Os olhos continuam no alvo enquanto os pes se movem; nao olhe para o chao.",
            "A saida acontece IMEDIATAMENTE apos o golpe, no mesmo folego. Se voce "
            "parar meio segundo antes de sair, o proposito se perdeu.",
            "Recomponha a base antes de pensar no proximo golpe.",
        ],
        "giro": [
            "O QUE GIRA: nada, de proposito. A saida lateral e deslocamento puro.",
            "Se voce precisar reencarar o alvo depois de sair, faca isso com um "
            "passo de ajuste, nao girando os pes no lugar.",
        ],
        "checagem": [
            "Filme de frente: a guarda nao pode oscilar durante os passos.",
            "Voce deve terminar em base montada, pronto para bater de novo.",
            "Marque uma linha no chao: voce saiu dela, ou so recuou em cima dela?",
            "Assista em camera lenta: existe uma pausa entre o golpe e a saida? "
            "Se existe, os dois ainda sao dois movimentos, nao um.",
        ],
        "erros": [
            "Parar para admirar o proprio golpe.",
            "Recuar em linha reta — e a trajetoria que o adversario ja esta seguindo.",
            "Sair de guarda baixa.",
            "Cruzar os pes na pressa de sair.",
        ],
    },
    "teep": {
        "nome": "Teep — chute frontal de empurrao",
        "resumo": "Nao e um chute de impacto: e um empurrao com o pe, para criar "
                  "distancia e interromper o avanco.",
        "inicio": [
            "Base e guarda montadas. As maos ficam na guarda o movimento inteiro.",
        ],
        "execucao": [
            "Levante o JOELHO primeiro, ate a altura do quadril, bem a frente do corpo.",
            "Puxe a ponta do pe para cima (dorsiflexao). O contato e com a "
            "SOLA/planta do pe, nunca com os dedos.",
            "Do joelho levantado, estenda a perna a frente enquanto empurra o "
            "quadril na mesma direcao.",
            "A forca vem da EXTENSAO DO QUADRIL, nao do chute da perna.",
            "O tronco inclina levemente para tras como contrapeso — pouco, "
            "sem perder a guarda de vista.",
            "Recolha a perna pelo mesmo caminho: primeiro dobra o joelho de "
            "volta, depois desce o pe.",
        ],
        "giro": [
            "O QUE GIRA: quase nada. O teep e o golpe com menos rotacao do repertorio.",
            "COMO: o pe de apoio pivota de 30 a 45 graus para fora, apenas o "
            "suficiente para o quadril conseguir projetar a frente.",
            "QUANDO: o pivo acontece junto com a extensao do quadril, no fim do "
            "movimento, nao no inicio.",
            "Se voce sentir necessidade de girar muito, provavelmente esta "
            "tentando chutar com forca em vez de empurrar.",
        ],
        "retorno": [
            "O pe volta para a base, no lugar de onde saiu.",
            "Nunca deixe o pe cair a frente — isso vira um passo e te deixa "
            "de base trocada, sem saber onde esta.",
        ],
        "checagem": [
            "Filme de lado: o joelho tem de subir ANTES de a perna estender.",
            "Se a perna sobe reta, e chute de futebol, nao teep.",
            "O pe volta ao mesmo ponto do chao de onde saiu.",
        ],
        "erros": [
            "Bater com os dedos do pe.",
            "Jogar a perna sem levantar o joelho primeiro.",
            "Deixar o pe cair no chao a frente.",
            "Baixar as maos para 'ajudar' no equilibrio.",
        ],
    },
    "joelho": {
        "nome": "Joelhada frontal",
        "resumo": "Golpe de curta distancia. A forca vem do quadril avancando, "
                  "nao da perna subindo.",
        "inicio": [
            "Base e guarda montadas.",
        ],
        "execucao": [
            "Levante o joelho na diagonal, de baixo para cima e a frente.",
            "Ao mesmo tempo, AVANCE o quadril na direcao do alvo. Este e o golpe.",
            "A ponta do pe aponta para baixo, perna relaxada abaixo do joelho.",
            "O contato e com a parte de cima da CANELA, logo abaixo do joelho — "
            "nunca com a rotula.",
            "Os bracos descem em oposicao, como se puxassem o alvo para baixo "
            "enquanto o joelho sobe.",
            "O tronco inclina levemente para tras, equilibrando o avanco do quadril.",
        ],
        "giro": [
            "O QUE GIRA: o pe de apoio e o quadril do lado que bate.",
            "COMO GIRA O PE: pivota de 30 a 45 graus para fora, sobre a planta.",
            "COMO GIRA O QUADRIL: o quadril do lado que bate roda para DENTRO e "
            "para CIMA, ao mesmo tempo em que avanca.",
            "QUANDO: o pivo do pe acontece junto com a subida do joelho, nao depois.",
            "QUANTO: menos que no chute baixo. Se voce girar demais, o joelho passa "
            "de lado pelo alvo em vez de entrar de frente.",
        ],
        "retorno": [
            "Recolha o joelho pelo mesmo caminho e recomponha a base.",
            "Nunca desca o pe a frente da posicao original.",
        ],
        "checagem": [
            "Filme de lado: o quadril tem de avancar visivelmente. Se so a perna "
            "subiu, e elevacao de joelho, nao joelhada.",
            "Passe a mao na regiao do contato: tem de ser canela dura, nao a rotula.",
        ],
        "erros": [
            "Bater com a rotula (patela) — dano articular direto.",
            "Nao avancar o quadril: vira levantamento de perna sem forca.",
            "Deixar a guarda cair ao descer os bracos em oposicao.",
            "Segurar as correntes ou o topo do saco com violencia (na fase com saco).",
        ],
    },
    "chutebaixo": {
        "nome": "Chute baixo (low kick)",
        "resumo": "O golpe que mais depende de rotacao e o que mais machuca quem "
                  "gira errado. O giro do pe de apoio nao e detalhe: e o golpe.",
        "inicio": [
            "Base e guarda montadas.",
            "Antes de qualquer coisa: se o giro do pe de apoio ainda nao sai "
            "automatico, volte para /como girodope e nao chute ainda.",
        ],
        "execucao": [
            "Passo curto de abertura com o pe da frente, um pouco para fora da "
            "linha do alvo. Isso abre espaco para o quadril passar.",
            "O pe de apoio comeca a girar (ver a secao de giro abaixo).",
            "O quadril direito roda e avanca — e ele que carrega a perna.",
            "A perna vem como um TACO DE BEISEBOL: joelho levemente flexionado, "
            "perna relaxada, chegando de lado. Nao e chute de futebol, com a perna "
            "estendida vindo de frente.",
            "O contato e com o terco inferior da CANELA, na coxa do alvo.",
            "O braco direito desce e vai para tras, como contrapeso que ajuda "
            "a rotacao.",
            "O tronco inclina para o lado oposto ao chute, equilibrando.",
        ],
        "giro": [
            "O QUE GIRA: o pe de APOIO (o esquerdo, que fica no chao). Este e o "
            "ponto mais importante de toda a tecnica.",
            "COMO: sobre a PLANTA do pe, com o calcanhar subindo e rodando. Nunca "
            "sobre o calcanhar apoiado.",
            "QUANTO: ate o CALCANHAR APONTAR PARA O ALVO — de 90 a 120 graus. Giro "
            "incompleto significa potencia quase zero e torcao direta no joelho.",
            "QUANDO: o giro do pe de apoio COMECA ANTES de a perna que chuta "
            "chegar ao alvo, e continua durante todo o impacto. Nao e um ajuste "
            "no fim: e o que inicia o movimento.",
            "O JOELHO DO PE DE APOIO segue o pe. Pe e joelho apontam sempre para a "
            "mesma direcao. Se o joelho girar e o pe ficar preso no chao, a torcao "
            "vai inteira para o ligamento — e assim que se rompe joelho chutando.",
            "O QUADRIL gira junto e avanca. A coxa nao levanta sozinha; ela e "
            "levada pelo quadril.",
        ],
        "retorno": [
            "Duas saidas validas: recolher pelo mesmo caminho, ou completar o giro "
            "e voltar a base do outro lado.",
            "O que nao pode e deixar a perna morta no ar ou ficar de costas para o alvo.",
        ],
        "checagem": [
            "Filme de tras: o calcanhar do pe de apoio esta apontando para o alvo "
            "no momento do impacto? Se nao, o giro foi incompleto.",
            "Filme de lado: a perna chegou de lado (taco) ou de frente (futebol)?",
            "Passe a mao na canela: o contato tem de ser osso, nao o peito do pe.",
        ],
        "erros": [
            "Nao girar o pe de apoio: principal causa de lesao de joelho em iniciante.",
            "Girar o joelho com o pe preso no chao.",
            "Bater com o peito do pe em vez da canela.",
            "Chutar com a perna estendida, como chute de futebol.",
            "Olhar para baixo durante o chute.",
            "Ficar de costas para o alvo depois do movimento.",
        ],
    },
    "girodope": {
        "nome": "Giro do pe de apoio (drill isolado)",
        "resumo": "O exercicio mais importante da fase de fundamentos. Sem este "
                  "giro automatico, nenhum chute e seguro.",
        "inicio": [
            "Base e guarda montadas, de frente para o espelho ou para um ponto "
            "escolhido como alvo imaginario.",
        ],
        "execucao": [
            "Sem chutar, sem mover a outra perna: levante o calcanhar esquerdo "
            "do chao, apoiando so a planta.",
            "Gire o pe sobre a planta, levando o calcanhar em direcao ao alvo.",
            "Continue ate o calcanhar apontar para o alvo — 90 a 120 graus.",
            "Deixe o joelho esquerdo acompanhar o giro, sempre apontando para a "
            "mesma direcao que o pe.",
            "O quadril acompanha naturalmente; nao segure o tronco de frente.",
            "Volte devagar a posicao inicial e repita.",
            "Depois de dominar parado, repita levantando o joelho direito junto, "
            "mas ainda sem chutar.",
        ],
        "giro": [
            "O QUE GIRA: o pe de apoio, sobre a planta.",
            "O QUE NAO GIRA: o joelho por conta propria. Ele apenas segue o pe.",
            "COMO SABER QUE ESTA CERTO: coloque a mao no joelho enquanto gira. Ele "
            "deve girar junto com o pe, sem torcao entre os dois.",
            "QUANTO: ate o calcanhar apontar para o alvo. Se o calcanhar continua "
            "apontando para o lado, faltou giro.",
        ],
        "checagem": [
            "Filme de tras: onde o calcanhar termina apontando?",
            "Faca 10 giros com os olhos fechados. Se o equilibrio se perde, ainda "
            "nao esta pronto para chutar.",
            "So passe ao chute baixo quando o giro sair sem voce pensar nele.",
        ],
        "erros": [
            "Girar o joelho em vez do pe — e exatamente o movimento que lesiona.",
            "Girar com o calcanhar apoiado no chao.",
            "Parar o giro no meio, com o calcanhar apontando de lado.",
            "Apressar a progressao e comecar a chutar antes de o giro estar automatico.",
        ],
    },
    "bloqueio": {
        "nome": "Bloqueio e resposta",
        "resumo": "Absorver o golpe com estrutura, sem afastar a guarda do rosto, "
                  "e devolver imediatamente.",
        "inicio": [
            "Base e guarda montadas.",
        ],
        "execucao": [
            "CONTRA SOCO ALTO:",
            "O cotovelo sobe e a mao encosta na tempora, do lado que vem o golpe.",
            "O antebraco fica vertical, colado a lateral da cabeca.",
            "Voce continua olhando por cima ou por dentro da guarda — nunca fecha os olhos.",
            "O ombro do mesmo lado sobe para fechar o vao ate o queixo.",
            "CONTRA CHUTE BAIXO:",
            "Levante a canela do lado atacado, joelho apontando ligeiramente para fora.",
            "O pe fica flexionado e a perna firme, nao relaxada.",
            "Voce recebe o chute na canela, nunca na coxa nem no lado de dentro da perna.",
            "RESPOSTA:",
            "Assim que o golpe passar, devolva um jab. Bloqueio sem resposta e "
            "so apanhar de forma organizada.",
        ],
        "giro": [
            "O QUE GIRA: quase nada no bloqueio alto — apenas alguns graus de "
            "tronco, na direcao do golpe, para dissipar a forca.",
            "NO BLOQUEIO DE PERNA: o pe de apoio pivota de leve para fora, para "
            "voce nao ser desequilibrado pelo impacto.",
            "QUANDO: o giro acontece no momento do contato, absorvendo. Girar "
            "antes abre a guarda.",
        ],
        "retorno": [
            "A estrutura volta a guarda normal imediatamente apos o contato.",
            "A perna que bloqueou desce para a base, nunca a frente dela.",
        ],
        "checagem": [
            "Filme de frente: a mao nao pode se afastar do rosto para 'ir buscar' o golpe.",
            "No bloqueio de perna, o joelho tem de estar apontando para fora, "
            "protegendo o lado de dentro da coxa.",
        ],
        "erros": [
            "Fechar os olhos.",
            "Afastar a mao do rosto.",
            "Receber com o antebraco mole, sem estrutura.",
            "Bloquear e ficar parado, sem devolver.",
        ],
    },
    "sombra": {
        "nome": "Boxe-sombra",
        "resumo": "Treinar o movimento no ar, com atencao total a forma. E a base "
                  "de toda a fase de fundamentos.",
        "inicio": [
            "Espaco livre, de frente para um espelho ou com o celular filmando.",
            "Sem luva e sem bandagem: voce precisa ver as maos.",
        ],
        "execucao": [
            "Comece so com base e deslocamento, sem golpe nenhum.",
            "Adicione um unico golpe e repita ate ele sair limpo.",
            "Escolha UM ponto de atencao por rodada: hoje o punho, amanha o "
            "queixo, depois o pe de apoio. Corrigir tudo ao mesmo tempo nao funciona.",
            "Trabalhe em tres velocidades, nesta ordem: muito lento, medio, "
            "e so entao normal. Nunca comece rapido.",
            "Toda mao que sai volta a guarda antes de a proxima sair.",
        ],
        "giro": [
            "Os giros sao os mesmos de cada golpe. A vantagem da sombra e que, sem "
            "impacto, voce consegue PARAR no meio do giro e conferir a posicao.",
            "Use isso: dispare o direto, congele no meio e olhe onde esta o calcanhar.",
        ],
        "checagem": [
            "Filme de frente e de lado. As duas vistas revelam coisas diferentes: "
            "de frente aparece guarda caida, de lado aparece punho dobrado e "
            "desequilibrio.",
            "Assista em camera lenta. Erros de forma somem em velocidade normal.",
        ],
        "erros": [
            "Acelerar antes de a forma estar limpa.",
            "Bater no ar travando o cotovelo.",
            "Tentar corrigir cinco coisas na mesma rodada.",
            "Fazer sombra sem se ver: sem espelho nem camera, voce so repete o "
            "que ja faz errado.",
        ],
    },
    "prancha": {
        "nome": "Prancha",
        "resumo": "Sustentacao do tronco. Serve para o quadril conseguir "
                  "transferir forca sem a coluna ceder no meio do caminho.",
        "inicio": [
            "De bruços, antebracos no chao, cotovelos exatamente sob os ombros.",
            "Pes na largura do quadril, apoiados nas pontas.",
        ],
        "execucao": [
            "Suba o corpo apoiado em antebracos e pontas dos pes.",
            "Alinhe calcanhar, quadril, ombro e cabeca numa unica linha reta.",
            "Contraia o gluteo com forca — e ele que impede o quadril de cair.",
            "Contraia o abdomen como se fosse levar um soco na barriga.",
            "Olhe para o chao, um palmo a frente das maos, mantendo o pescoco neutro.",
            "Empurre o chao com os antebracos, afastando as escapulas — nao deixe "
            "o peito afundar entre os ombros.",
            "Respire normalmente durante todo o tempo.",
            "Para descer, apoie os joelhos primeiro; nao desabe de uma vez.",
        ],
        "checagem": [
            "Filme de lado: uma linha reta deve passar por calcanhar, quadril e ombro.",
            "Se voce consegue conversar, a respiracao esta certa.",
            "Se a lombar comeca a doer, o quadril caiu — encerre a serie.",
        ],
        "erros": [
            "Quadril subindo, virando um triangulo.",
            "Lombar afundando.",
            "Prender a respiracao.",
            "Levantar a cabeca e olhar para frente.",
        ],
    },
    "bandagem": {
        "nome": "Bandagem de 5 m",
        "resumo": "Protecao do punho e dos nos. So necessaria quando existe "
                  "impacto — nao se usa na fase de fundamentos.",
        "inicio": [
            "Mao aberta, dedos separados, polegar afastado.",
            "Bandagem enrolada, com a alca livre.",
        ],
        "execucao": [
            "Polegar na alca, com a bandagem passando pelo DORSO da mao.",
            "3 voltas no punho.",
            "3 voltas na palma, subindo em direcao aos dedos.",
            "Entre os dedos, nesta ordem: mindinho/anelar, anelar/medio, "
            "medio/indicador. Cada passagem sobe pelo dorso e volta pela palma.",
            "Volte ao punho e cruze pelo dorso em X, 2 ou 3 vezes.",
            "3 voltas cobrindo os nos dos dedos.",
            "Termine no punho e feche o velcro.",
        ],
        "checagem": [
            "Feche o punho: deve ficar firme, sem formigar.",
            "Abra e feche a mao 10 vezes. Se a mao esfriar, perder cor ou "
            "formigar, esta apertada demais — refaca.",
            "O punho nao pode dobrar para tras com facilidade.",
        ],
        "erros": [
            "Apertada demais: corta a circulacao.",
            "Frouxa no punho: nao protege exatamente onde a lesao acontece.",
            "Pular a passagem entre os dedos, deixando os nos sem colchao.",
        ],
    },
    "mobilidade": {
        "nome": "Mobilidade de aquecimento",
        "resumo": "Preparar as articulacoes que vao girar. Movimento, nao "
                  "alongamento parado.",
        "inicio": [
            "Em pe, espaco livre ao redor, pes na largura do quadril.",
            "Sem pressa: mobilidade feita rapido nao chega ao fim da amplitude "
            "e por isso nao prepara nada.",
        ],
        "execucao": [
            "OMBROS:",
            "10 circulos grandes para tras, levando o braco o mais longe que "
            "conseguir sem forcar. Depois 10 para frente.",
            "10 aberturas: bracos a frente, abre ate sentir o peito esticar, fecha.",
            "QUADRIL:",
            "Joelho elevado a frente, 10 circulos por lado: abre para fora, "
            "desce, fecha para dentro.",
            "10 balancos da perna para frente e para tras, solta, apoiando-se "
            "na parede se precisar.",
            "TORNOZELO:",
            "10 circulos em cada sentido, com a ponta do pe apoiada no chao.",
            "Agachamento profundo mantido por 20 s, com os calcanhares no chao. "
            "Se o calcanhar subir, apoie-se em algo e desca ate onde der.",
            "COLUNA TORACICA:",
            "Maos na nuca, 10 rotacoes de tronco para cada lado, mantendo o "
            "quadril parado de frente.",
            "PUNHOS:",
            "10 circulos em cada sentido com a mao fechada, para o punho chegar "
            "aquecido no primeiro soco.",
        ],
        "giro": [
            "Esta e a preparacao especifica dos giros que voce vai usar depois: "
            "quadril e tornozelo sao as duas articulacoes que giram no chute baixo.",
            "Se o tornozelo estiver rigido, o pe de apoio nao gira o suficiente.",
        ],
        "checagem": [
            "No agachamento profundo, os calcanhares ficam no chao? Se nao, o "
            "tornozelo esta rigido e o chute baixo vai sofrer.",
            "Na rotacao de tronco, o quadril continuou de frente? Se ele girou "
            "junto, voce nao mobilizou a coluna, so girou o corpo inteiro.",
            "Ao terminar, voce deve estar levemente aquecido e sem falta de ar.",
        ],
        "erros": [
            "Alongamento estatico longo antes do treino: reduz forca e nao previne lesao.",
            "Fazer rapido demais, sem chegar ao fim da amplitude.",
            "Pular a mobilidade de tornozelo — e a que mais afeta o chute.",
        ],
    },
    "elevacaojoelhos": {
        "nome": "Elevacao alternada dos joelhos",
        "resumo": "O padrao motor da joelhada, sem impacto e sem alvo.",
        "inicio": [
            "Em pe, guarda alta, como se fosse bater.",
        ],
        "execucao": [
            "Levante o joelho direito ate a altura do quadril, na diagonal e a frente.",
            "No topo, ESTENDA o quadril a frente, como faria na joelhada. Este e "
            "o ponto do exercicio; sem isso e so levantar a perna.",
            "Segure meio segundo no topo, sentindo o gluteo do lado que sustenta.",
            "Desca controlado, sem deixar o pe bater no chao.",
            "Repita do outro lado, alternando.",
            "Ritmo controlado: nao e corrida no lugar.",
            "Abdomen contraido e tronco vertical do inicio ao fim.",
            "Maos na guarda, como se estivesse pronto para bater.",
        ],
        "giro": [
            "Sem giro nesta versao. O objetivo aqui e isolar a EXTENSAO do quadril, "
            "que e a parte que a maioria esquece na joelhada.",
            "O pivo do pe so entra depois, em /como joelho.",
        ],
        "checagem": [
            "Filme de lado: o quadril avanca no topo do movimento? Se o tronco "
            "so balanca e o quadril fica parado, voce nao esta treinando a joelhada.",
            "O joelho chega a altura do quadril ou para antes?",
            "O tronco continuou vertical, ou voce se inclinou para tras para "
            "'ajudar' a perna a subir?",
            "Voce consegue manter a guarda alta durante as 20 repeticoes?",
        ],
        "erros": [
            "Correr no lugar sem realmente levantar o joelho.",
            "Inclinar o tronco para tras para 'ajudar' a perna a subir.",
            "Joelho parando abaixo da linha do quadril.",
            "Deixar a guarda cair.",
        ],
    },
    "corda": {
        "nome": "Pular corda",
        "resumo": "Condicionamento e ritmo. Nao faz parte da fase de fundamentos "
                  "(e equipamento); entra junto com o saco.",
        "inicio": [
            "Altura certa: pisando no meio da corda, as alcas chegam a axila.",
            "Cotovelos proximos ao corpo, maos na altura do quadril.",
        ],
        "execucao": [
            "Comece sem a corda: 30 s saltando no lugar, baixo, so para achar o ritmo.",
            "Pegue a corda com as maos na altura do quadril, um palmo afastadas do corpo.",
            "Saltos baixos, de 2 a 3 cm do chao. O objetivo e ritmo, nao altura.",
            "Aterrisse na ponta dos pes, com o joelho levemente flexionado para absorver.",
            "Os pes saem e voltam juntos, sem alternar, enquanto voce aprende.",
            "O giro da corda vem do PUNHO, nao do ombro nem do cotovelo.",
            "Mantenha o tronco ereto e o olhar a frente, nao na corda.",
            "Se errar, recomece sem parar o ritmo do corpo — a pausa longa e o "
            "que quebra o condicionamento.",
            "Comece com blocos de 30 s e va aumentando conforme a panturrilha aguentar.",
        ],
        "giro": [
            "O QUE GIRA: apenas os punhos, em circulos pequenos.",
            "Se o braco inteiro esta girando, voce vai cansar o ombro antes das pernas.",
        ],
        "checagem": [
            "OUCA: deve haver UM som por salto. Dois sons seguidos significam que "
            "voce esta dando um salto extra entre as passagens da corda.",
            "Os calcanhares nao devem encostar no chao em nenhum salto.",
            "Se a panturrilha queimar antes de 1 min, os saltos estao altos demais.",
            "Filme de frente: os cotovelos devem ficar praticamente parados.",
        ],
        "erros": [
            "Saltos altos: sobrecarrega panturrilha e tendao de aquiles, a lesao "
            "mais comum de quem volta a pular corda.",
            "Aterrissar de calcanhar.",
            "Girar com o ombro e o braco inteiro.",
        ],
    },
    "controlarsaco": {
        "nome": "Controlar o saco",
        "resumo": "Manter distancia e ritmo enquanto o saco balanca. Nao existe "
                  "na fase de fundamentos, so no ciclo com saco.",
        "inicio": [
            "Base montada, a uma distancia em que o jab estendido alcance o saco.",
        ],
        "execucao": [
            "Acompanhe o saco com passos curtos, sem sair da base nem cruzar os pes.",
            "Leia o balanco: o saco tem um ponto mais proximo e um mais distante. "
            "Voce trabalha quando ele esta indo embora, nao quando esta vindo.",
            "Espere o saco passar o ponto mais proximo antes de voltar a bater.",
            "Use jabs leves para amortecer e reposicionar o saco em vez de segura-lo.",
            "Se precisar realmente para-lo, use a palma aberta na LATERAL do saco, "
            "acompanhando o movimento dele por um instante antes de frear.",
            "Mantenha a guarda alta enquanto controla — e exatamente o momento em "
            "que todo mundo relaxa a mao.",
            "Continue respirando no ritmo do round; controlar nao e descansar.",
        ],
        "giro": [
            "Sem giro proprio. Voce usa o deslocamento normal, mantendo os angulos "
            "dos pes da base.",
            "Se precisar mudar de angulo em relacao ao saco, faca com passos "
            "laterais, circulando, nao girando os pes no lugar.",
        ],
        "checagem": [
            "Filme de lado: voce esta batendo no saco quando ele volta? Isso e o "
            "erro que mais machuca punho de iniciante.",
            "Ao fim do round de controle, seus pes devem estar em base montada, "
            "nao esparramados.",
            "Se voce precisou agarrar a corrente alguma vez, o balanco esta maior "
            "do que voce consegue controlar — bata mais leve.",
        ],
        "erros": [
            "Agarrar o topo do saco ou a corrente com violencia — quem paga e o ombro.",
            "Bater de frente no saco enquanto ele volta em sua direcao.",
            "Parar de se mover e ficar so esperando o saco.",
        ],
    },
    "respiracao": {
        "nome": "Respiracao",
        "resumo": "Controlar o folego durante o esforco e baixar a frequencia no fim.",
        "inicio": [
            "Em pe com as maos no quadril, ou sentado.",
        ],
        "execucao": [
            "DURANTE O TREINO:",
            "Expire curto e forte a cada golpe, pela boca, contraindo o abdomen.",
            "Inspire pelo nariz entre os golpes.",
            "Nunca prenda o ar.",
            "NA VOLTA A CALMA:",
            "Inspire pelo nariz contando 4 segundos.",
            "Segure 2 segundos.",
            "Expire pela boca contando 6 segundos.",
            "Repita de 8 a 10 ciclos.",
        ],
        "checagem": [
            "Se voce nao consegue falar uma frase inteira entre os rounds, "
            "a intensidade esta acima do planejado.",
            "Ao fim da volta a calma, a respiracao deve estar quase normal.",
        ],
        "erros": [
            "Prender a respiracao durante o esforco: principal causa de cansaco precoce.",
            "Respirar so pela boca, ofegando, entre os rounds.",
            "Pular a volta a calma.",
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
            "Base, guarda e passos para frente e para tras",
            "Jab parado",
            "Direto parado",
            "Jab + direto",
            "Jab + direto saindo lateralmente",
        ], nota=f"5 blocos de 2 min, 1 min de descanso entre eles.\n{NUMERACAO}",
           tecnicas=("base", "passos", "jab", "direto", "saidalateral")),
        _bloco("Saco", None, [
            "Apenas jab",
            "Jab + direto",
            "Jab + direto + saida lateral",
            "Jab no corpo + direto na cabeca",
            "Jab + direto + gancho",
            "Golpes leves circulando o saco",
            "Combinacoes livres de 2 ou 3 socos",
            "Condicionamento: 20 s trabalhando / 20 s controlando",
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
            "Guarda e deslocamento",
            "Bloqueio imaginario e resposta com jab",
            "Teep sem forca, primeiro no ar",
            "Joelho frontal alternado no ar",
            "Jab + direto + joelho",
        ], nota="5 blocos de 2 min, 1 min de descanso.",
           tecnicas=("base", "passos", "bloqueio", "teep", "joelho")),
        _bloco("Saco", None, [
            "Jab + saida",
            "Jab + direto + saida",
            "Teep alternado, devagar",
            "Jab + teep",
            "Direto + joelho de tras",
            "Jab + direto + joelho de tras",
            "Joelho alternado, controlando o saco",
            "Tecnica livre leve",
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
            "Giro do pe de apoio, sem chutar",
            "Chute baixo com a perna de tras, no ar",
            "Chute baixo com a perna da frente, no ar",
            "Jab + direto + chute baixo",
        ], nota="4 blocos de 2 min, 1 min de descanso.",
           tecnicas=("girodope", "chutebaixo", "jab", "direto")),
        _bloco("Saco", None, [
            "Jab + direto",
            "Chute baixo da perna de tras",
            "Jab + chute baixo",
            "Jab + direto + chute baixo",
            "Direto + chute baixo",
            "Jab + direto + joelho",
            "Combinacoes livres",
            "Condicionamento: 20 s de golpes / 20 s movimentando",
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

# Os blocos de aprendizado continuam de mao nua: sem impacto nao ha o que
# proteger, e a mao livre deixa o punho visivel para correcao. A protecao entra
# so no bloco final, onde existe contato.
SEM_LUVA = ("Este bloco e de mao nua, sem bandagem nem luva — voce precisa "
            "enxergar o punho para corrigir. O saco so entra no bloco final.")

# Teto de potencia da fase. O saco aqui e instrumento de conferencia, nao alvo:
# a 20-30% voce sente onde o golpe encosta sem que um erro de alinhamento vire
# lesao de punho.
POTENCIA_FUNDAMENTOS = "20-30%"

NO_SACO = ("Bandagem e luva obrigatorias neste bloco. Potencia maxima "
           f"{POTENCIA_FUNDAMENTOS} — o saco aqui serve para conferir distancia, "
           "alinhamento e ponto de contato, nao para treinar forca.")

FUNDAMENTOS_A = {
    "nome": "Fundamentos A — postura, guarda e socos retos",
    "intensidade": "leve (aprendizado, sem impacto)",
    "usa_progressao": False,
    "blocos": [
        _bloco("Preparacao", "6 min", [
            "3 min de mobilidade de ombros, quadril e tornozelos",
            "2 min de caminhada leve pela sala",
            "1 min so respirando, decidindo em que voce vai prestar atencao hoje",
        ], nota=SEM_LUVA,
           tecnicas=("mobilidade", "respiracao")),
        _bloco("Base e guarda", "10 min", [
            "Monte a base do zero 20 vezes: comece com os pes juntos, recue o "
            "pe direito, ajuste os angulos dos dois pes e levante a guarda",
            "Desmanche completamente entre uma repeticao e outra — o objetivo e "
            "treinar a montagem, nao ficar parado na posicao",
            "Segure a guarda por 3 x 30 s de frente para o espelho, 30 s de descanso",
            "1 min andando pela sala sem desmanchar a guarda",
        ], nota="Confira a cada repeticao: queixo baixo, cotovelos para dentro, "
                "joelhos moles, calcanhar de tras levantado.",
           tecnicas=("base", "sombra")),
        _bloco("Deslocamento", "7 min", [
            "Frente e tras: 20 idas e voltas (1 ida + 1 volta = 1 repeticao)",
            "Direita e esquerda: 20 para cada lado",
            "Quadrado: imagine um quadrado de 1 m no chao e percorra os quatro "
            "lados sem nunca virar o corpo — 10 voltas em cada sentido",
            "Descanse 30 s entre os tres exercicios",
        ], nota="Regra unica desta fase: os pes nunca se cruzam. Se cruzarem, "
                "pare, remonte a base e recomece a serie.",
           tecnicas=("passos",)),
        _bloco("Jab isolado", "8 min", [
            "30 jabs LENTOS de frente para o espelho, um a cada 3 s, contando "
            "o trajeto de ida e de volta",
            "Descanse 1 min",
            "30 jabs em ritmo medio, ainda sem forca",
            "Descanse 1 min",
            "20 jabs dando um passo a frente junto: o pe esquerdo sai primeiro e "
            "o punho parte no mesmo instante",
        ], nota=f"Pare a cada 10 e confira: punho reto, mao voltou ao rosto. {SEM_COMBO}",
           tecnicas=("jab",)),
        _bloco("Direto isolado", "8 min", [
            "20 giros de pe direito e quadril com as MAOS NA GUARDA, sem soltar "
            "o braco — so o giro, para sentir de onde vem a forca",
            "30 diretos lentos, respeitando a ordem pe > quadril > tronco > braco",
            "Descanse 1 min",
            "30 diretos em ritmo medio",
            "10 diretos filmados de lado, para conferir o calcanhar direito",
        ], nota=f"O giro vem primeiro; o braco e o ultimo elo. {SEM_COMBO}",
           tecnicas=("direto",)),
        _bloco("Saco leve", "8 min", [
            "Enfaixe as maos e coloque as luvas antes de encostar no saco",
            "DISTANCIA: estenda o jab ate os nos tocarem o saco de leve. Ajuste "
            "os pes ate essa distancia sair certa. Entre e saia 10 vezes",
            "20 jabs a 20%, so para sentir onde o punho encosta",
            "Pare e confira o punho: doeu, dobrou, ou entrou reto?",
            "20 diretos a 20%, conferindo se o calcanhar de tras girou",
            "10 jabs e 10 diretos alternados, ainda um de cada vez",
            "Espere o saco parar entre as series. Nunca bata nele voltando",
        ], nota=f"{NO_SACO} Dor no punho ou nos nos = pare o bloco. "
                f"{SEM_COMBO}",
           tecnicas=("bandagem", "jab", "direto", "controlarsaco")),
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
        ], nota=f"Jab e direto aqui sao revisao, ainda um de cada vez. {SEM_LUVA}",
           tecnicas=("mobilidade", "base", "jab", "direto")),
        _bloco("Gancho isolado", "9 min", [
            "20 rotacoes de tronco com os bracos soltos e pendurados, sem golpe, "
            "so para sentir o pe da frente girando",
            "30 ganchos lentos com o cotovelo travado a 90 graus: 15 na altura da "
            "cabeca e 15 na altura das costelas",
            "Descanse 1 min",
            "30 ganchos em ritmo medio",
        ], nota=f"No espelho: punho, cotovelo e ombro na mesma linha horizontal. {SEM_COMBO}",
           tecnicas=("gancho",)),
        _bloco("Jab no corpo", "8 min", [
            "20 descidas sem golpe: flexione os JOELHOS, coluna reta, e volte",
            "30 jabs no corpo lentos: desce, soca, sobe — tres tempos separados",
            "Descanse 1 min",
            "20 em ritmo medio, agora com os tres tempos emendados",
        ], nota=f"A cabeca sai da linha central ao descer. {SEM_COMBO}",
           tecnicas=("jabcorpo",)),
        _bloco("Bloqueio e saida lateral", "9 min", [
            "Bloqueio alto: 30 repeticoes de cada lado, subindo o cotovelo sem "
            "afastar a mao do rosto",
            "Bloqueio de perna: 20 elevacoes de canela de cada lado, joelho "
            "apontando um pouco para fora",
            "Saida lateral: 20 para cada lado — um unico jab, e imediatamente "
            "dois passos para o lado",
        ], nota="Nunca recue em linha reta. O jab antes da saida existe so para "
                "dar o timing — continua sendo um golpe so.",
           tecnicas=("bloqueio", "saidalateral")),
        _bloco("Saco leve", "8 min", [
            "Enfaixe as maos e coloque as luvas",
            "DISTANCIA DO GANCHO: e mais curta que a do jab. Encoste o cotovelo "
            "dobrado no saco para achar o ponto certo, depois recue meio passo",
            "20 ganchos a 20%, 10 de cada lado, conferindo se o cotovelo manteve "
            "os 90 graus no impacto",
            "20 jabs no corpo a 20%, descendo pelos joelhos",
            "10 saidas laterais: um unico jab e dois passos para o lado",
            "Espere o saco parar entre as series",
        ], nota=f"{NO_SACO} No gancho, o saco denuncia na hora se o braco abriu: "
                f"o golpe escorrega em vez de entrar. {SEM_COMBO}",
           tecnicas=("bandagem", "gancho", "jabcorpo", "saidalateral", "controlarsaco")),
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
        ], nota=SEM_LUVA,
           tecnicas=("mobilidade", "elevacaojoelhos")),
        _bloco("Giro do pe de apoio", "8 min", [
            "30 giros lentos com a perna esquerda de apoio, SEM chutar, ate o "
            "calcanhar apontar para o alvo imaginario",
            "30 giros lentos com a perna direita de apoio",
            "Descanse 1 min",
            "20 giros por lado em ritmo medio",
            "10 giros por lado com o joelho da outra perna levantado, ainda sem chutar",
        ], nota="Quem gira e o PE, nao o joelho. So passe para o chute quando o "
                "giro sair sem voce pensar — e a diferenca entre chutar e lesionar.",
           tecnicas=("girodope",)),
        _bloco("Teep isolado", "9 min", [
            "20 elevacoes de joelho ate a altura do quadril, sem estender a perna",
            "30 teeps lentos por perna: sobe o joelho, estende empurrando, "
            "recolhe o joelho, desce o pe — quatro tempos",
            "Descanse 1 min",
            "20 por perna em ritmo medio, com os quatro tempos emendados",
        ], nota=f"Recolha o pe de volta a base; nunca deixe cair a frente. {SEM_COMBO}",
           tecnicas=("teep",)),
        _bloco("Joelhada isolada", "8 min", [
            "20 elevacoes diagonais de joelho, ainda SEM avancar o quadril",
            "30 joelhadas lentas por perna, agora avancando o quadril no topo — "
            "a diferenca entre as duas coisas e o golpe inteiro",
            "Descanse 1 min",
            "20 por perna em ritmo medio",
        ], nota=f"O contato seria ACIMA da rotula, nunca nela. {SEM_COMBO}",
           tecnicas=("joelho",)),
        _bloco("Chute baixo isolado", "9 min", [
            "20 chutes baixos LENTOS por perna, no ar, com atencao unica no giro "
            "do pe de apoio — ignore a perna que chuta por enquanto",
            "Descanse 1 min",
            "20 por perna em ritmo medio",
            "10 por perna filmados de TRAS, que e a unica vista onde da para ver "
            "se o calcanhar de apoio girou o suficiente",
        ], nota=f"Sem forca e sem alvo: o objetivo e a trajetoria, nao o impacto. {SEM_COMBO}",
           tecnicas=("chutebaixo", "girodope")),
        _bloco("Saco leve", "8 min", [
            "PORTAO: so faca este bloco se o giro do pe de apoio ja sair sem "
            "voce pensar. Se ainda nao sai, repita o bloco 2 e encerre a sessao",
            "Enfaixe as maos e coloque as luvas",
            "10 teeps por perna a 20%: empurrar o saco, nao bater nele",
            "10 joelhadas por perna a 20%, avancando o quadril",
            "5 chutes baixos por perna a 20%, contato com a CANELA",
            "Espere o saco parar entre as series",
        ], nota="Cinco chutes por perna e pouco de proposito: a canela precisa de "
                "meses de exposicao gradual. Dor na canela ou no peito do pe "
                "encerra o bloco na hora — insistir vira periostite, que tira "
                "voce de treino por semanas. "
                f"{NO_SACO}",
           tecnicas=("girodope", "teep", "joelho", "chutebaixo", "bandagem", "controlarsaco")),
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
    "No saco leve, o punho entra reto e nao doi no dia seguinte.",
    "Voce acerta a distancia de primeira, sem precisar ajustar depois do golpe.",
    "Nenhum movimento causa dor em punho, ombro, joelho ou tornozelo.",
]

# Conferencia antes de encostar no saco. Vira parte do indice da fase, porque
# e o unico ponto onde equipamento mal montado ainda da para pegar sem custo.
ANTES_DE_BATER = [
    "Inspecione suporte, parabolts, corrente e mosquetao. Balance o saco com "
    "forca e observe: nada pode ceder, ranger ou folgar.",
    "Bandagem de 5 m nas duas maos — passo a passo em /como bandagem.",
    "Luvas de 16 oz por cima da bandagem.",
    "Espaco livre em volta para voce circular sem esbarrar em nada.",
    "Celular posicionado para filmar: o saco esconde o erro que o espelho "
    "mostrava, porque agora voce olha para o alvo, nao para si.",
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
                 if progride else f"bloco {idx + 1} de {total} · um movimento por vez")

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
        linhas.append("<i>aprendizado no espelho + saco leve — um movimento por vez</i>")
    linhas.append("")

    for i, bloco in enumerate(roteiro["blocos"], 1):
        duracao = bloco["duracao"] or f"{rounds} de {duracao_round}"
        linhas.append(f"{i}. <b>{bloco['titulo']}</b> — {duracao}")
    linhas += ["", "Envie /proximo para comecar bloco a bloco."]
    return "\n".join(linhas)


def formatar_regras():
    return "<b>Regras do ciclo</b>\n\n" + "\n".join(f"• {r}" for r in REGRAS)


# Ordem de exibicao das secoes de uma tecnica. `giro`, `retorno` e `checagem`
# sao opcionais -- nem todo movimento gira (prancha, respiracao) e nem todo um
# tem retorno proprio.
SECOES_TECNICA = [
    ("inicio", "Posicao inicial"),
    ("execucao", "Execucao"),
    ("giro", "O que gira, quanto e quando"),
    ("retorno", "Retorno"),
    ("checagem", "Como saber que esta certo"),
    ("erros", "Erros comuns"),
]

# Limite de uma mensagem do Telegram. As tecnicas detalhadas passam disso, entao
# a mensagem e dividida em partes em vez de a instrucao ser encurtada.
LIMITE_TELEGRAM = 4096


def dividir_mensagem(texto, limite=LIMITE_TELEGRAM):
    """Divide em partes que cabem no Telegram, quebrando em linha em branco e,
    se um bloco unico ainda nao couber, em quebra de linha."""
    if len(texto) <= limite:
        return [texto]
    partes, atual = [], ""
    for bloco in texto.split("\n\n"):
        candidato = f"{atual}\n\n{bloco}" if atual else bloco
        if len(candidato) <= limite:
            atual = candidato
            continue
        if atual:
            partes.append(atual)
            atual = ""
        while len(bloco) > limite:
            corte = bloco.rfind("\n", 0, limite)
            if corte <= 0:
                corte = limite
            partes.append(bloco[:corte])
            bloco = bloco[corte:].lstrip("\n")
        atual = bloco
    if atual:
        partes.append(atual)
    return partes


def formatar_tecnica(chave):
    """Passo a passo detalhado. `chave` ja resolvida por buscar_tecnica."""
    tec = TECNICAS[chave]
    linhas = [f"<b>{tec['nome']}</b>"]
    if tec.get("resumo"):
        linhas.append(f"<i>{tec['resumo']}</i>")

    for campo, titulo in SECOES_TECNICA:
        itens = tec.get(campo)
        if not itens:
            continue
        linhas += ["", f"<b>{titulo}</b>"]
        if campo == "execucao":
            # A ordem importa na execucao, entao ela vai numerada. Item terminado
            # em ':' e sub-cabecalho (ex.: "CONTRA SOCO ALTO:") e nao consome
            # numero -- numerar cabecalho embaralharia a contagem dos passos.
            numero = 0
            for item in itens:
                if item.endswith(":"):
                    linhas.append(f"<b>{item}</b>")
                    numero = 0
                    continue
                numero += 1
                linhas.append(f"{numero}. {item}")
        else:
            linhas += [f"\u2022 {item}" for item in itens]

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
        "<b>Fase de fundamentos — com saco leve</b>",
        "",
        "Aprender cada movimento isolado antes de bater. Bater no saco antes de "
        "o padrao estar formado grava o padrao errado com impacto junto, e chute "
        "baixo sem giro do pe de apoio machuca o joelho logo na primeira sessao.",
        "",
        "Cada sessao tem duas partes. Os blocos de aprendizado sao de mao nua, "
        "de frente para o espelho: sem impacto voce enxerga o punho e corrige. "
        f"O bloco final e no saco, com bandagem e luva, a no maximo "
        f"{POTENCIA_FUNDAMENTOS} — ali o saco responde o que o espelho nao "
        "responde: distancia, alinhamento e ponto de contato.",
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
        "<b>Quando passar para o ciclo de 8 semanas (/mt)</b>",
    ]
    linhas += [f"• {c}" for c in CRITERIO_DE_PASSAGEM]
    linhas += ["", "<b>Antes de encostar no saco</b>"]
    linhas += [f"• {e}" for e in ANTES_DE_BATER]
    linhas += ["", "<i>Nao ha pressa aqui. Uma semana a mais de fundamento custa "
                   "uma semana; um padrao errado gravado custa meses para desfazer.</i>"]
    return "\n".join(linhas)


def formatar_indice_tecnicas():
    linhas = ["<b>Biblioteca de execucao</b>", ""]
    for chave in sorted(TECNICAS):
        linhas.append(f"• /como {chave} — {TECNICAS[chave]['nome']}")
    linhas += ["", f"<i>{LATERALIDADE}</i>"]
    return "\n".join(linhas)
