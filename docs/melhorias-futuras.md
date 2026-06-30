# Melhorias Futuras

Este documento registra somente melhorias que ainda precisam ser avaliadas ou
implementadas na Forja de Ferro.

## Estado Atual

Nao existem melhorias tecnicas priorizadas pendentes.

Novas propostas devem entrar neste arquivo apenas quando resolverem uma
necessidade observada no uso. Evite adicionar funcionalidades por antecipacao
ou manter tarefas ja concluidas como se ainda fizessem parte da fila.

## Principios

- preservar o SQLite como fonte da verdade
- manter o bot simples de operar pelo celular
- priorizar confiabilidade antes de adicionar funcionalidades
- evitar interpretar RPE 9 isolado como estagnacao
- manter compatibilidade com o historico existente
- testar mudancas sem alterar o banco ou a sessao reais
- manter interface e documentacao em PT-BR
- evitar novos aliases e exigir `/` nos comandos textuais do Telegram

## Novas Propostas

### Analises Avancadas Do Dashboard

**Estado parcial:** foram entregues painel de equilibrio muscular, PRs
expandidos, grafico de carga vs. RPE, filtro rapido por segmento anatomico,
calendario/heatmap de sessoes, relatorio semanal local e renderizacao dos
graficos de dados com Chart.js. Permanecem pendentes tendencias semanais por
segmento, deteccao automatica de lacunas, fadiga acumulada, sugestao de proxima
sessao, alvos semanais configuraveis e notas de tecnica/dor/amplitude.

**Problema observado:** o dashboard ja mostra volume, RPE, mapa muscular e
comparacoes basicas, mas ainda nao transforma esses dados em uma leitura
integrada do equilibrio do programa, lacunas de treino, fadiga recente e
proximas decisoes de progressao.

**Comportamento esperado:**

- mostrar tendencia semanal por grupo e segmento anatomico, com comparacao
  contra a media recente
- criar um painel de equilibrio muscular, comparando anterior vs. posterior,
  empurrar vs. puxar, quadriceps vs. posteriores, peitoral vs. costas e
  deltoide anterior/lateral/posterior
- detectar lacunas do programa, como ausencia de puxada vertical, panturrilha,
  core direto, rotadores externos ou excesso relativo de deltoide anterior
- calcular um indicador descritivo de fadiga acumulada por segmento usando
  volume recente, RPE e proximidade temporal, sem diagnostico clinico
- sugerir a proxima sessao de forma conservadora, indicando quais exercicios
  podem subir, manter ou exigir cautela com base em RPE, consolidacoes e
  segmentos sobrecarregados
- expandir recordes para maior carga, maior volume, melhor 1RM estimado e
  melhor desempenho com a mesma carga e menor RPE
- mostrar grafico de carga vs. RPE por exercicio para evidenciar consolidacao,
  queda de esforco e possiveis travamentos
- permitir definir alvos semanais por grupo ou segmento e exibir abaixo, no
  alvo ou acima do intervalo planejado
- adicionar filtros interativos por periodo, exercicio, grupo muscular e
  segmento anatomico, usando JavaScript puro ou uma biblioteca leve quando isso
  simplificar a manutencao
- criar calendario/heatmap de sessoes por dia, com intensidade visual por
  volume, RPE ou fadiga estimada
- gerar um relatorio semanal em HTML ou PDF com volume, RPE, segmentos
  treinados, recordes, lacunas e sugestoes
- permitir notas de tecnica, dor, amplitude, execucao e observacoes por
  exercicio ou sessao para contextualizar alertas que RPE e carga nao explicam
  sozinhos

**Impacto esperado:** transformar o dashboard de um painel descritivo em uma
ferramenta de revisao do programa, ajudando a tomar decisoes sobre progressao,
recuperacao, lacunas e equilibrio muscular sem adicionar atrito ao registro pelo
Telegram.

**Criterios objetivos de conclusao:**

1. A tendencia por segmento mostra pelo menos volume semanal, media movel e
   variacao percentual em periodo configuravel.
2. O painel de equilibrio apresenta relacoes claras e auditaveis, sem rotular
   automaticamente desequilibrio como lesao ou diagnostico.
3. A deteccao de lacunas usa regras configuraveis e explica qual evidencia foi
   usada para cada alerta.
4. A fadiga acumulada informa formula, janela temporal e limitacoes, e evita
   classificacoes clinicas.
