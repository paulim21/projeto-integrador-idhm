"""
Gráficos do dashboard (Plotly).

Regras de visualização adotadas em todo o painel:

* uma paleta categórica fixa — cada dimensão do IDHM tem SEMPRE a mesma cor,
  em todos os gráficos (Educação = azul, Renda = laranja, Longevidade = verde-água);
* cor segue a entidade, nunca a posição no ranking;
* eixo único (nunca dois eixos y no mesmo gráfico);
* malha e eixos discretos, marcas finas, rótulos diretos só onde ajudam;
* todo gráfico tem camada de hover com os números exatos;
* texto sempre em tinta neutra — a cor fica só na marca.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go

# --- paleta ----------------------------------------------------------------
COR_EDUCACAO = "#2a78d6"     # slot 1 - azul
COR_RENDA = "#eb6834"        # slot 2 - laranja
COR_LONGEVIDADE = "#1baf7a"  # slot 3 - verde-água
COR_DESTAQUE = "#eb6834"
COR_NEUTRA = "#9ec5f4"
COR_BASE = "#2a78d6"

CORES_REGIAO = {
    "Norte": "#2a78d6",
    "Nordeste": "#eb6834",
    "Centro-Oeste": "#1baf7a",
    "Sudeste": "#eda100",
    "Sul": "#e87ba4",
}

CORES_DIMENSAO = {
    "idhm_educacao": COR_EDUCACAO,
    "idhm_renda": COR_RENDA,
    "idhm_longevidade": COR_LONGEVIDADE,
}

ROTULO_DIMENSAO = {
    "idhm": "IDHM geral",
    "idhm_educacao": "Educação",
    "idhm_renda": "Renda",
    "idhm_longevidade": "Longevidade",
}

TINTA_PRIMARIA = "#0b0b0b"
TINTA_SECUNDARIA = "#52514e"
MALHA = "rgba(11,11,11,0.08)"


def _base_layout(fig: go.Figure, altura: int = 420, titulo: str | None = None) -> go.Figure:
    fig.update_layout(
        height=altura,
        separators=",.",   # vírgula decimal e ponto de milhar, padrão brasileiro
        title=dict(text=titulo, font=dict(size=16, color=TINTA_PRIMARIA)) if titulo else None,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, Segoe UI, sans-serif", size=13, color=TINTA_SECUNDARIA),
        margin=dict(l=10, r=20, t=50 if titulo else 20, b=40),
        hoverlabel=dict(bgcolor="#fcfcfb", bordercolor=MALHA, font=dict(color=TINTA_PRIMARIA)),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, font=dict(color=TINTA_SECUNDARIA)),
    )
    fig.update_xaxes(showgrid=True, gridcolor=MALHA, zeroline=False, linecolor=MALHA)
    fig.update_yaxes(showgrid=True, gridcolor=MALHA, zeroline=False, linecolor=MALHA)
    return fig


# ---------------------------------------------------------------------------
# 1. Ranking das UFs (barras horizontais) — magnitude + identidade
# ---------------------------------------------------------------------------

def grafico_ranking(df: pd.DataFrame, coluna: str = "idhm", destaques: list[str] | None = None) -> go.Figure:
    destaques = destaques or []
    dados = df.sort_values(coluna, ascending=True)
    cores = [COR_DESTAQUE if s in destaques else COR_NEUTRA for s in dados["sigla_uf"]]

    fig = go.Figure(
        go.Bar(
            x=dados[coluna],
            y=dados["uf"],
            orientation="h",
            marker=dict(color=cores, line=dict(width=0)),
            text=[f"{v:.3f}".replace(".", ",") for v in dados[coluna]],
            textposition="outside",
            textfont=dict(size=11, color=TINTA_SECUNDARIA),
            customdata=np.stack([dados["regiao"], dados["faixa_idhm"]], axis=-1),
            hovertemplate="<b>%{y}</b><br>" + ROTULO_DIMENSAO.get(coluna, coluna)
            + ": %{x:.3f}<br>Região: %{customdata[0]}<br>Faixa: %{customdata[1]}<extra></extra>",
            showlegend=False,
        )
    )
    media = df[coluna].mean()
    fig.add_vline(
        x=media, line=dict(color=TINTA_SECUNDARIA, width=1, dash="dot"),
        annotation_text=f"média {media:.3f}".replace(".", ","),
        annotation_position="top",
        annotation_font=dict(size=11, color=TINTA_SECUNDARIA),
    )
    fig.update_xaxes(range=[0, min(1.0, float(df[coluna].max()) + 0.12)], title=None)
    fig.update_yaxes(title=None, tickfont=dict(size=11))
    return _base_layout(fig, altura=720)


# ---------------------------------------------------------------------------
# 2. Boxplot das três dimensões — dispersão e outliers (1,5 x IQR)
# ---------------------------------------------------------------------------

def grafico_boxplot_dimensoes(df: pd.DataFrame, destaques: list[str] | None = None) -> go.Figure:
    destaques = destaques or []
    fig = go.Figure()
    for coluna, cor in CORES_DIMENSAO.items():
        fig.add_trace(
            go.Box(
                y=df[coluna],
                name=ROTULO_DIMENSAO[coluna],
                marker=dict(color=cor, outliercolor=cor, size=7),
                line=dict(color=cor, width=2),
                fillcolor="rgba(0,0,0,0)",
                boxpoints="outliers",
                text=df["uf"],
                hovertemplate="<b>%{text}</b><br>%{y:.3f}<extra></extra>",
            )
        )
    # UFs das personas sobrepostas como pontos, para leitura direta do gestor
    if destaques:
        marcados = df[df["sigla_uf"].isin(destaques)]
        for coluna in CORES_DIMENSAO:
            fig.add_trace(
                go.Scatter(
                    x=[ROTULO_DIMENSAO[coluna]] * len(marcados),
                    y=marcados[coluna],
                    mode="markers+text",
                    marker=dict(color=COR_DESTAQUE, size=10, line=dict(color="#fcfcfb", width=2)),
                    text=marcados["sigla_uf"],
                    textposition="middle right",
                    textfont=dict(size=10, color=TINTA_PRIMARIA),
                    hovertemplate="<b>%{text}</b><br>%{y:.3f}<extra></extra>",
                    showlegend=False,
                )
            )
    fig.update_yaxes(title="Índice (0 a 1)", range=[0, 1])
    return _base_layout(fig, altura=460)


# ---------------------------------------------------------------------------
# 3. Boxplot por região — compara blocos do país
# ---------------------------------------------------------------------------

def grafico_boxplot_regioes(df: pd.DataFrame, coluna: str = "idhm") -> go.Figure:
    ordem = (
        df.groupby("regiao")[coluna].median().sort_values(ascending=False).index.tolist()
    )
    fig = go.Figure()
    for regiao in ordem:
        recorte = df[df["regiao"] == regiao]
        fig.add_trace(
            go.Box(
                y=recorte[coluna],
                name=regiao,
                marker=dict(color=CORES_REGIAO.get(regiao, COR_BASE), size=7),
                line=dict(color=CORES_REGIAO.get(regiao, COR_BASE), width=2),
                fillcolor="rgba(0,0,0,0)",
                boxpoints="all",
                jitter=0.4,
                pointpos=0,
                text=recorte["uf"],
                hovertemplate="<b>%{text}</b><br>%{y:.3f}<extra></extra>",
            )
        )
    fig.update_yaxes(title=ROTULO_DIMENSAO.get(coluna, coluna))
    return _base_layout(fig, altura=430)


# ---------------------------------------------------------------------------
# 4. Histograma — forma da distribuição
# ---------------------------------------------------------------------------

def grafico_histograma(df: pd.DataFrame, coluna: str = "idhm", bins: int = 8,
                       rotulo_y: str = "Nº de UFs") -> go.Figure:
    valores = df[coluna].dropna()
    fig = go.Figure(
        go.Histogram(
            x=valores,
            nbinsx=bins,
            marker=dict(color=CORES_DIMENSAO.get(coluna, COR_BASE), line=dict(color="#fcfcfb", width=2)),
            hovertemplate="Faixa: %{x}<br>UFs: %{y}<extra></extra>",
            showlegend=False,
        )
    )
    for valor, rotulo, tracejado in (
        (valores.mean(), "média", "dot"),
        (valores.median(), "mediana", "dash"),
    ):
        fig.add_vline(
            x=valor, line=dict(color=TINTA_PRIMARIA, width=1, dash=tracejado),
            annotation_text=f"{rotulo} {valor:.3f}".replace(".", ","),
            annotation_position="top",
            annotation_font=dict(size=11, color=TINTA_SECUNDARIA),
        )
    fig.update_xaxes(title=ROTULO_DIMENSAO.get(coluna, coluna))
    fig.update_yaxes(title=rotulo_y)
    return _base_layout(fig, altura=400)


# ---------------------------------------------------------------------------
# 5. Evolução histórica (linhas) — mudança no tempo
# ---------------------------------------------------------------------------

def grafico_evolucao(
    df_completo: pd.DataFrame, siglas: list[str], coluna: str = "idhm",
    media_brasil: bool = True, rotulo_x: str = "Censo"
) -> go.Figure:
    fig = go.Figure()

    if media_brasil:
        media = df_completo.groupby("ano")[coluna].mean().reset_index()
        fig.add_trace(
            go.Scatter(
                x=media["ano"], y=media[coluna],
                mode="lines", name="Média das 27 UFs",
                line=dict(color=TINTA_SECUNDARIA, width=2, dash="dot"),
                hovertemplate="Média das UFs — %{x}: %{y:.3f}<extra></extra>",
            )
        )

    paleta = [COR_EDUCACAO, COR_RENDA, COR_LONGEVIDADE, "#eda100", "#e87ba4"]
    for i, sigla in enumerate(siglas[:5]):
        serie = df_completo[df_completo["sigla_uf"] == sigla].sort_values("ano")
        if serie.empty:
            continue
        nome = serie["uf"].iloc[0]
        fig.add_trace(
            go.Scatter(
                x=serie["ano"], y=serie[coluna],
                mode="lines+markers+text", name=nome,
                line=dict(color=paleta[i % len(paleta)], width=2),
                marker=dict(size=9, line=dict(color="#fcfcfb", width=2)),
                text=[""] * (len(serie) - 1) + [f" {serie[coluna].iloc[-1]:.3f}".replace(".", ",")],
                textposition="middle right",
                textfont=dict(size=11, color=TINTA_SECUNDARIA),
                hovertemplate=f"<b>{nome}</b> — %{{x}}: %{{y:.3f}}<extra></extra>",
            )
        )
    fig.update_xaxes(title=rotulo_x, tickvals=sorted(df_completo["ano"].unique()))
    fig.update_yaxes(title=ROTULO_DIMENSAO.get(coluna, coluna), range=[0, 1])
    fig.update_layout(hovermode="x unified")
    return _base_layout(fig, altura=430)


# ---------------------------------------------------------------------------
# 6. Perfil das três dimensões por UF (barras agrupadas)
# ---------------------------------------------------------------------------

def grafico_perfil_dimensoes(df: pd.DataFrame, siglas: list[str]) -> go.Figure:
    recorte = df[df["sigla_uf"].isin(siglas)].sort_values("idhm", ascending=False)
    fig = go.Figure()
    for coluna, cor in CORES_DIMENSAO.items():
        fig.add_trace(
            go.Bar(
                x=recorte["uf"], y=recorte[coluna],
                name=ROTULO_DIMENSAO[coluna],
                marker=dict(color=cor, line=dict(color="#fcfcfb", width=2)),
                text=[f"{v:.3f}".replace(".", ",") for v in recorte[coluna]],
                textposition="outside",
                textfont=dict(size=10, color=TINTA_SECUNDARIA),
                hovertemplate="<b>%{x}</b><br>" + ROTULO_DIMENSAO[coluna] + ": %{y:.3f}<extra></extra>",
            )
        )
    fig.update_layout(barmode="group", bargap=0.3, bargroupgap=0.08)
    fig.update_yaxes(title="Índice (0 a 1)", range=[0, 1.05])
    fig.update_xaxes(title=None)
    return _base_layout(fig, altura=450)


# ---------------------------------------------------------------------------
# 7. Lacuna até a referência (lollipop) — quanto falta para a meta
# ---------------------------------------------------------------------------

def grafico_lacuna(df: pd.DataFrame, coluna: str, referencia: float, destaques: list[str] | None = None) -> go.Figure:
    destaques = destaques or []
    dados = df.sort_values(coluna, ascending=True).copy()
    dados["lacuna"] = (referencia - dados[coluna]).clip(lower=0)

    fig = go.Figure()
    for _, linha in dados.iterrows():
        cor = COR_DESTAQUE if linha["sigla_uf"] in destaques else COR_NEUTRA
        fig.add_trace(
            go.Scatter(
                x=[linha[coluna], referencia], y=[linha["uf"], linha["uf"]],
                mode="lines", line=dict(color=cor, width=3),
                hoverinfo="skip", showlegend=False,
            )
        )
    cores = [COR_DESTAQUE if s in destaques else COR_BASE for s in dados["sigla_uf"]]
    fig.add_trace(
        go.Scatter(
            x=dados[coluna], y=dados["uf"], mode="markers",
            marker=dict(color=cores, size=10, line=dict(color="#fcfcfb", width=2)),
            customdata=dados["lacuna"],
            hovertemplate="<b>%{y}</b><br>Valor: %{x:.3f}<br>Falta para a referência: %{customdata:.3f}<extra></extra>",
            showlegend=False,
        )
    )
    fig.add_vline(
        x=referencia, line=dict(color=TINTA_PRIMARIA, width=1, dash="dash"),
        annotation_text=f"referência {referencia:.3f}".replace(".", ","),
        annotation_position="top",
        annotation_font=dict(size=11, color=TINTA_SECUNDARIA),
    )
    fig.update_xaxes(title=ROTULO_DIMENSAO.get(coluna, coluna), range=[0, 1])
    fig.update_yaxes(title=None, tickfont=dict(size=11))
    return _base_layout(fig, altura=720)


# ---------------------------------------------------------------------------
# 8. Dispersão Educação x Renda (identidade por região, 3 grupos no máximo)
# ---------------------------------------------------------------------------

def grafico_dispersao(df: pd.DataFrame, destaques: list[str] | None = None) -> go.Figure:
    destaques = destaques or []
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["idhm_educacao"], y=df["idhm_renda"],
            mode="markers",
            marker=dict(
                color=COR_NEUTRA, size=12, line=dict(color="#fcfcfb", width=2),
            ),
            text=df["uf"],
            customdata=np.stack([df["sigla_uf"], df["idhm"]], axis=-1),
            hovertemplate="<b>%{text}</b><br>Educação: %{x:.3f}<br>Renda: %{y:.3f}"
            "<br>IDHM: %{customdata[1]:.3f}<extra></extra>",
            name="Demais UFs",
        )
    )
    marcados = df[df["sigla_uf"].isin(destaques)]
    if not marcados.empty:
        fig.add_trace(
            go.Scatter(
                x=marcados["idhm_educacao"], y=marcados["idhm_renda"],
                mode="markers+text",
                marker=dict(color=COR_DESTAQUE, size=14, line=dict(color="#fcfcfb", width=2)),
                text=marcados["sigla_uf"], textposition="top center",
                textfont=dict(size=11, color=TINTA_PRIMARIA),
                hovertemplate="<b>%{text}</b><br>Educação: %{x:.3f}<br>Renda: %{y:.3f}<extra></extra>",
                name="Estados atendidos",
            )
        )
    fig.update_xaxes(title="IDHM Educação")
    fig.update_yaxes(title="IDHM Renda")
    return _base_layout(fig, altura=430)


# ---------------------------------------------------------------------------
# 9. Radar (aranha) dos três subíndices — comparação de perfil entre estados
# ---------------------------------------------------------------------------

PALETA_ESTADOS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]


def grafico_radar(df: pd.DataFrame, siglas: list[str], mostrar_media: bool = True) -> go.Figure:
    """
    Radar dos subíndices do IDHM (Educação, Renda, Longevidade) por estado.

    O radar mostra o FORMATO do desenvolvimento humano de cada UF: um triângulo
    equilibrado indica as três dimensões no mesmo patamar; um triângulo puxado
    para dentro em um vértice mostra qual dimensão está travando o índice.
    """
    eixos = ["idhm_educacao", "idhm_renda", "idhm_longevidade"]
    rotulos = [ROTULO_DIMENSAO[c] for c in eixos]
    fig = go.Figure()

    if mostrar_media:
        medias = [float(df[c].mean()) for c in eixos]
        fig.add_trace(
            go.Scatterpolar(
                r=medias + [medias[0]],
                theta=rotulos + [rotulos[0]],
                name="Média das 27 UFs",
                mode="lines",
                line=dict(color=TINTA_SECUNDARIA, width=2, dash="dot"),
                hovertemplate="Média das UFs<br>%{theta}: %{r:.3f}<extra></extra>",
            )
        )

    recorte = df[df["sigla_uf"].isin(siglas)].sort_values("idhm", ascending=False)
    for i, (_, linha) in enumerate(recorte.iterrows()):
        valores = [float(linha[c]) for c in eixos]
        cor = PALETA_ESTADOS[i % len(PALETA_ESTADOS)]
        nome = str(linha["uf"]) + " (" + f"{linha['idhm']:.3f}".replace(".", ",") + ")"
        fig.add_trace(
            go.Scatterpolar(
                r=valores + [valores[0]],
                theta=rotulos + [rotulos[0]],
                name=nome,
                mode="lines+markers",
                line=dict(color=cor, width=2),
                marker=dict(size=8, line=dict(color="#fcfcfb", width=2)),
                hovertemplate="<b>" + str(linha["uf"]) + "</b><br>%{theta}: %{r:.3f}<extra></extra>",
            )
        )

    minimo = max(0.0, float(recorte[eixos].min().min()) - 0.15) if not recorte.empty else 0.0
    fig.update_layout(
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(
                visible=True, range=[minimo, 1.0], tickformat=".2f",
                gridcolor=MALHA, linecolor=MALHA,
                tickfont=dict(size=10, color=TINTA_SECUNDARIA),
            ),
            angularaxis=dict(
                gridcolor=MALHA, linecolor=MALHA,
                tickfont=dict(size=13, color=TINTA_PRIMARIA),
            ),
            # folga para os rótulos dos três eixos não serem cortados
            domain=dict(x=[0.12, 0.88], y=[0.02, 0.88]),
        ),
    )
    fig = _base_layout(fig, altura=560)
    fig.update_layout(margin=dict(l=40, r=40, t=70, b=40))
    return fig


# ---------------------------------------------------------------------------
# 10. Boxplot municipal por UF — dispersão DENTRO de cada estado
# ---------------------------------------------------------------------------

def grafico_boxplot_municipal(df_mun: pd.DataFrame, coluna: str = "idhm",
                              destaques: list[str] | None = None) -> go.Figure:
    """Um boxplot por UF, construído sobre os municípios daquele estado."""
    destaques = destaques or []
    ordem = df_mun.groupby("sigla_uf")[coluna].median().sort_values(ascending=False).index.tolist()

    fig = go.Figure()
    for sigla in ordem:
        recorte = df_mun[df_mun["sigla_uf"] == sigla]
        cor = COR_DESTAQUE if sigla in destaques else CORES_REGIAO.get(
            recorte["regiao"].iloc[0], COR_BASE
        )
        fig.add_trace(
            go.Box(
                y=recorte[coluna],
                name=sigla,
                marker=dict(color=cor, outliercolor=cor, size=4),
                line=dict(color=cor, width=1.6),
                fillcolor="rgba(0,0,0,0)",
                boxpoints="outliers",
                text=recorte["municipio"],
                hovertemplate="<b>%{text}</b><br>%{y:.3f}<extra></extra>",
                showlegend=False,
            )
        )
    fig.update_yaxes(title=ROTULO_DIMENSAO.get(coluna, coluna))
    fig.update_xaxes(title="Unidade da Federação", tickfont=dict(size=11))
    return _base_layout(fig, altura=480)


# ---------------------------------------------------------------------------
# 11. Extremos municipais — maiores e menores índices
# ---------------------------------------------------------------------------

def grafico_extremos_municipios(df_mun: pd.DataFrame, coluna: str = "idhm",
                                n: int = 10) -> go.Figure:
    """Barras horizontais com os n municípios de maior e de menor índice."""
    ordenado = df_mun.sort_values(coluna)
    piores = ordenado.head(n)
    melhores = ordenado.tail(n)
    dados = pd.concat([piores, melhores])
    rotulo = dados["municipio"] + " (" + dados["sigla_uf"] + ")"
    cores = [COR_DESTAQUE] * len(piores) + [COR_BASE] * len(melhores)

    fig = go.Figure(
        go.Bar(
            x=dados[coluna], y=rotulo, orientation="h",
            marker=dict(color=cores, line=dict(width=0)),
            text=[f"{v:.3f}".replace(".", ",") for v in dados[coluna]],
            textposition="outside",
            textfont=dict(size=11, color=TINTA_SECUNDARIA),
            customdata=np.stack([dados["faixa_idhm"], dados["populacao"]], axis=-1),
            hovertemplate="<b>%{y}</b><br>" + ROTULO_DIMENSAO.get(coluna, coluna)
            + ": %{x:.3f}<br>Faixa: %{customdata[0]}"
            + "<br>População: %{customdata[1]:,}<extra></extra>",
            showlegend=False,
        )
    )
    mediana = float(df_mun[coluna].median())
    fig.add_vline(
        x=mediana, line=dict(color=TINTA_SECUNDARIA, width=1, dash="dot"),
        annotation_text=f"mediana dos municípios {mediana:.3f}".replace(".", ","),
        annotation_position="top", annotation_font=dict(size=11, color=TINTA_SECUNDARIA),
    )
    fig.update_xaxes(range=[0, 1.08], title=ROTULO_DIMENSAO.get(coluna, coluna))
    fig.update_yaxes(title=None, tickfont=dict(size=11))
    return _base_layout(fig, altura=620)


# ---------------------------------------------------------------------------
# 12. Dispersão IDHM x investimento público, com reta de tendência
# ---------------------------------------------------------------------------

def grafico_dispersao_investimento(df: pd.DataFrame, coluna_x: str,
                                   coluna_y: str = "idhm",
                                   destaques: list[str] | None = None):
    """
    Correlaciona o IDHM com o gasto público por habitante.

    Devolve (figura, estatísticas), com o coeficiente de correlação de Pearson
    e os parâmetros da reta ajustada por mínimos quadrados.
    """
    destaques = destaques or []
    dados = df.dropna(subset=[coluna_x, coluna_y]).copy()
    x = dados[coluna_x].astype(float).to_numpy()
    y = dados[coluna_y].astype(float).to_numpy()

    estat = {"n": int(len(x))}
    fig = go.Figure()

    if len(x) >= 3:
        correlacao = float(np.corrcoef(x, y)[0, 1])
        coef = np.polyfit(x, y, 1)
        linha_x = np.linspace(x.min(), x.max(), 50)
        estat.update({
            "correlacao": correlacao,
            "r2": correlacao ** 2,
            "inclinacao": float(coef[0]),
            "intercepto": float(coef[1]),
        })
        fig.add_trace(
            go.Scatter(
                x=linha_x, y=np.polyval(coef, linha_x),
                mode="lines", name="Tendência (mínimos quadrados)",
                line=dict(color=TINTA_SECUNDARIA, width=2, dash="dash"),
                hoverinfo="skip",
            )
        )

    comuns = dados[~dados["sigla_uf"].isin(destaques)]
    fig.add_trace(
        go.Scatter(
            x=comuns[coluna_x], y=comuns[coluna_y], mode="markers",
            marker=dict(color=COR_NEUTRA, size=12, line=dict(color="#fcfcfb", width=2)),
            text=comuns["uf"], name="Demais UFs",
            hovertemplate="<b>%{text}</b><br>Gasto por habitante: R$ %{x:,.0f}"
                          "<br>IDHM: %{y:.3f}<extra></extra>",
        )
    )
    marcados = dados[dados["sigla_uf"].isin(destaques)]
    if not marcados.empty:
        fig.add_trace(
            go.Scatter(
                x=marcados[coluna_x], y=marcados[coluna_y],
                mode="markers+text",
                marker=dict(color=COR_DESTAQUE, size=14, line=dict(color="#fcfcfb", width=2)),
                text=marcados["sigla_uf"], textposition="top center",
                textfont=dict(size=11, color=TINTA_PRIMARIA),
                name="Estados atendidos",
                hovertemplate="<b>%{text}</b><br>Gasto por habitante: R$ %{x:,.0f}"
                              "<br>IDHM: %{y:.3f}<extra></extra>",
            )
        )

    fig.update_xaxes(title="Gasto público estadual por habitante (R$)")
    fig.update_yaxes(title=ROTULO_DIMENSAO.get(coluna_y, coluna_y))
    return _base_layout(fig, altura=460), estat
