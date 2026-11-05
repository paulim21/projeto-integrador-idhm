"""
Seção individual do projeto integrador — Índice de Desenvolvimento Humano (IDH / IDHM).

Este arquivo contém a seção completa e é escrito para ser usado de DUAS formas:

  1. sozinho, pelo `app.py` deste repositório (apresentação individual);
  2. importado pelo painel unificado do grupo:

        from secao_idhm import renderizar_secao
        renderizar_secao()     # desenha a seção inteira na área principal

A função `renderizar_secao()` não chama `st.set_page_config` nem escreve na
barra lateral do grupo sem permissão: o parâmetro `usar_sidebar` controla isso.
"""

from __future__ import annotations

import io
from pathlib import Path

import pandas as pd
import streamlit as st

from src import graficos as gx
from src.dados_fonte import ORDEM_FAIXAS, PERSONAS, UF_NOME
from src.estatistica import (
    ROTULOS,
    detectar_outliers,
    evolucao,
    resumo_descritivo,
    tabela_resumo,
    texto_outliers,
)
from src.etl import CAMINHO_BRUTO, executar_etl, extrair
from src.personas import (
    DIMENSOES,
    NOME_DIMENSAO,
    anos_para_convergir,
    diagnostico_uf,
    indicadores_desigualdade,
    simular_fundo,
    texto_diagnostico,
)

RAIZ = Path(__file__).resolve().parent
ASSETS = RAIZ / "assets"
CAMINHO_NOTICIAS = RAIZ / "dados" / "noticias.csv"

TITULO = "Índice de Desenvolvimento Humano (IDH / IDHM)"
SUBTITULO = (
    "As três dimensões do índice — Longevidade, Educação e Renda — para descobrir "
    "o que puxa o desenvolvimento humano para baixo em cada estado e dimensionar um "
    "Fundo Regional de Redução de Desigualdades."
)


# ---------------------------------------------------------------------------
# Carga de dados (com cache)
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner="Executando o ETL da base de IDHM...")
def _carregar(conteudo: bytes | None = None):
    """Roda o ETL sobre o arquivo enviado ou sobre a base bruta do repositório."""
    origem = io.BytesIO(conteudo) if conteudo else CAMINHO_BRUTO
    dados, log = executar_etl(origem)
    return dados, log.como_dataframe()


@st.cache_data
def _ler_bruto(conteudo: bytes | None = None) -> pd.DataFrame:
    return extrair(io.BytesIO(conteudo) if conteudo else CAMINHO_BRUTO)


@st.cache_data
def _ler_noticias() -> pd.DataFrame:
    if CAMINHO_NOTICIAS.exists():
        return pd.read_csv(CAMINHO_NOTICIAS, sep=";", encoding="utf-8")
    return pd.DataFrame()


# ---------------------------------------------------------------------------
# Utilidades de formatação
# ---------------------------------------------------------------------------

def n(valor, casas: int = 3) -> str:
    """Número no padrão brasileiro: 0.663 -> '0,663'."""
    if valor is None or valor != valor:
        return "—"
    return f"{valor:,.{casas}f}".replace(",", "@").replace(".", ",").replace("@", ".")


def reais(valor: float) -> str:
    """Valor em reais na escala mais legível: bilhões acima de R$ 1 bi, milhões abaixo."""
    if valor is None or valor != valor:
        return "—"
    if abs(valor) >= 1e9:
        return f"R$ {n(valor / 1e9, 2)} bi"
    if abs(valor) >= 1e6:
        return f"R$ {n(valor / 1e6, 1)} mi"
    return f"R$ {n(valor, 2)}"


def br_tabela(df: pd.DataFrame, casas: int = 3, casas_por_coluna: dict | None = None,
              sinal: tuple[str, ...] = ()) -> pd.DataFrame:
    """
    Converte as colunas numéricas para texto no padrão brasileiro (vírgula decimal).

    Fazemos a formatação na mão, e não pelo `Styler`, para que o número apareça
    exatamente igual na tela, no tooltip e no texto corrido do painel.
    """
    casas_por_coluna = casas_por_coluna or {}
    saida = df.copy()
    for coluna in saida.columns:
        if not pd.api.types.is_numeric_dtype(saida[coluna]):
            continue
        if pd.api.types.is_integer_dtype(saida[coluna]):
            continue
        casa = casas_por_coluna.get(coluna, casas)
        prefixo = "+" if coluna in sinal else ""
        saida[coluna] = saida[coluna].map(
            lambda v, c=casa, p=prefixo: "—" if pd.isna(v) else
            (f"{v:{p}.{c}f}".replace(".", ","))
        )
    return saida