5. As sugestoes da proxima sessao mostram o motivo da recomendacao e nunca
   aumentam carga automaticamente.
6. Graficos interativos mantem o dashboard funcionando como HTML local sem
   servidor obrigatorio.
7. Exportacao semanal nao inclui segredos, caminhos locais sensiveis ou estado
   temporario indevido.
8. Notas de tecnica ficam persistidas em estrutura propria e sao opcionais no
   fluxo normal.
9. Testes cobrem os calculos centrais, dados ausentes, historico antigo,
   configuracoes e renderizacao HTML.
10. A documentacao diferencia volume atribuido, estimativas e observacoes
    subjetivas de medidas fisiologicas reais.

**Riscos e decisoes pendentes:**

- avaliar se Chart.js deve continuar via CDN com versao fixa ou ser empacotado
  localmente para uso completamente offline
- definir configuracao de alvos semanais sem tornar o banco ou o bot complexos
- escolher uma formula simples e auditavel para fadiga acumulada, deixando claro
  que ela e heuristica
- evitar que sugestoes automaticas substituam julgamento sobre tecnica, dor,
  sono, alimentacao e recuperacao
- definir se relatorios PDF serao gerados por HTML local, navegador headless ou
  biblioteca Python
- projetar notas de tecnica sem poluir o registro rapido de carga e RPE

### Registro De Repeticoes Reais E Indicadores De Forca

**Problema observado:** o sistema registra carga e RPE, mas presume que todas
as series e repeticoes prescritas foram concluidas. Quando um treino `3x5`
termina, por exemplo, em `5, 5 e 4` repeticoes, o volume e o desempenho ficam
superestimados.

**Comportamento esperado:**

- preservar o formato atual `80 8`, interpretado como 80 kg, RPE 8 e execucao
  completa conforme a prescricao
- aceitar opcionalmente repeticoes reais por serie, como `80 5,5,4 9`
- validar a quantidade de series e os valores informados antes de gravar
- armazenar as repeticoes realizadas sem substituir a prescricao original
- calcular volume real a partir da soma das repeticoes executadas
- apresentar 1RM estimado, recordes e tendencias como estimativas, com formula
  e limitacoes documentadas
- diferenciar claramente carga, repeticoes e RPE observados de indicadores
  derivados
- nao criar classificacoes universais, diagnosticos ou um score composto sem
  referencia e criterio tecnico documentados

**Impacto esperado:** tornar o historico mais fiel quando houver series
incompletas e permitir acompanhar ganho de forca, desempenho com a mesma carga,
volume executado e evolucao por exercicio sem aumentar o atrito do registro
normal.

**Criterios objetivos de conclusao:**

1. `80 8` continua funcionando sem mudanca no fluxo atual.
2. `80 5,5,5 8` e `80 5,5,4 9` sao aceitos e persistidos corretamente.
3. Entradas com quantidade de series divergente da prescricao ou repeticoes
   invalidas retornam erro claro e nao alteram o banco.
4. Volume, resumo da sessao, dashboard, recordes e comparacoes usam repeticoes
   reais quando existirem e recorrem as prescritas nos registros antigos.
5. Migracao preserva integralmente o historico existente.
6. Testes isolados cobrem parser, validacao, migracao, desfazer, recuperacao de
   sessao, resumo e compatibilidade com registros antigos.
7. A documentacao informa a formula escolhida para 1RM estimado, sua faixa de
   aplicacao e as limitacoes da estimativa.

**Riscos e decisoes pendentes:**

- definir se as repeticoes serao armazenadas em tabela filha por serie ou em
  outra estrutura SQLite normalizada
- definir se o RPE continuara representando o exercicio ou passara a aceitar
  valor por serie em uma etapa futura
- escolher e referenciar a formula de 1RM estimado antes de expor comparacoes
  de forca
- evitar comparar diretamente exercicios, tecnicas ou amplitudes diferentes
  como se medissem a mesma capacidade

### Perfil Individual De Fadiga Por Exercicio

**Dependencia:** esta proposta depende do registro de repeticoes reais por
serie. Analises relacionadas ao descanso tambem dependem do registro do
intervalo realmente realizado, pois o descanso atualmente armazenado e apenas
o prescrito.

**Problema observado:** carga total e RPE final nao mostram quanto o desempenho
caiu entre as series. Duas sessoes com a mesma carga podem representar
capacidades diferentes de sustentar repeticoes e recuperar-se durante o
exercicio.

