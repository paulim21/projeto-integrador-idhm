# Roteiro da roda de conversa — seção IDH / IDHM

Tempo-alvo: **6 a 8 minutos**. A regra é não ler a tela: cada bloco abaixo é uma ideia
dita em voz alta, com o número que a sustenta já conferido na base.

> **Se o tempo apertar**, corte nesta ordem: o bloco 7 (gasto público), depois o 6
> (série 2012–2024), depois metade do bloco 5 (municípios, mantendo só a frase da
> amplitude). Os blocos 1 a 4 e 8 a 10 são o núcleo cobrado pela rubrica.

> Todos os valores deste roteiro saem da base tratada do painel (Atlas Brasil / Censos de
> 1991, 2000 e 2010). Se alterar os filtros durante a apresentação, os números mudam — e é
> esse o ponto do dashboard.

---

## 0. Abertura (30 s)

> "Fomos contratados por cinco governos estaduais para responder a uma pergunta só:
> **onde colocar o dinheiro de um fundo de redução de desigualdades para ele render mais
> em desenvolvimento humano?** O indicador que usamos é o IDHM."

Abra a aba **Contexto & notícias** e mostre o infográfico da composição.

> "O IDHM é a média geométrica de três dimensões com o mesmo peso: Longevidade, Educação e
> Renda. Média geométrica, não soma — e essa diferença é toda a análise: **uma dimensão
> baixa derruba o índice inteiro, não dá para compensar com as outras duas.**"

---

## 1. A base não chega pronta (1 min)

Aba **Dados & ETL**.

> "Antes de qualquer gráfico: a planilha chegou com 88 linhas e saiu com 81, que é o número
> certo — 27 unidades da federação vezes 3 Censos."

Aponte duas correções concretas no log:

- **a linha `BRASIL`** no meio das UFs, que inflaria qualquer média se ficasse;
- **o erro de escala**: a renda da Bahia em 2010 estava gravada como `6,63` em vez de
  `0,663`. Vírgula no lugar errado. Como todo índice tem de estar entre 0 e 1, a regra de
  domínio pegou sozinha.

> "E a prova de que a limpeza não deformou nada: recalculamos o IDHM a partir das três
> dimensões e comparamos com o valor publicado. **As 81 linhas fecham com diferença menor
> que 0,001.**"

---

## 2. O retrato de 2010 (1 min 30 s)

Aba **Panorama**, filtro no Censo de 2010.

| Medida | IDHM geral 2010 |
|---|---|
| Média | 0,705 |
| Mediana (Q2) | 0,699 |
| Q1 – Q3 | 0,664 – 0,738 |
| IQR | 0,074 |
| Amplitude | 0,193 (Alagoas 0,631 → Distrito Federal 0,824) |
| Desvio padrão | 0,048 |
| Coeficiente de variação | 6,9% |

> "A média é 0,705 e a mediana é 0,699. A média está acima — ou seja, **poucos estados no
> topo puxam o valor médio para cima e escondem a situação da metade de baixo.** Quatorze
> das 27 UFs estão abaixo da média. Quando a gente fala de um estado típico, a medida
> honesta é a mediana."

> "A amplitude de 0,193 separa Alagoas do Distrito Federal. E isso não é um acidente
> geográfico: **13 das 16 unidades do Norte e Nordeste estão abaixo da mediana nacional.**"

---

## 3. Qual dimensão é o problema (1 min 30 s)

Aba **Estatística descritiva**, tabela das quatro medidas lado a lado.

| Dimensão (2010) | Média | Amplitude | Coef. de variação |
|---|---|---|---|
| Longevidade | 0,809 | 0,118 | 3,7% |
| Renda | 0,707 | 0,251 | 8,1% |
| Educação | 0,612 | 0,222 | 9,3% |

> "Olhem o boxplot das três dimensões. **Longevidade é a caixa mais alta e mais estreita**:
> média 0,809 e coeficiente de variação de só 3,7%. O Brasil resolveu razoavelmente bem, e
> de forma parecida em todo lugar, a parte de expectativa de vida."

> "**Educação é a caixa mais baixa e a mais espalhada**: média 0,612, a menor das três, com
> o maior coeficiente de variação, 9,3%. É a dimensão que puxa o índice do país inteiro
> para baixo e é também onde os estados mais diferem entre si. Em 2010 ela vai de 0,520 em
> Alagoas a 0,742 no Distrito Federal."

