# Números que Falam — Descobrindo o Brasil
## Seção individual: Índice de Desenvolvimento Humano (IDH / IDHM)

Dashboard interativo em **Python + Streamlit + Pandas + NumPy + Plotly** que analisa as
três dimensões do IDHM — **Longevidade, Educação e Renda** — nas 27 unidades da federação,
identifica o que puxa o índice para baixo em cada estado e dimensiona um
**Fundo Regional de Redução de Desigualdades**.

O painel é apresentado na perspectiva de uma startup de análise de dados prestando
consultoria a cinco gestores públicos:

| Persona | Cargo | UF |
|---|---|---|
| João | Governador do Maranhão | MA |
| Helder | Governador do Pará | PA |
| Gladson | Governador do Acre | AC |
| Susu | Governador da Bahia | BA |
| Verinha | Governadora de Minas Gerais | MG |

---

## Como rodar

```bash
pip install -r requirements.txt
```

```bash
python scripts/gerar_base_bruta.py
```

```bash
python scripts/gerar_imagens.py
```

```bash
streamlit run app.py
```

Os dois scripts só precisam ser executados na primeira vez: eles geram a base bruta
(`dados/raw/idhm_uf_bruto.csv`) e as duas imagens explicativas da pasta `assets/`.
O painel abre em `http://localhost:8501`.

---

## O que o painel entrega

### 1. Panorama
Cartões com média, mediana, amplitude, desvio padrão, IQR e coeficiente de variação;
ranking das 27 UFs; distribuição por região; contagem por faixa do PNUD; tabela completa.

### 2. Dados & ETL
A base chega como uma extração manual de planilha, com os problemas de sempre. O painel
mostra o **log do tratamento gerado em tempo de execução**, com o número de linhas após
cada etapa:

| # | Problema na base bruta | Tratamento |
|---|---|---|
| 1 | Vírgula decimal, colunas separadas por `;` | Conversão explícita de tipo |
| 2 | Nomes de UF com espaço sobrando e caixa inconsistente | Normalização de texto + remapeamento pela sigla |
| 3 | Ano como texto (`" 2000"`, `"2.010"`) | Limpeza do separador de milhar e conversão para inteiro |
| 4 | Linha de agregado `BRASIL` entre as UFs | Filtro pela lista oficial das 27 siglas |
| 5 | Linhas duplicadas | `drop_duplicates` na chave ano + UF |
| 6 | IDHM total em branco | Recalculado pela média geométrica das três dimensões |
| 7 | Erro de escala (`6,63` em vez de `0,663`) | Regra de domínio: todo índice está em [0, 1] |
| 8 | Coluna livre de observações | Descartada |

**Validação cruzada:** depois da limpeza, o IDHM recalculado a partir das dimensões bate
com o valor publicado nas 81 linhas (27 UFs × 3 Censos) com diferença menor que 0,001.

### 3. Estatística descritiva
Média, mediana, moda, Q1/Q2/Q3, IQR, amplitude, desvio padrão (populacional e amostral),
variância, coeficiente de variação e assimetria — para o IDHM e para cada uma das três
dimensões. Boxplot das dimensões, histograma com média e mediana marcadas, boxplot por
região, dispersão Educação × Renda e matriz de correlação.

**Outliers** pela regra de Tukey (1,5 × IQR), com os limites explícitos, a distância de
cada UF além do limite em número de IQRs e a justificativa de manutenção ou exclusão.

### 4. As três dimensões
Perfil comparado das três dimensões por estado, evolução 1991 → 2000 → 2010, tabela de
ganho absoluto e relativo, e gráfico de lacuna até uma referência ajustável.

### 5. Consultoria & Fundo Regional
Para cada gestor:

- posição do estado no ranking e no quartil da distribuição;
- **gargalo interno** (menor dimensão — é ela que segura a média geométrica);
- **maior defasagem em relação ao país** (maior distância até a média das 27 UFs);
- simulação de quanto o IDHM subiria levando cada dimensão, sozinha, até a referência;
- projeção de quantos anos o estado levaria para alcançar uma meta no ritmo histórico;
- **simulador do fundo**: valor total, critério de elegibilidade, grau de concentração e
  teto por estado, com rateio por UF e repartição interna entre as três dimensões.