**Comportamento esperado:**

- calcular a queda absoluta e percentual de repeticoes entre a primeira e as
  demais series realizadas com a mesma carga
- acompanhar a capacidade de sustentar o desempenho separadamente por
  exercicio
- comparar apenas sessoes com prescricao, tecnica e carga suficientemente
  compativeis
- relacionar a queda de repeticoes ao RPE registrado sem tratar associacao como
  causalidade
- quando houver intervalo realizado, comparar faixas de descanso com a
  manutencao das repeticoes
- mostrar tendencias individuais descritivas, sem classificacao clinica ou
  limite universal de fadiga
- explicar os dados usados e o motivo de cada observacao apresentada

**Impacto esperado:** complementar os indicadores de forca com uma medida de
repetibilidade do desempenho, ajudando a identificar se a mesma carga esta
sendo sustentada com menor queda entre series e menor esforco percebido.

**Criterios objetivos de conclusao:**

1. O calculo usa somente repeticoes realmente registradas e nao inventa
   distribuicao por serie para registros antigos.
2. Sessoes com series em cargas diferentes nao sao resumidas por uma unica
   queda percentual sem criterio documentado.
3. O historico por exercicio mostra repeticoes por serie, queda de desempenho,
   carga e RPE usados na comparacao.
4. Observacoes sobre descanso aparecem apenas quando o intervalo realizado foi
   medido e existe amostra individual minima documentada.
5. O sistema usa linguagem descritiva como `queda de repeticoes`, evitando
   diagnosticar fadiga, recuperacao insuficiente ou risco de lesao.
6. Testes cobrem series completas, incompletas, cargas diferentes, dados
   antigos e amostras insuficientes.
7. A documentacao tecnica apresenta definicoes, referencias, limitacoes e
   criterios de comparabilidade.

**Riscos e decisoes pendentes:**

- definir como registrar o intervalo realizado sem tornar o fluxo do Telegram
  lento ou trabalhoso
- definir a amostra minima para apresentar tendencia individual
- decidir como tratar alteracoes deliberadas de carga entre series
- evitar rotulos arbitrarios como fadiga baixa, moderada ou alta sem pontos de
  corte sustentados pela literatura e pelo contexto de aplicacao

### Prescricao Autorregulada Por Top Set E Back-off

**Dependencias:** esta proposta depende do registro de repeticoes reais e da
definicao documentada do calculo de 1RM estimado. Sua aplicacao exige que o
plano identifique explicitamente quais exercicios usam top set e quais series
sao back-offs.

**Problema observado:** a progressao atual usa o desempenho da sessao anterior,
mas nao ajusta as series seguintes conforme o rendimento apresentado no
proprio dia. Em exercicios principais, um top set pode fornecer uma referencia
pratica para ajustar os back-offs sem abandonar a prescricao planejada.

**Comportamento esperado:**

- permitir configurar por exercicio um top set com faixa de repeticoes e RPE
  alvo
- registrar carga, repeticoes reais e RPE do top set
- calcular uma estimativa de forca do dia usando formula e tabela de RPE/RIR
  previamente definidas e referenciadas
- calcular os back-offs por percentual configurado da carga do top set ou do
  1RM estimado do dia
- arredondar a recomendacao conforme os incrementos de carga realmente
  disponiveis para o equipamento
- reduzir ou manter os back-offs quando o top set exceder o RPE alvo ou ficar
  incompleto
- nunca aumentar automaticamente a carga ja colocada no exercicio sem
  confirmacao do usuario
- preservar planos e exercicios que continuam usando a progressao atual
- mostrar formula, dados de entrada e motivo de cada ajuste sugerido

**Impacto esperado:** adaptar o volume secundario ao desempenho observado na
sessao, mantendo a progressao de forca auditavel e mais sensivel a variacoes
diarias de rendimento.

**Criterios objetivos de conclusao:**

1. O recurso e ativado somente em exercicios configurados para top set e
   back-off.
2. O bot aceita o registro normal nos demais exercicios sem alterar o fluxo
   existente.
3. A recomendacao informa top set registrado, metodo de calculo, percentual,
   arredondamento e carga sugerida para o back-off.
4. Top set acima do RPE alvo ou com repeticoes incompletas nao gera aumento
   automatico dos back-offs.
5. Dados insuficientes, RPE ausente ou entrada fora da faixa validada resultam
   em orientacao conservadora claramente explicada.