> "Conclusão de consultoria: **o problema do desenvolvimento humano no Brasil é, antes de
> tudo, um problema de educação.** Não por opinião — pelo formato da distribuição."

---

## 4. Outliers: a regra de 1,5 × IQR (1 min)

> "Aplicamos a regra de Tukey. Para o IDHM geral de 2010: Q1 = 0,664, Q3 = 0,738,
> IQR = 0,074. O intervalo aceitável vai de 0,554 a 0,848."

> "**Nenhuma UF ficou fora.** E isso é um resultado, não a ausência de um. Significa que a
> desigualdade brasileira é uma rampa contínua: não existe um estado descolado do resto.
> Alagoas e Maranhão são o fim da fila, não um ponto fora da curva."

Troque o indicador em foco para **IDHM Renda**:

> "Agora aparece um: **o Distrito Federal, com renda de 0,863, é outlier superior.** É um
> valor real, não erro de digitação — é a concentração de renda do funcionalismo federal em
> uma unidade pequena. **Nós o mantivemos na base**, porque excluí-lo apagaria exatamente a
> desigualdade que viemos medir. O que fazemos é não usar o DF como referência de meta para
> os outros estados."

---

## 5. Dentro dos estados: o recorte municipal (1 min 30 s)

Aba **Municípios**.

> "Até aqui falamos de 27 médias estaduais. Mas a média de um estado esconde o estado.
> Agora são **5.565 municípios**."

| Medida — IDHM municipal, 2010 | Valor |
|---|---|
| Média | 0,659 |
| Mediana | 0,665 |
| Q1 – Q3 | 0,599 – 0,718 |
| IQR | 0,119 |
| Desvio padrão | 0,072 |
| Amplitude | **0,444** (Melgaço/PA 0,418 ate São Caetano do Sul/SP 0,862) |

A frase que ancora o bloco inteiro:

> "A amplitude entre os 27 estados é 0,193. A amplitude **dentro do Pará**, sozinho, é
> **0,328** — de Melgaço, 0,418, a Belém, 0,746. **A desigualdade dentro de cada um dos
> cinco estados que atendemos é maior que a desigualdade entre todos os estados do
> Brasil.** Isso muda o desenho da política pública: não adianta transferir dinheiro para
> a média de um estado."

Mostre a tabela de dispersão por UF, ordenada por IQR:

> "O IQR municipal mede o quanto um estado é desigual por dentro. O **Acre** lidera, com
> 0,078, seguido de **Minas Gerais**, com 0,069. No outro extremo, o **Ceará** tem IQR de
> 0,033 — é o mais homogêneo entre os seus municípios. Atenção à leitura: homogêneo não
> quer dizer bom. O Ceará é parelho em um patamar baixo, com média municipal de 0,617."

> "E daqui sai uma recomendação: **IQR alto pede política focalizada em territórios; IQR
> baixo com média baixa pede política universal.** Dois estados com o mesmo IDHM podem
> exigir desenhos opostos de intervenção."

Outliers na escala municipal:

> "Nos limites de Tukey municipais — de 0,420 a 0,896 — **um único município do país fica
> fora: Melgaço, no Pará, com 0,418.** Um outlier em 5.565 casos. Reforça o que vimos no
> nível estadual: a desigualdade brasileira é uma rampa contínua, não um punhado de
> exceções."

---

## 6. A desigualdade está caindo (1 min)

Aba **As três dimensões**, série histórica.

| Coeficiente de variação do IDHM entre as UFs | 1991 | 2000 | 2010 |
|---|---|---|---|
| | 15,6% | 12,4% | **6,9%** |

> "A dispersão entre os estados **caiu pela metade em vinte anos**. Os estados mais pobres
> cresceram mais rápido: o Maranhão subiu 79% no período, de 0,357 para 0,639, enquanto
> Minas Gerais subiu 53%. Há convergência — ela só é lenta demais para quem está na ponta
> de baixo, e é por isso que o fundo existe."

Role até o bloco da série de 2012 a 2024:

> "A série dos Censos para em 2010. O PNUD, a Fundação João Pinheiro e o IBGE publicam
> desde então uma série anual, o *Radar IDHM*, que vai até **2024** — e ela está aqui, em
> bloco separado, porque **as duas séries não se somam**: a dos Censos vem do Censo
> Demográfico, a anual vem da PNAD Contínua, com metodologia revisada. Juntar as duas no
> mesmo gráfico criaria um degrau que não existe na realidade."

> "O que essa série mostra: em 2024, **todas as 27 UFs estão nas faixas alto ou muito
> alto** — nenhuma permanece onde estava em 2010. E ela registra a pandemia: **2021 é uma
> queda visível em quase todo o país**, efeito sobre longevidade e renda. O Maranhão saiu
> de 0,669 em 2012 para 0,745 em 2024, com recuo em 2021."

---

## 7. Gasto público explica o IDHM? (1 min)

Aba **Estatística descritiva**, bloco "Quem gasta mais por habitante tem IDHM maior?".

> "Essa é a pergunta que todo gestor faz. Para respondê-la foi preciso sair do IBGE: o
> Atlas mede resultado social, não orçamento. Cruzamos o IDHM de 2024 com a **despesa
> empenhada pelos governos estaduais no mesmo ano**, do Siconfi, do Tesouro Nacional."

> "O resultado é contraintuitivo: a correlação de Pearson é **−0,035**. Praticamente nula.
> O gasto por habitante explica **0,1%** da variação do IDHM entre os estados."

> "E o gráfico mostra por quê. Quem mais gasta por habitante em investimento social é o
> **Acre**, R$ 5.782, com IDHM de 0,754. Quem menos gasta é o **Rio de Janeiro**,
> R$ 1.274, com IDHM de 0,819. Estados pequenos recebem transferências constitucionais
> que, divididas por poucos habitantes, produzem gasto per capita alto. **É efeito de
> escala populacional, não de eficiência.**"

> "A conclusão honesta para o consórcio: **gastar mais por habitante, isoladamente, não
> garante IDHM maior.** O que o fundo precisa definir não é só quanto, mas onde — e é
> exatamente isso que o simulador faz. Vale o alerta: correlação não é causa. O IDHM
> responde a décadas de política pública, não ao orçamento de um ano."

---

## 8. O diagnóstico de cada gestor (1 min 30 s)

Comece pelo **radar**, na aba *As três dimensões*, com os cinco estados selecionados:

> "Um olhar só no radar já entrega o diagnóstico. Os cinco triângulos têm o **mesmo
> formato**: largos no vértice da Longevidade, achatados no da Educação. Nenhum dos cinco
> estados tem um problema particular — todos têm **o mesmo problema**, e ele é educação.
> A linha pontilhada é a média do país, e Minas Gerais é o único dos cinco que fica por
> fora dela nos três vértices."

Depois vá para a aba **Consultoria & Fundo** e troque a persona no seletor.

| Gestor | UF | IDHM 2010 | Posição | Gargalo interno | Maior defasagem x país |
|---|---|---|---|---|---|
| João | Maranhão | 0,639 | 26º | Educação (0,562) | **Renda** (−0,095) |
| Helder | Pará | 0,646 | 24º | Educação (0,528) | Educação |
| Susu | Bahia | 0,660 | 22º | Educação (0,555) | Educação |
| Gladson | Acre | 0,663 | 21º | Educação (0,559) | Educação |
| Verinha | Minas Gerais | 0,731 | 9º | Educação (0,638) | acima da média nas três |

Use o Maranhão para mostrar as duas leituras:

> "João, o menor número do seu estado é Educação, 0,562. Mas **a dimensão em que o Maranhão
> está mais atrás do resto do país é Renda**: 0,095 ponto abaixo da média nacional, contra
> 0,050 em Educação. Não é contradição — é que os patamares nacionais são diferentes. A
> educação é baixa em quase todo lugar, então estar baixo nela te distancia menos dos
> outros. **O índice é travado pela educação; a posição relativa é perdida na renda.**"

> "E a simulação diz qual das duas rende mais: se a Renda do Maranhão sozinha subisse até a
> média das 27 UFs, o IDHM iria de 0,639 para **0,670**, mais 0,031. É o maior retorno entre
> as três dimensões. **Começa por aí.**"