### 6. Contexto & notícias
Infográfico da composição do índice, régua das faixas do PNUD com os estados atendidos,
reportagens e fontes oficiais (lidas de `dados/noticias.csv`, editável sem mexer no código)
e um glossário dos termos estatísticos para a roda de conversa.

---

## Decisões metodológicas

**Por que 1991, 2000 e 2010?** É a série oficial comparável do IDHM por UF, calculada pelo
Atlas do Desenvolvimento Humano no Brasil a partir dos Censos Demográficos do IBGE. Séries
anuais estimadas existem, mas usam metodologias diferentes e não são comparáveis linha a
linha com os valores censitários.

**Desvio padrão populacional.** As 27 UFs são a população completa de unidades da
federação, não uma amostra; por isso a medida de referência é `ddof=0`. O valor amostral
(`ddof=1`) é exibido ao lado para comparação.

**Moda de variável contínua.** O IDHM praticamente não repete valores. A moda é calculada
sobre o valor arredondado em duas casas — equivale a perguntar em qual centésimo do índice
se concentram mais UFs.

**Gargalo interno ≠ maior defasagem.** As três dimensões têm patamares nacionais
diferentes: a Longevidade é alta no Brasil inteiro, a Educação é baixa em quase todo lugar.
A dimensão de menor valor em um estado não é necessariamente aquela em que ele está mais
atrás do país. O painel mostra as duas leituras e o fundo usa a segunda.

**Outliers mantidos.** Nenhuma UF ficou fora dos limites de Tukey no IDHM geral de 2010: a
desigualdade entre os estados é grande, mas é uma variação contínua. Quando algum valor
extremo aparece em outro filtro, ele é mantido — retirá-lo apagaria exatamente a
desigualdade que o estudo quer medir.

---

## Estrutura do projeto

```
.
├── app.py                      # aplicação Streamlit individual
├── secao_idhm.py               # a seção do dashboard (abas, filtros, textos)
├── requirements.txt
├── .streamlit/config.toml      # tema fixo (as cores dos gráficos foram validadas no claro)
├── src/
│   ├── dados_fonte.py          # base de referência, metadados de UF, personas, faixas
│   ├── etl.py                  # extração, limpeza, validação, enriquecimento (com log)
│   ├── estatistica.py          # medidas descritivas e detecção de outliers
│   ├── graficos.py             # todos os gráficos, com paleta e regras fixas
│   └── personas.py             # diagnóstico por gestor e simulador do fundo
├── scripts/
│   ├── gerar_base_bruta.py     # gera dados/raw/idhm_uf_bruto.csv
│   └── gerar_imagens.py        # gera as imagens de assets/
├── dados/
│   ├── raw/idhm_uf_bruto.csv   # base como ela chega (gerada)
│   ├── processed/              # base tratada (gerada pelo ETL)
│   └── noticias.csv            # reportagens e fontes da aba de contexto
└── assets/                     # imagens explicativas (geradas)
```

---

## Integração com o painel do grupo

A seção foi escrita para plugar no painel unificado sem reescrita:

```python
import streamlit as st
from secao_idhm import renderizar_secao

secao = st.sidebar.radio("Seções", ["...", "IDH / IDHM", "..."])
if secao == "IDH / IDHM":
    renderizar_secao()                      # com filtros próprios na barra lateral
    # renderizar_secao(usar_sidebar=False)  # para usar os filtros do grupo
```

`renderizar_secao()` não chama `st.set_page_config` — quem faz isso é o `app.py` do grupo.

---

## Upload de base própria

A barra lateral tem `st.file_uploader`. O arquivo enviado precisa ter:

- `;` como separador de colunas e `,` como separador decimal;
- as colunas `ano`, `sigla`, `unidade_federativa`, `regiao`, `idhm`, `idhm_educacao`,
  `idhm_renda`, `idhm_longevidade`.

O arquivo passa pelo mesmo ETL da base do repositório — inclusive pelas etapas de limpeza.
Sem envio, o painel usa `dados/raw/idhm_uf_bruto.csv`.

---

## Fonte dos dados

**Atlas do Desenvolvimento Humano no Brasil** (PNUD / Ipea / Fundação João Pinheiro),
série dos Censos Demográficos do IBGE de 1991, 2000 e 2010 — <http://www.atlasbrasil.org.br/>