6. O banco preserva separadamente prescricao, desempenho realizado e
   recomendacao calculada.
7. Testes cobrem RPE abaixo, dentro e acima do alvo, repeticoes incompletas,
   arredondamento, falta de RPE, exercicios nao configurados e historico antigo.
8. A documentacao apresenta referencias, formula de 1RM estimado, tabela de
   RPE/RIR, faixa de aplicacao e limitacoes.

**Riscos e decisoes pendentes:**

- selecionar referencias e uma tabela de RPE/RIR apropriada ao treinamento de
  forca antes de definir as regras numericas
- definir se o back-off usa percentual da carga real do top set ou do 1RM
  estimado do dia em cada tipo de plano
- limitar estimativas em series longas ou exercicios nos quais o RPE e menos
  confiavel
- evitar que variacoes de tecnica, amplitude ou equipamento sejam
  interpretadas como mudanca real de forca
- definir como representar top set e back-offs no esquema dos planos sem
  comprometer a compatibilidade com os modelos existentes

### Mapa De Intensidade Para Forca

**Dependencias:** esta proposta depende do registro de repeticoes reais e de
uma referencia de 1RM ou 1RM estimado valida para cada exercicio analisado.

**Problema observado:** volume total isolado nao informa quanto do treinamento
foi executado em intensidades especificas para o desenvolvimento e a pratica de
forca maxima. O projeto ainda nao mostra a distribuicao das repeticoes conforme
a intensidade relativa.

**Comportamento esperado:**

- calcular a intensidade relativa de cada registro como percentual da
  referencia de 1RM adotada para o exercicio
- consolidar repeticoes realizadas por faixa de intensidade em cada exercicio,
  sessao, semana e periodo selecionado
- mostrar contagens especificas de repeticoes acima de limites configurados,
  como 80%, 85% e 90%
- apresentar intensidade media ponderada pelas repeticoes realizadas
- separar claramente 1RM testado de 1RM estimado
- permitir faixas configuraveis e registrar a versao da classificacao usada
- analisar exercicios individualmente antes de produzir qualquer consolidacao
  geral
- exibir dados insuficientes ou referencia desatualizada em vez de calcular
  percentuais enganosos
- tratar o mapa como descricao da exposicao a intensidade, nao como prova
  isolada de que a prescricao e adequada

**Impacto esperado:** mostrar se o treinamento executado esta concentrado em
cargas leves, moderadas ou altas em relacao a capacidade estimada do proprio
praticante, complementando volume, RPE e tendencia de forca.

**Criterios objetivos de conclusao:**

1. Cada percentual informa qual referencia de 1RM foi usada, sua data e se ela
   foi testada ou estimada.
2. As faixas de intensidade possuem definicao, referencia e configuracao
   documentadas, sem serem apresentadas como limites universais.
3. As contagens usam repeticoes realmente executadas quando disponiveis e
   identificam registros antigos baseados na prescricao.
4. A intensidade media e ponderada pelas repeticoes, com formula visivel na
   documentacao.
5. Exercicios com tecnica, amplitude ou equipamento diferentes nao compartilham
   automaticamente a mesma referencia de 1RM.
6. O dashboard permite consultar a distribuicao por exercicio e periodo sem
   misturar indiscriminadamente levantamentos principais e acessorios.
7. Testes cobrem limites das faixas, arredondamento, referencia ausente,
   referencia desatualizada, 1RM testado, 1RM estimado e dados antigos.
8. A documentacao explica que exposicao a cargas altas e apenas uma parte da
   preparacao para forca e deve ser interpretada com volume, esforco,
   recuperacao e especificidade.

**Riscos e decisoes pendentes:**

- selecionar referencias academicas e definir faixas padrao antes de codificar
  limites numericos
- definir quando uma referencia de 1RM fica desatualizada
- decidir quais exercicios aceitam mapa de intensidade por padrao
- evitar que estimativas instaveis de 1RM causem mudancas artificiais de faixa
- definir se o sistema permitira registrar testes diretos de 1RM separadamente
  dos recordes estimados

### Melhores Series E Recordes Por Repeticoes

**Dependencia:** a identificacao precisa de recordes por repeticoes depende do
registro das repeticoes realmente executadas. Registros antigos podem continuar
usando a prescricao, mas devem ser identificados como tal.