def _estilo() -> None:
    st.markdown(
        """
        <style>
          .bloco-destaque{border-left:4px solid #2a78d6;background:rgba(42,120,214,.06);
            padding:.85rem 1.1rem;border-radius:6px;margin:.4rem 0 1rem}
          .bloco-alerta{border-left:4px solid #eb6834;background:rgba(235,104,52,.07);
            padding:.85rem 1.1rem;border-radius:6px;margin:.4rem 0 1rem}
          .cartao-noticia{border:1px solid rgba(11,11,11,.10);border-radius:8px;
            padding:.9rem 1.1rem;margin-bottom:.7rem;background:#fff}
          .cartao-noticia .veiculo{font-size:.78rem;text-transform:uppercase;
            letter-spacing:.04em;color:#52514e}
          .rodape{color:#52514e;font-size:.82rem;border-top:1px solid rgba(11,11,11,.08);
            padding-top:.7rem;margin-top:1.4rem}
          div[data-testid="stMetricValue"]{font-size:1.55rem}
        </style>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Barra lateral de filtros
# ---------------------------------------------------------------------------

def montar_filtros(dados: pd.DataFrame, chave: str = "idhm") -> dict:
    """Desenha os controles na barra lateral e devolve as escolhas."""
    st.sidebar.markdown("### Filtros do IDHM")

    anos = sorted(dados["ano"].unique())
    ano = st.sidebar.select_slider(
        "Ano do Censo", options=anos, value=anos[-1], key=f"{chave}_ano",
        help="A série oficial comparável do IDHM por UF é censitária: 1991, 2000 e 2010.",
    )

    regioes_disp = ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"]
    regioes = st.sidebar.multiselect(
        "Regiões", regioes_disp, default=regioes_disp, key=f"{chave}_regioes",
    )

    ufs_disp = (
        dados[(dados["ano"] == ano) & (dados["regiao"].isin(regioes))]
        .sort_values("uf")["sigla_uf"].tolist()
    )
    ufs = st.sidebar.multiselect(
        "Unidades da Federação",
        ufs_disp,
        default=ufs_disp,
        format_func=lambda s: f"{s} — {UF_NOME[s]}",
        key=f"{chave}_ufs",
        help="Deixe todas marcadas para analisar o país inteiro.",
    )

    indicador = st.sidebar.selectbox(
        "Indicador em foco",
        list(ROTULOS),
        format_func=lambda c: ROTULOS[c],
        key=f"{chave}_indicador",
        help="Troca o indicador usado no ranking, no histograma e no boxplot por região.",
    )

    destacar = st.sidebar.checkbox(
        "Destacar os estados atendidos (MA, PA, AC, BA, MG)",
        value=True, key=f"{chave}_destaque",
    )

    st.sidebar.markdown("---")
    return {
        "ano": int(ano),
        "regioes": regioes,
        "ufs": ufs,
        "indicador": indicador,
        "destaques": list(PERSONAS) if destacar else [],
    }


# ---------------------------------------------------------------------------
# Abas da seção
# ---------------------------------------------------------------------------

def _aba_visao_geral(df_ano: pd.DataFrame, df_filtrado: pd.DataFrame, f: dict) -> None:
    st.subheader(f"Panorama do IDHM nas unidades da federação — Censo {f['ano']}")

    r = resumo_descritivo(df_filtrado[f["indicador"]])
    desig = indicadores_desigualdade(df_filtrado, f["indicador"])

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("UFs no filtro", r.get("n", 0))
    c2.metric(f"Média — {ROTULOS[f['indicador']]}", n(r.get("media")))
    c3.metric("Mediana (Q2)", n(r.get("mediana")))
    c4.metric("Amplitude (máx − mín)", n(r.get("amplitude")),
              help="Distância entre o melhor e o pior estado do filtro.")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Desvio padrão", n(r.get("desvio_padrao")))
    c2.metric("IQR (Q3 − Q1)", n(r.get("iqr")))
    c3.metric("Coef. de variação", f"{n(r.get('coef_variacao'), 1)}%",
              help="Desvio padrão como % da média: permite comparar a desigualdade entre anos e dimensões.")
    c4.metric("Melhor ÷ pior", n(desig.get("razao_melhor_pior"), 2))

    st.markdown(
        f"""<div class="bloco-destaque">
        <b>Leitura para o gestor.</b> No filtro atual, o melhor desempenho é
        {desig.get('melhor_uf', '—')} e o pior é {desig.get('pior_uf', '—')}.
        {desig.get('n_abaixo_media', 0)} das {r.get('n', 0)} UFs estão abaixo da média —
        sinal de distribuição puxada por poucos estados no topo.
        </div>""",
        unsafe_allow_html=True,
    )

    if (ASSETS / "faixas_idhm.png").exists():
        st.image(str(ASSETS / "faixas_idhm.png"), use_container_width=True)

    col_a, col_b = st.columns([3, 2], gap="large")
    with col_a:
        st.markdown(f"**Ranking das UFs — {ROTULOS[f['indicador']]}**")
        st.plotly_chart(
            gx.grafico_ranking(df_filtrado, f["indicador"], f["destaques"]),
            use_container_width=True,
        )
    with col_b:
        st.markdown("**Quantas UFs em cada faixa do PNUD**")
        contagem = (
            df_filtrado["faixa_idhm"].value_counts()
            .reindex(ORDEM_FAIXAS).fillna(0).astype(int)
            .rename_axis("Faixa do PNUD").rename("UFs").to_frame()
        )
        contagem["% das UFs"] = (
            contagem["UFs"] / max(len(df_filtrado), 1) * 100
        ).round(1).map(lambda v: f"{v:.1f}%".replace(".", ","))
        st.dataframe(contagem, use_container_width=True)

        st.markdown("**Distribuição por região**")
        st.plotly_chart(
            gx.grafico_boxplot_regioes(df_filtrado, f["indicador"]),
            use_container_width=True,
        )

    st.markdown("**Tabela completa do ano filtrado**")
    st.dataframe(
        br_tabela(df_filtrado[[
            "sigla_uf", "uf", "regiao", "idhm", "faixa_idhm",
            "idhm_educacao", "idhm_renda", "idhm_longevidade",
            "dimensao_mais_fraca", "desequilibrio_interno",
        ]]).rename(columns={
            "sigla_uf": "UF", "uf": "Estado", "regiao": "Região", "idhm": "IDHM",
            "faixa_idhm": "Faixa", "idhm_educacao": "Educação", "idhm_renda": "Renda",
            "idhm_longevidade": "Longevidade",
            "dimensao_mais_fraca": "Dimensão mais fraca",
            "desequilibrio_interno": "Desequilíbrio interno",
        }),
        use_container_width=True, hide_index=True,
    )


def _aba_etl(bruto: pd.DataFrame, log: pd.DataFrame, tratado: pd.DataFrame) -> None:
    st.subheader("Da planilha bruta à base confiável")
    st.markdown(
        "Nenhuma análise vale mais do que o dado que a alimenta. A base chega como uma "
        "extração manual de planilha e passa por dez etapas de tratamento antes de virar "
        "gráfico. O relatório abaixo é gerado pelo próprio código a cada execução."
    )

    c1, c2, c3 = st.columns(3)
    c1.metric("Linhas na base bruta", len(bruto))
    c2.metric("Linhas após o tratamento", len(tratado))
    c3.metric("Registros esperados", "81", help="27 UFs × 3 Censos (1991, 2000 e 2010).")

    st.markdown("**Problemas encontrados na base bruta**")
    st.markdown(
        """
        | # | Problema | Como foi tratado |
        |---|---|---|
        | 1 | Separador decimal com vírgula e colunas separadas por `;` | Conversão explícita de tipo (`str` → `float`) |
        | 2 | Nomes de UF com espaço sobrando e caixa inconsistente | Normalização de texto e remapeamento pela sigla oficial |
        | 3 | Ano gravado como texto (`" 2000"`, `"2.010"`) | Limpeza do separador de milhar e conversão para inteiro |
        | 4 | Linha de agregado `BRASIL` misturada às UFs | Filtro pela lista oficial das 27 siglas |
        | 5 | Linhas duplicadas da extração | `drop_duplicates` na chave ano + UF |
        | 6 | IDHM total em branco em alguns registros | Recalculado pela média geométrica das 3 dimensões |
        | 7 | Erro de escala (`6,63` em vez de `0,663`) | Regra de domínio: todo índice tem de estar em [0, 1] |
        | 8 | Coluna livre de observações sem valor analítico | Descartada |
        """
    )

    st.markdown("**Log do tratamento (gerado em tempo de execução)**")
    st.dataframe(log, use_container_width=True, hide_index=True)

    with st.expander("Ver a base BRUTA, como ela chega"):
        st.dataframe(bruto.head(30), use_container_width=True, hide_index=True)
    with st.expander("Ver a base TRATADA, pronta para análise"):
        st.dataframe(tratado, use_container_width=True, hide_index=True)

    st.download_button(
        "Baixar a base tratada (CSV)",
        data=tratado.to_csv(index=False).encode("utf-8"),
        file_name="idhm_uf_tratado.csv",
        mime="text/csv",
    )

    st.markdown(
        """<div class="bloco-destaque">
        <b>Validação cruzada.</b> O IDHM é a média geométrica das três dimensões. Depois do
        tratamento, o código recalcula o índice a partir das dimensões e compara com o valor
        publicado: as 81 linhas fecham com diferença menor que 0,001. É a prova de que a
        limpeza não deformou o dado.
        </div>""",
        unsafe_allow_html=True,
    )


def _aba_estatistica(df_filtrado: pd.DataFrame, f: dict) -> None:
    st.subheader("Estatística descritiva do IDHM e das suas três dimensões")

    coluna = f["indicador"]
    r = resumo_descritivo(df_filtrado[coluna])
    if not r:
        st.warning("Sem dados no filtro atual.")
        return

    st.markdown("**Todas as medidas, para os quatro indicadores**")
    resumo = tabela_resumo(df_filtrado)
    st.dataframe(
        br_tabela(resumo, casas_por_coluna={"Coef. de variação (%)": 1, "Moda (2 casas)": 2}),
        use_container_width=True, hide_index=True,
    )

    st.markdown(f"**Detalhe do indicador em foco: {ROTULOS[coluna]}**")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("Medidas de posição")
        st.markdown(
            f"- Média: **{n(r['media'])}**\n"
            f"- Mediana (Q2): **{n(r['mediana'])}**\n"
            f"- Moda (2 casas): **{n(r['moda'], 2)}** ({r['frequencia_moda']} UFs)\n"
            f"- Q1: **{n(r['q1'])}** · Q3: **{n(r['q3'])}**"
        )
    with c2:
        st.markdown("Medidas de dispersão")
        st.markdown(
            f"- Amplitude: **{n(r['amplitude'])}** ({n(r['minimo'])} a {n(r['maximo'])})\n"
            f"- IQR (Q3 − Q1): **{n(r['iqr'])}**\n"
            f"- Desvio padrão (populacional): **{n(r['desvio_padrao'])}**\n"
            f"- Desvio padrão (amostral): **{n(r['desvio_padrao_amostral'])}**"
        )
    with c3:
        st.markdown("Forma da distribuição")
        simetria = (
            "assimetria à direita (cauda de estados melhores)" if r["assimetria"] > 0.2
            else "assimetria à esquerda (cauda de estados piores)" if r["assimetria"] < -0.2
            else "praticamente simétrica"
        )
        relacao = (
            "média > mediana" if r["media"] > r["mediana"]
            else "média < mediana" if r["media"] < r["mediana"] else "média = mediana"
        )
        st.markdown(
            f"- Coeficiente de assimetria: **{n(r['assimetria'], 2)}** → {simetria}\n"
            f"- Comparação: **{relacao}**\n"
            f"- Coef. de variação: **{n(r['coef_variacao'], 1)}%**"
        )

    st.markdown(
        f"""<div class="bloco-destaque">
        <b>Por que média e mediana diferem.</b> A média do {ROTULOS[coluna]} é {n(r['media'])}
        e a mediana é {n(r['mediana'])}. Quando a média fica acima da mediana, poucos estados
        de desempenho alto puxam o valor médio para cima e <i>escondem</i> a situação da metade
        de baixo. Para falar da realidade típica de um estado, a mediana é a medida honesta;
        para somar esforço nacional, a média.
        </div>""",
        unsafe_allow_html=True,
    )

    col_a, col_b = st.columns(2, gap="large")
    with col_a:
        st.markdown("**Boxplot das três dimensões**")
        st.caption(
            "Mostra, para o ano filtrado, como as 27 UFs se espalham em cada dimensão. "
            "A caixa vai de Q1 a Q3 (o IQR), a linha interna é a mediana e os pontos "
            "soltos são outliers pela regra de 1,5 × IQR."
        )
        st.plotly_chart(
            gx.grafico_boxplot_dimensoes(df_filtrado, f["destaques"]),
            use_container_width=True,
        )
    with col_b:
        st.markdown(f"**Histograma — {ROTULOS[coluna]}**")
        bins = st.slider("Número de faixas do histograma", 4, 14, 8, key="bins_hist")
        st.plotly_chart(
            gx.grafico_histograma(df_filtrado, coluna, bins),
            use_container_width=True,
        )

    st.markdown("### Outliers pela regra de 1,5 × IQR")
    st.markdown(texto_outliers(df_filtrado, coluna))

    marcados = detectar_outliers(df_filtrado, coluna)
    fora = marcados[marcados["situacao"] != "Dentro dos limites"]
    if not fora.empty:
        st.dataframe(
            br_tabela(fora, casas_por_coluna={"distancia_em_iqr": 2}).rename(columns={
                "sigla_uf": "UF", "uf": "Estado", "regiao": "Região",
                coluna: ROTULOS[coluna], "situacao": "Situação",
                "distancia_em_iqr": "Distância além do limite (em IQRs)",
            }),
            use_container_width=True, hide_index=True,
        )
    else:
        st.caption(
            "Tabela vazia porque nenhuma UF ficou fora dos limites de Tukey neste filtro — "
            "o resultado faz parte da análise e precisa ser dito na apresentação."
        )

    with st.expander("Ver a classificação de todas as UFs em relação aos limites"):
        st.dataframe(
            br_tabela(marcados, casas_por_coluna={"distancia_em_iqr": 2}).rename(columns={
                "sigla_uf": "UF", "uf": "Estado", "regiao": "Região",
                coluna: ROTULOS[coluna], "situacao": "Situação",
                "distancia_em_iqr": "Distância além do limite (em IQRs)",
            }),
            use_container_width=True, hide_index=True,
        )

    st.markdown("### Educação e Renda andam juntas?")
    st.plotly_chart(gx.grafico_dispersao(df_filtrado, f["destaques"]), use_container_width=True)
    correl = df_filtrado[DIMENSOES].corr().round(3)
    st.markdown("**Correlação entre as dimensões (Pearson)**")
    st.dataframe(
        br_tabela(correl).rename(index=NOME_DIMENSAO, columns=NOME_DIMENSAO),
        use_container_width=True,
    )


def _aba_dimensoes(dados: pd.DataFrame, df_ano: pd.DataFrame, f: dict) -> None:
    st.subheader("As três dimensões: onde cada estado perde pontos")
    st.markdown(
        "O IDHM é média geométrica, não soma. Isso tem uma consequência prática direta: "
        "**a dimensão mais fraca domina o resultado**. Um estado com longevidade alta e "
        "educação baixa não compensa uma com a outra — o índice fica preso perto da pior."
    )

    ufs_foco = st.multiselect(
        "Estados no comparativo",
        sorted(df_ano["sigla_uf"].tolist()),
        default=[s for s in PERSONAS if s in df_ano["sigla_uf"].values],
        format_func=lambda s: f"{s} — {UF_NOME[s]}",
        key="dim_ufs",
    )
    if not ufs_foco:
        st.info("Escolha pelo menos um estado para comparar.")
        return

    st.markdown("**Perfil das três dimensões, estado por estado**")
    st.plotly_chart(gx.grafico_perfil_dimensoes(df_ano, ufs_foco), use_container_width=True)

    st.markdown("**Quem é o gargalo de cada estado**")
    tabela = df_ano[df_ano["sigla_uf"].isin(ufs_foco)][
        ["uf", "idhm", "idhm_educacao", "idhm_renda", "idhm_longevidade",
         "dimensao_mais_fraca", "desequilibrio_interno"]
    ].copy()
    for coluna in DIMENSOES:
        tabela[f"lacuna_{NOME_DIMENSAO[coluna].lower()}"] = (
            df_ano[coluna].mean() - tabela[coluna]
        ).round(3)
    st.dataframe(
        br_tabela(tabela).rename(columns={
            "uf": "Estado", "idhm": "IDHM", "idhm_educacao": "Educação",
            "idhm_renda": "Renda", "idhm_longevidade": "Longevidade",
            "dimensao_mais_fraca": "Gargalo",
            "desequilibrio_interno": "Desequilíbrio interno",
            "lacuna_educação": "Falta p/ média — Educação",
            "lacuna_renda": "Falta p/ média — Renda",
            "lacuna_longevidade": "Falta p/ média — Longevidade",
        }).sort_values("IDHM"),
        use_container_width=True, hide_index=True,
    )
    st.caption(
        "Valores positivos na coluna 'Falta p/ média' indicam quanto o estado está abaixo da "
        "média das UFs naquela dimensão. É esse número que orienta o rateio do fundo."
    )

    st.markdown("### Evolução entre os Censos de 1991, 2000 e 2010")
    indicador_evo = st.selectbox(
        "Indicador na série histórica",
        list(ROTULOS), format_func=lambda c: ROTULOS[c], key="evo_ind",
    )
    st.plotly_chart(
        gx.grafico_evolucao(dados, ufs_foco, indicador_evo),
        use_container_width=True,
    )

    linhas = []
    for sigla in ufs_foco:
        serie = evolucao(dados, sigla, indicador_evo)
        if serie.empty:
            continue
        linhas.append({
            "Estado": UF_NOME[sigla],
            "1991": serie[indicador_evo].iloc[0],
            "2000": serie[indicador_evo].iloc[1] if len(serie) > 1 else None,
            "2010": serie[indicador_evo].iloc[-1],
            "Ganho 1991→2010": serie[indicador_evo].iloc[-1] - serie[indicador_evo].iloc[0],
            "Crescimento %": (serie[indicador_evo].iloc[-1] / serie[indicador_evo].iloc[0] - 1) * 100,
        })
    if linhas:
        evo = pd.DataFrame(linhas).sort_values("Ganho 1991→2010", ascending=False)
        st.dataframe(
            br_tabela(
                evo,
                casas_por_coluna={"Crescimento %": 1},
                sinal=("Ganho 1991→2010", "Crescimento %"),
            ),
            use_container_width=True, hide_index=True,
        )

    st.markdown("### Quanto falta para alcançar a referência")
    referencia = st.slider(
        "Valor de referência do indicador", 0.40, 1.00,
        float(round(df_ano[f["indicador"]].max(), 2)), 0.01,
        key="ref_lacuna",
        help="Por padrão, o melhor desempenho do ano. Pode ser usado como meta de convergência.",
    )
    st.plotly_chart(
        gx.grafico_lacuna(df_ano, f["indicador"], referencia, f["destaques"]),
        use_container_width=True,
    )


def _aba_consultoria(dados: pd.DataFrame, df_ano: pd.DataFrame, df_filtrado: pd.DataFrame, f: dict) -> None:
    st.subheader("Consultoria aos gestores e o Fundo Regional de Redução de Desigualdades")
    st.markdown(
        "Esta é a entrega da consultoria: para cada gestor, qual dimensão está travando o "
        "índice do seu estado, quanto o IDHM subiria se esse gargalo fosse corrigido e "
        "quanto do fundo o estado recebe segundo um critério público e auditável."
    )

    siglas_personas = [s for s in PERSONAS if s in df_ano["sigla_uf"].values]
    escolhido = st.selectbox(
        "Gestor atendido",
        siglas_personas,
        format_func=lambda s: f"{PERSONAS[s]['nome']} — {PERSONAS[s]['cargo']}",
        key="persona_sel",
    )

    d = diagnostico_uf(df_ano, dados, escolhido)
    if not d:
        st.warning("Estado fora do filtro atual.")
        return

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("IDHM", n(d["idhm"]), help=f"Faixa: {d['faixa']}")
    c2.metric("Posição entre as 27 UFs", f"{d['posicao']['posicao']}º")
    c3.metric("Gargalo interno", NOME_DIMENSAO[d["dimensao_mais_fraca"]],
              delta=n(d["valores"][d["dimensao_mais_fraca"]]),
              delta_color="off",
              help="Dimensão de menor valor — é ela que segura a média geométrica.")
    c4.metric("Maior defasagem x país", NOME_DIMENSAO[d["dimensao_maior_defasagem"]],
              delta=n(-d["lacunas"][d["dimensao_maior_defasagem"]]),
              delta_color="inverse",
              help="Dimensão em que o estado está mais distante da média das 27 UFs. "
                   "É o critério usado no rateio do fundo.")

    st.markdown(texto_diagnostico(d))

    st.markdown("**Ganho de IDHM ao levar cada dimensão, sozinha, até a referência**")
    st.caption(f"Referência usada para este estado: {d['referencial']}.")
    ganhos = pd.DataFrame([
        {
            "Dimensão": NOME_DIMENSAO[c],
            "Valor atual": d["valores"][c],
            "Referência": d["alvo"][c],
            "IDHM resultante": d["idhm"] + g,
            "Ganho no IDHM": g,
        }
        for c, g in d["ganhos_por_dimensao"].items()
    ]).sort_values("Ganho no IDHM", ascending=False)
    st.dataframe(
        br_tabela(ganhos, sinal=("Ganho no IDHM",)),
        use_container_width=True, hide_index=True,
    )

    st.markdown("**Em quanto tempo o estado chega à meta, no ritmo histórico?**")
    meta = st.slider(
        "Meta de IDHM para o estado", 0.60, 0.95, 0.800, 0.005, key="meta_conv",
        help="0,700 é a entrada na faixa ALTA do PNUD; 0,800, na faixa MUITO ALTA.",
    )
    anos = anos_para_convergir(d, meta)
    if anos is None:
        st.caption("Série histórica insuficiente para projetar a convergência.")
    elif anos == 0:
        st.success(f"{d['uf']} já alcançou a meta de {n(meta)} em {d['ano']}.")
    else:
        rapido = anos <= 12
        classe = "bloco-destaque" if rapido else "bloco-alerta"
        abertura = (
            "<b>Meta ao alcance.</b>" if rapido
            else "<b>O ritmo atual não resolve.</b>"
        )
        fecho = (
            "O fundo aqui serve para antecipar e garantir o resultado, não para criar a trajetória."
            if rapido else
            "É esse horizonte que justifica um aporte concentrado e com prazo, em vez de "
            "esperar a convergência natural."
        )
        st.markdown(
            f"""<div class="{classe}">
            {abertura} Mantido o crescimento geométrico observado entre 1991 e {d['ano']}
            ({d['uf']} saiu de {n(float(d['serie']['idhm'].iloc[0]))} para {n(d['idhm'])}),
            o estado levaria cerca de <b>{anos:.0f} anos</b> a partir de {d['ano']} para
            alcançar um IDHM de {n(meta)}. {fecho}
            </div>""",
            unsafe_allow_html=True,
        )
        st.caption(
            "Projeção de tendência, não previsão: supõe que o ritmo de 1991–2010 se mantenha, "
            "o que ignora choques e o efeito de teto conforme o índice se aproxima de 1."
        )

    with st.expander("Frentes de política pública associadas às dimensões críticas"):
        from src.personas import ALAVANCAS, SIGNIFICADO
        for rotulo, chave in (
            ("Gargalo interno", d["dimensao_mais_fraca"]),
            ("Maior defasagem em relação ao país", d["dimensao_maior_defasagem"]),
        ):
            st.markdown(f"**{rotulo} — {NOME_DIMENSAO[chave]}**: mede {SIGNIFICADO[chave]}.")
            for item in ALAVANCAS[chave]:
                st.markdown(f"- {item}")
        st.caption(
            "As frentes são o encaminhamento da análise, não um resultado estatístico: "
            "o que o painel demonstra com número é ONDE está o problema e QUANTO ele custa em índice."
        )

    st.markdown("---")
    st.markdown("### Simulador do Fundo Regional")
    st.markdown(
        "O rateio segue um critério simples de explicar em audiência pública: **recebe quem "
        "está abaixo da referência, e recebe mais quem está mais longe dela**. Dentro de cada "
        "estado, o dinheiro se divide entre as três dimensões na proporção da lacuna de cada uma."
    )

    c1, c2 = st.columns(2)
    with c1:
        valor_bi = st.slider("Valor total do fundo (R$ bilhões)", 1.0, 50.0, 10.0, 0.5, key="fundo_valor")
        modo_ref = st.radio(
            "Referência de elegibilidade",
            ["Mediana nacional", "Média nacional", "Faixa Alta (0,700)", "Melhor UF"],
            key="fundo_ref", horizontal=False,
        )
    with c2:
        concentracao = st.slider(
            "Concentração do rateio", 1.0, 3.0, 1.0, 0.1, key="fundo_conc",
            help="1,0 = proporcional à lacuna. Acima de 1,0 concentra mais recurso nos estados mais distantes.",
        )
        teto = st.slider(
            "Teto por estado (% do fundo)", 0.10, 1.00, 0.35, 0.05, key="fundo_teto",
            help="Evita que um único estado absorva o fundo inteiro.",
        )

    referencias = {
        "Mediana nacional": float(df_filtrado["idhm"].median()),
        "Média nacional": float(df_filtrado["idhm"].mean()),
        "Faixa Alta (0,700)": 0.700,
        "Melhor UF": float(df_filtrado["idhm"].max()),
    }
    tabela, resumo = simular_fundo(
        df_filtrado, valor_bi * 1_000_000_000,
        referencia=referencias[modo_ref],
        concentracao=concentracao, teto_por_uf=teto,
    )

    if tabela.empty:
        st.info("Com essa referência, nenhuma UF do filtro é elegível ao fundo.")
        return

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Referência adotada", n(resumo["referencia"]), help=resumo["faixa_referencia"])
    c2.metric("UFs elegíveis", f"{resumo['n_elegiveis']} de {resumo['n_total']}")
    c3.metric("Fundo rateado", reais(resumo["total_rateado"]))
    c4.metric(
        "Maior cota",
        f"{n(tabela['cota_%'].max() * 100, 1)}%",
        help=f"Estado: {tabela.loc[tabela['cota_%'].idxmax(), 'uf']}",
    )

    st.markdown("**Para onde o dinheiro vai, por dimensão**")
    c1, c2, c3 = st.columns(3)
    c1.metric("Educação", reais(resumo["por_educacao"]))
    c2.metric("Renda", reais(resumo["por_renda"]))
    c3.metric("Longevidade", reais(resumo["por_longevidade"]))

    exibir = tabela.copy()
    exibir["cota_%"] = (exibir["cota_%"] * 100).round(2)
    for coluna in ["valor_R$", "para_educação_R$", "para_renda_R$", "para_longevidade_R$"]:
        exibir[coluna] = (exibir[coluna] / 1e6).round(1)
    st.dataframe(
        br_tabela(exibir, casas_por_coluna={
            "cota_%": 2, "valor_R$": 1, "para_educação_R$": 1,
            "para_renda_R$": 1, "para_longevidade_R$": 1,
        }).rename(columns={
            "prioridade": "Prioridade", "sigla_uf": "UF", "uf": "Estado",
            "regiao": "Região", "idhm": "IDHM", "lacuna_idhm": "Lacuna até a referência",
            "cota_%": "Cota (%)", "valor_R$": "Cota (R$ mi)",
            "para_educação_R$": "Educação (R$ mi)", "para_renda_R$": "Renda (R$ mi)",
            "para_longevidade_R$": "Longevidade (R$ mi)",
            "dimensao_mais_fraca": "Gargalo interno",
            "maior_defasagem": "Maior defasagem",
        }),
        use_container_width=True, hide_index=True,
    )
    st.download_button(
        "Baixar o rateio do fundo (CSV)",
        data=tabela.to_csv(index=False).encode("utf-8"),
        file_name=f"rateio_fundo_idhm_{f['ano']}.csv",
        mime="text/csv",
    )

    if escolhido in tabela["sigla_uf"].values:
        linha = tabela[tabela["sigla_uf"] == escolhido].iloc[0]
        st.markdown(
            f"""<div class="bloco-destaque">
            <b>Resposta direta a {PERSONAS[escolhido]['nome']}.</b> Com os parâmetros atuais,
            {linha['uf']} é prioridade <b>{int(linha['prioridade'])}</b> e recebe
            <b>{n(linha['cota_%'] * 100, 1)}%</b> do fundo —
            {reais(linha['valor_R$'])}, dos quais
            {reais(linha['para_educação_R$'])} para Educação,
            {reais(linha['para_renda_R$'])} para Renda e
            {reais(linha['para_longevidade_R$'])} para Longevidade.
            </div>""",
            unsafe_allow_html=True,
        )
    else:
        st.caption(
            f"{UF_NOME[escolhido]} não é elegível com a referência escolhida "
            "(o IDHM do estado já está acima dela)."
        )


def _aba_contexto() -> None:
    st.subheader("Contexto: o que é o IDHM e o que a imprensa tem mostrado")

    if (ASSETS / "idhm_composicao.png").exists():
        st.image(str(ASSETS / "idhm_composicao.png"), use_container_width=True)

    c1, c2 = st.columns(2, gap="large")
    with c1:
        st.markdown(
            """
            **Como o índice é construído**

            O IDHM adapta o IDH global do PNUD para a realidade brasileira, usando dados do
            Censo Demográfico do IBGE. As três dimensões têm o mesmo peso:

            - **Longevidade** — expectativa de vida ao nascer; resume saúde, saneamento e mortalidade.
            - **Educação** — escolaridade da população adulta e fluxo escolar da população jovem.
            - **Renda** — renda mensal por habitante, como proxy do padrão de vida.

            O índice final é a **média geométrica** das três, o que impede que um resultado
            muito bom em uma dimensão esconda um resultado muito ruim em outra.
            """
        )
    with c2:
        st.markdown(
            """
            **Faixas de desenvolvimento humano (PNUD)**

            | Faixa | Intervalo |
            |---|---|
            | Muito baixo | 0,000 – 0,499 |
            | Baixo | 0,500 – 0,599 |
            | Médio | 0,600 – 0,699 |
            | Alto | 0,700 – 0,799 |
            | Muito alto | 0,800 – 1,000 |

            **Fonte dos dados deste painel:** Atlas do Desenvolvimento Humano no Brasil
            (PNUD / Ipea / Fundação João Pinheiro), série dos Censos de 1991, 2000 e 2010.
            """
        )

    st.markdown("### Reportagens e fontes oficiais")
    noticias = _ler_noticias()
    if noticias.empty:
        st.info("Arquivo `dados/noticias.csv` não encontrado.")
        return

    tipos = noticias["tipo"].unique().tolist()
    escolha = st.radio("Mostrar", ["Tudo"] + tipos, horizontal=True, key="filtro_noticia")
    recorte = noticias if escolha == "Tudo" else noticias[noticias["tipo"] == escolha]

    for _, linha in recorte.iterrows():
        st.markdown(
            f"""<div class="cartao-noticia">
            <div class="veiculo">{linha['tipo']} · {linha['veiculo']}</div>
            <b>{linha['titulo']}</b><br>
            <span>{linha['resumo']}</span><br>
            <a href="{linha['link']}" target="_blank">{linha['link']}</a>
            </div>""",
            unsafe_allow_html=True,
        )

    st.caption(
        "A lista é lida de `dados/noticias.csv` — basta editar o arquivo para trocar as "
        "matérias sem mexer no código. Confirme título e data no veículo antes da apresentação."
    )

    with st.expander("Glossário rápido para a roda de conversa"):
        st.markdown(
            """
            - **Média geométrica** — raiz cúbica do produto das três dimensões. Penaliza o desequilíbrio.
            - **Quartis (Q1, Q2, Q3)** — dividem as UFs ordenadas em quatro grupos de tamanho igual.
            - **IQR (Q3 − Q1)** — faixa onde está a metade central dos estados; é a dispersão que não
              se deixa contaminar pelos extremos.
            - **Regra de 1,5 × IQR** — um valor é outlier se cair abaixo de Q1 − 1,5·IQR ou acima de
              Q3 + 1,5·IQR.
            - **Amplitude** — diferença entre o maior e o menor valor; mede a desigualdade total.
            - **Coeficiente de variação** — desvio padrão dividido pela média, em %. Permite comparar
              a desigualdade entre anos e entre dimensões de escalas diferentes.
            """
        )


# ---------------------------------------------------------------------------
# Ponto de entrada da seção
# ---------------------------------------------------------------------------

def renderizar_secao(usar_sidebar: bool = True, mostrar_cabecalho: bool = True) -> None:
    """Desenha a seção inteira. Use `usar_sidebar=False` para não criar filtros próprios."""
    _estilo()

    if mostrar_cabecalho:
        st.title(TITULO)
        st.markdown(f"<p style='font-size:1.03rem;color:#52514e'>{SUBTITULO}</p>",
                    unsafe_allow_html=True)

    enviado = None
    if usar_sidebar:
        st.sidebar.markdown("### Base de dados")
        arquivo = st.sidebar.file_uploader(
            "Enviar outra base de IDHM (.csv)",
            type=["csv"],
            help="Formato esperado: ';' como separador de colunas e ',' como decimal, "
                 "com as colunas ano, sigla, unidade_federativa, idhm e as três dimensões. "
                 "Sem envio, o painel usa a base do repositório.",
            key="upload_idhm",
        )
        if arquivo is not None:
            enviado = arquivo.getvalue()
            st.sidebar.success(f"Usando `{arquivo.name}`")
        else:
            st.sidebar.caption("Usando a base do repositório: `dados/raw/idhm_uf_bruto.csv`")

    try:
        dados, log = _carregar(enviado)
        bruto = _ler_bruto(enviado)
    except Exception as erro:  # arquivo enviado em formato incompatível
        st.error(
            "Não foi possível tratar o arquivo enviado. Verifique o separador de colunas (;), "
            f"o separador decimal (,) e os nomes das colunas.\n\nDetalhe técnico: `{erro}`"
        )
        return

    if usar_sidebar:
        f = montar_filtros(dados)
    else:  # dentro do painel do grupo: usa o ano mais recente e o país inteiro
        f = {
            "ano": int(dados["ano"].max()),
            "regioes": ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"],
            "ufs": sorted(dados["sigla_uf"].unique().tolist()),
            "indicador": "idhm",
            "destaques": list(PERSONAS),
        }

    df_ano = dados[dados["ano"] == f["ano"]].copy()
    df_filtrado = df_ano[
        df_ano["regiao"].isin(f["regioes"]) & df_ano["sigla_uf"].isin(f["ufs"])
    ].copy()

    if df_filtrado.empty:
        st.warning("Nenhuma UF selecionada. Ajuste os filtros na barra lateral.")
        return
    if len(df_filtrado) < len(df_ano):
        st.info(
            f"Filtro ativo: {len(df_filtrado)} de {len(df_ano)} UFs. As estatísticas desta "
            "seção são recalculadas sobre a seleção; o diagnóstico de cada gestor usa sempre "
            "as 27 UFs do ano, para que a posição no ranking continue comparável."
        )

    abas = st.tabs([
        "Panorama",
        "Dados & ETL",
        "Estatística descritiva",
        "As três dimensões",
        "Consultoria & Fundo",
        "Contexto & notícias",
    ])
    with abas[0]:
        _aba_visao_geral(df_ano, df_filtrado, f)
    with abas[1]:
        _aba_etl(bruto, log, dados)
    with abas[2]:
        _aba_estatistica(df_filtrado, f)
    with abas[3]:
        _aba_dimensoes(dados, df_ano, f)
    with abas[4]:
        _aba_consultoria(dados, df_ano, df_filtrado, f)
    with abas[5]:
        _aba_contexto()

    st.markdown(
        """<div class="rodape">
        <b>Números que Falam — Descobrindo o Brasil</b> · seção individual: IDH / IDHM ·
        Fonte: Atlas do Desenvolvimento Humano no Brasil (PNUD / Ipea / Fundação João Pinheiro),
        Censos Demográficos do IBGE de 1991, 2000 e 2010 ·
        Construído com Python, Pandas, NumPy, Plotly e Streamlit.
        </div>""",
        unsafe_allow_html=True,
    )