Para Minas Gerais, inverta o tom:

> "Verinha, Minas está acima da média nacional nas três dimensões — 9º lugar. Seu caso não
> é de recuperação. Para Minas, a referência deixa de ser a média e passa a ser o grupo de
> ponta: o painel troca sozinho o referencial para o 3º quartil."

---

## 9. O fundo (1 min)

Mexa nos controles ao vivo.

> "O critério tem que caber em uma frase de audiência pública: **recebe quem está abaixo da
> referência, e recebe mais quem está mais longe dela.** Com a mediana nacional como corte,
> 13 das 27 UFs são elegíveis."

Mostre o rateio com R$ 10 bilhões:

> "Com 10 bilhões, o Maranhão é prioridade 2 e fica com 12,6% do fundo. Dentro do estado, o
> dinheiro se divide entre as três dimensões na proporção da lacuna de cada uma — por isso a
> maior fatia do Maranhão vai para Renda, e não para Educação. **O mesmo critério que define
> quanto cada estado recebe define para onde o dinheiro vai dentro dele.**"

Suba o controle de **concentração** para 2,0:

> "E se o fundo for mais concentrado? O expoente muda o peso da lacuna. **Nenhum número
> aqui é escolha política escondida no código** — é tudo parâmetro visível, que o gestor
> mexe e vê o resultado."

Encerre com o teto:

> "O teto por estado existe para evitar que uma UF absorva o fundo inteiro. Também é
> parâmetro."

---

## 10. Fechamento (20 s)

> "Resumo: o IDHM do Brasil é travado pela **educação**; a desigualdade entre estados
> **está caindo, mas devagar**; não há estado fora da curva — há uma **rampa contínua** —
> e a maior desigualdade está **dentro** dos estados, não entre eles. Gasto por habitante,
> sozinho, não explica o índice. Por isso o fundo deve ser rateado pela **lacuna até a
> referência**, com a divisão interna seguindo a dimensão em que cada estado mais perde
> para o país, e executado de forma **focalizada nos territórios** — não distribuído pela
> média estadual."

---

## Perguntas prováveis e respostas curtas

**"Por que 2010 e não dados atuais?"**
Porque é a última série oficial comparável do IDHM por UF, calculada pelo Atlas Brasil
sobre os Censos. Existem estimativas anuais, mas com metodologia diferente — misturar as
duas séries na mesma tabela produziria comparação falsa.

**"A moda faz sentido em dado contínuo?"**
Quase não: o IDHM raramente repete valor. Por isso ela é calculada sobre o valor arredondado
em duas casas, o que equivale a perguntar em qual centésimo do índice se concentram mais
UFs. É a leitura honesta da moda aqui.

**"Por que desvio padrão populacional?"**
As 27 UFs não são amostra de nada: são a população completa de unidades da federação. O
painel exibe os dois valores lado a lado, e a diferença entre eles é desprezível (0,048
contra 0,049).

**"Por que não excluir os outliers?"**
Porque o outlier encontrado — o DF na renda — é um valor verdadeiro. Excluir é legítimo
quando o ponto é erro de medição; aqui ele é o fenômeno. O que fazemos é não usá-lo como
meta de convergência para os demais.

**"Por que a correlação com o gasto público deu quase zero? O gráfico não serve?"**
Serve, e é justamente esse o achado. Um r de −0,035 responde "não" a uma hipótese que o
gestor traz pronta, e a resposta vem com a explicação: o gasto per capita é inflado nos
estados pequenos pelas transferências constitucionais. Um resultado nulo bem explicado
vale mais que uma correlação forçada.

**"Por que duas séries temporais separadas?"**
Porque são metodologias diferentes. A série de 1991 a 2010 é censitária; a de 2012 a 2024
é estimada pela PNAD Contínua. Colocá-las no mesmo eixo criaria entre 2010 e 2012 um
degrau artificial, que seria lido como mudança real.

**"Essa projeção de anos é uma previsão?"**
Não. É extrapolação do ritmo de 1991 a 2010, útil para dimensionar a ordem de grandeza do
desafio. Ela ignora choques e o efeito de teto à medida que o índice se aproxima de 1 —
o próprio painel avisa isso embaixo do resultado.