**Problema observado:** o resumo atual identifica recordes gerais de carga ou
volume, mas nao diferencia claramente melhor carga para uma quantidade de
repeticoes, melhor 1RM estimado e melhora de desempenho com menor RPE.

**Comportamento esperado:**

- identificar a maior carga concluida para cada quantidade de repeticoes por
  exercicio
- identificar a melhor serie por volume, calculado como carga multiplicada
  pelas repeticoes daquela serie
- identificar separadamente o maior 1RM estimado, sempre rotulado como
  estimativa
- reconhecer quando a mesma carga e quantidade de repeticoes forem realizadas
  com RPE menor
- reconhecer quando a mesma carga for realizada com mais repeticoes
- mostrar recordes no resumo da sessao e no historico do exercicio
- preservar separadamente recordes observados, recordes estimados e melhoras de
  eficiencia por RPE
- exigir tecnica, amplitude, equipamento e variante de exercicio compativeis
  nas comparacoes

**Impacto esperado:** tornar o ganho de forca visivel em diferentes faixas de
repeticoes sem depender apenas do maior peso absoluto ou do volume total da
sessao.

**Criterios objetivos de conclusao:**

1. Um recorde como `maior carga para 5 repeticoes` usa repeticoes realmente
   concluidas quando esse dado estiver disponivel.
2. Recordes baseados em prescricao antiga aparecem identificados e nao sao
   tratados como equivalentes silenciosamente.
3. O sistema nao chama maior 1RM estimado de recorde real de 1RM.
4. Queda de RPE com carga e repeticoes iguais aparece como melhora de
   eficiencia, nao como aumento comprovado de forca maxima.
5. Series incompletas podem gerar recorde para a quantidade efetivamente
   realizada, mas nao para a quantidade prescrita.
6. Empates possuem regra deterministica e documentada, considerando data, RPE
   e qualidade dos dados.
7. Testes cobrem recorde por repeticoes, volume por serie, 1RM estimado,
   melhora por RPE, empate, serie incompleta e historico antigo.
8. A documentacao define cada tipo de recorde, formula usada e limitacoes.

**Riscos e decisoes pendentes:**

- definir se serao exibidos recordes para qualquer numero de repeticoes ou
  apenas faixas configuradas por exercicio
- evitar excesso de notificacoes para recordes pouco relevantes
- escolher a formula de 1RM estimado antes de ativar esse tipo de recorde
- definir como mudancas de tecnica, amplitude ou equipamento invalidam a
  comparacao historica

### Peso Corporal E Forca Relativa

**Estado parcial:** o historico temporal de peso corporal, o comando
`/peso VALOR`, a consulta `/peso`, o backup/exportacao e o indicador de peso no
dashboard foram entregues. Permanecem neste roadmap a associacao temporal com
sessoes e os calculos de forca relativa.

**Dependencia:** os indicadores de forca relativa dependem de uma referencia de
1RM testado ou estimado para o exercicio. O registro de peso corporal permanece
opcional e nao bloqueia o fluxo de treino.

**Problema observado:** a evolucao atual considera carga e volume absolutos,
mas nao permite observar como a capacidade de produzir forca muda em relacao a
massa corporal do proprio praticante.

**Comportamento esperado:**

- [x] adicionar `/peso VALOR` para registrar peso corporal em quilogramas com
  data e horario
- [x] aceitar virgula ou ponto decimal e validar limites configurados
- [x] permitir consultar o peso atual e o historico sem alterar sessoes de treino
- associar cada sessao ao registro de peso corporal mais recente disponivel na
  data, sem copiar ou reescrever silenciosamente o historico
- calcular forca relativa como `1RM de referencia / peso corporal`
- separar resultados baseados em 1RM testado daqueles baseados em 1RM estimado
- mostrar evolucao de forca absoluta e relativa por exercicio
- identificar dados ausentes ou peso corporal desatualizado em vez de preencher
  valores por interpolacao
- manter o registro normal de carga e RPE completamente inalterado

**Impacto esperado:** permitir acompanhar se o rendimento esta melhorando,
mantendo-se ou caindo em relacao ao peso corporal, inclusive durante fases de
ganho ou perda de massa.

**Criterios objetivos de conclusao:**

1. `/peso 82,5` e `/peso 82.5` registram o mesmo valor validado.
2. O peso corporal e armazenado como serie temporal, sem sobrescrever registros
   anteriores.
3. Cada indicador informa a data e a origem do peso corporal utilizado.
4. Forca relativa baseada em 1RM estimado aparece explicitamente como
   estimativa.
5. O sistema nao calcula forca relativa quando o peso esta ausente ou fora do
   prazo de validade configurado.
6. Alterar ou excluir um peso exige operacao explicita e deixa o comportamento
   historico documentado.
7. O dashboard separa peso corporal, forca absoluta e forca relativa por
   exercicio e periodo.
8. Testes cobrem formato decimal, validacao, historico, peso ausente,
   desatualizacao, associacao temporal e compatibilidade com sessoes antigas.
9. A documentacao orienta que comparacoes sejam feitas em condicoes de pesagem
   semelhantes e explica as limitacoes da razao simples.

**Riscos e decisoes pendentes:**

- definir limites de validacao e prazo para considerar um peso atualizado
- decidir se a sessao guarda uma referencia imutavel ao peso ou resolve o valor
  pela linha temporal durante a consulta
- evitar classificacoes normativas universais baseadas apenas na razao entre
  carga e peso corporal
- usar DOTS ou outra formula alometrica somente se houver levantamento,
  populacao e contexto compativeis com a formula escolhida
- definir comandos seguros para corrigir ou remover registros de peso corporal

Antes de adicionar um item:

1. confirmar que o problema foi observado no uso real
2. descrever o impacto e o comportamento esperado
3. definir um criterio objetivo de conclusao
4. avaliar riscos para o banco e o historico
5. planejar testes isolados

## Historico De Entregas

### 2026-06-25

- perfil corporal persistido com altura e idade
- calculo de IMC e relacao cintura/altura no dashboard usando as medicoes mais
  recentes

### 2026-06-24

- configuracao da barra reta de 2,20 m e 11 kg nos supinos, Agachamento
  Zercher, Remada curvada, Desenvolvimento em pe, Levantamento Terra Romeno e
  Remada curvada alta no peito
- configuracao da barra oca de 1,50 m e 1 kg no Agachamento sumô com barra à
  frente

### 2026-06-23

- registro temporal da circunferencia da cintura pelo comando `/cintura`,
  com consulta de historico, dashboard, backup e exportacao

### 2026-06-10

- extracao em lote de frames para analise de execucao:
  `8761362 feat: extrai frames de videos locais`
- documentacao do fluxo de videos e frames:
  `2eb008a docs: documenta analise de videos por frames`
- remocao de aliases e exigencia de `/` nos comandos textuais:
  `d2957cb refactor: remove aliases de comandos`
- catalogo centralizado de comandos:
  `3f9d58e docs: centraliza catalogo de comandos`

### 2026-06-09

- alertas coerentes com a regra de RPE:
  `4b693c5 feat: contextualize training alerts`
- testes diretos das regras de treino:
  `13f0b3f test: cover training rules`
- recuperacao da sessao ativa pelo SQLite:
  `a09a605 feat: recover active training sessions`
- versionamento e migracoes do esquema:
  `fee63a4 feat: version SQLite schema`
- backup, exportacao e restauracao:
  `f8ab04b feat: add data backup tools`
- observabilidade e tratamento de falhas do Telegram:
  `b7ff6a3 feat: improve Telegram reliability`
- resumo automatico ao concluir o treino:
  `09d134b feat: summarize completed workouts`
- grupos musculares armazenados no SQLite:
  `1713401 feat: store muscle groups in SQLite`
- planos de treino selecionaveis:
  `846654f feat: add selectable training plans`
- atualizacao do dashboard pelo Telegram:
  `f92b322 feat: update dashboard from Telegram`

## Itens Fora De Prioridade

Os itens abaixo nao devem ser implementados sem uma necessidade concreta:

- criar servidor web apenas para substituir o long polling
- trocar SQLite por banco remoto
- criar aplicativo movel separado
- adicionar contas e autenticacao multiusuario
- tornar o dashboard publico

Esses itens aumentam manutencao e superficie de falha sem resolver problemas
atuais do projeto.

## Manutencao Deste Documento

Ao iniciar uma melhoria:

- registrar a decisao tecnica no documento relacionado
- criar ou atualizar testes
- atualizar `AGENTS.md`, `CLAUDE.md` e
  `.github/copilot-instructions.md` quando o comportamento ou a estrutura mudar
- revisar README, `docs/index.md` e demais guias afetados

Ao concluir:

- remover o item de `Novas Propostas`
- registrar a entrega no historico com data e commit
