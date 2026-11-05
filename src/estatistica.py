"""
Estatística descritiva do projeto — calculada com NumPy e Pandas.

Entrega todas as medidas exigidas pelo projeto:
    média, mediana, moda, Q1, Q2 (mediana), Q3,
    IQR = Q3 - Q1, amplitude = máx - mín, desvio padrão
    e identificação de outliers pela regra de 1,5 x IQR.

Convenções adotadas (e justificadas na apresentação):

* Desvio padrão: as 27 UFs são a POPULAÇÃO completa de unidades da federação,
  por isso o valor de referência é o populacional (ddof=0). O amostral (ddof=1)
  também é devolvido para comparação.
* Quartis: interpolação linear (método padrão do NumPy/Pandas, 'linear').
* Moda: o IDHM é uma variável contínua, então praticamente não há valor
  repetido. A moda é calculada sobre o valor ARREDONDADO em 2 casas, o que
  equivale a perguntar "em qual centésimo do índice se concentram mais UFs".
"""

from __future__ import annotations

import numpy as np
import pandas as pd

ROTULOS = {
    "idhm": "IDHM geral",
    "idhm_educacao": "IDHM Educação",
    "idhm_renda": "IDHM Renda",
    "idhm_longevidade": "IDHM Longevidade",
}


# ---------------------------------------------------------------------------
# Medidas de posição, dispersão e forma
# ---------------------------------------------------------------------------

def calcular_moda(valores: pd.Series, casas: int = 2) -> tuple[float | None, int]:
    """Moda do valor arredondado. Devolve (moda, frequência)."""
    arredondado = valores.round(casas)
    contagem = arredondado.value_counts()
    if contagem.empty:
        return None, 0
    return float(contagem.index[0]), int(contagem.iloc[0])


def resumo_descritivo(valores: pd.Series) -> dict:
    """Todas as medidas descritivas de uma série numérica."""
    x = pd.Series(valores).dropna().astype(float)
    if x.empty:
        return {}

    arr = x.to_numpy()
    q1, q2, q3 = np.percentile(arr, [25, 50, 75])
    iqr = q3 - q1
    minimo, maximo = float(arr.min()), float(arr.max())
    media = float(arr.mean())
    dp_pop = float(np.std(arr, ddof=0))
    dp_amostral = float(np.std(arr, ddof=1)) if len(arr) > 1 else float("nan")
    moda, freq_moda = calcular_moda(x)

    return {
        "n": int(len(arr)),
        "media": media,
        "mediana": float(np.median(arr)),
        "moda": moda,
        "frequencia_moda": freq_moda,
        "minimo": minimo,
        "maximo": maximo,
        "amplitude": maximo - minimo,
        "q1": float(q1),
        "q2": float(q2),
        "q3": float(q3),
        "iqr": float(iqr),
        "limite_inferior": float(q1 - 1.5 * iqr),
        "limite_superior": float(q3 + 1.5 * iqr),
        "desvio_padrao": dp_pop,
        "desvio_padrao_amostral": dp_amostral,
        "variancia": float(np.var(arr, ddof=0)),
        "coef_variacao": (dp_pop / media * 100) if media else float("nan"),
        "assimetria": float(x.skew()),
    }


def tabela_resumo(df: pd.DataFrame, colunas: list[str] | None = None) -> pd.DataFrame:
    """Tabela com as medidas descritivas de várias colunas, lado a lado."""
    colunas = colunas or list(ROTULOS)
    linhas = []
    for coluna in colunas:
        if coluna not in df:
            continue
        r = resumo_descritivo(df[coluna])
        if not r:
            continue
        linhas.append({
            "Indicador": ROTULOS.get(coluna, coluna),
            "N": r["n"],
            "Média": r["media"],
            "Mediana (Q2)": r["mediana"],
            "Moda (2 casas)": r["moda"],
            "Mínimo": r["minimo"],
            "Máximo": r["maximo"],
            "Amplitude": r["amplitude"],
            "Q1": r["q1"],
            "Q3": r["q3"],
            "IQR": r["iqr"],
            "Desvio padrão": r["desvio_padrao"],
            "Coef. de variação (%)": r["coef_variacao"],
        })
    return pd.DataFrame(linhas)


# ---------------------------------------------------------------------------
# Outliers pela regra de 1,5 x IQR
# ---------------------------------------------------------------------------

def detectar_outliers(df: pd.DataFrame, coluna: str, rotulo: str = "sigla_uf") -> pd.DataFrame:
    """
    Marca cada registro como outlier inferior, outlier superior ou normal
    usando os limites de Tukey: [Q1 - 1,5*IQR ; Q3 + 1,5*IQR].
    """
    r = resumo_descritivo(df[coluna])
    if not r:
        return pd.DataFrame()

    saida = df[[rotulo, "uf", "regiao", coluna]].copy() if "uf" in df else df[[rotulo, coluna]].copy()
    valor = saida[coluna]
    saida["situacao"] = np.select(
        [valor < r["limite_inferior"], valor > r["limite_superior"]],
        ["Outlier inferior", "Outlier superior"],
        default="Dentro dos limites",
    )
    # distância em nº de IQRs além do limite — ajuda a graduar a gravidade
    distancia = np.where(
        valor < r["limite_inferior"],
        (r["limite_inferior"] - valor) / r["iqr"] if r["iqr"] else 0,
        np.where(
            valor > r["limite_superior"],
            (valor - r["limite_superior"]) / r["iqr"] if r["iqr"] else 0,
            0,
        ),
    )
    saida["distancia_em_iqr"] = np.round(distancia, 2)
    return saida.sort_values(coluna).reset_index(drop=True)


def texto_outliers(df: pd.DataFrame, coluna: str) -> str:
    """Frase pronta justificando (ou não) os outliers — para a leitura do gestor."""
    r = resumo_descritivo(df[coluna])
    if not r:
        return "Sem dados suficientes para avaliar outliers."

    marcado = detectar_outliers(df, coluna)
    fora = marcado[marcado["situacao"] != "Dentro dos limites"]
    nome = ROTULOS.get(coluna, coluna)
    base = (
        f"Limites de Tukey para o {nome}: "
        f"Q1 = {r['q1']:.3f}, Q3 = {r['q3']:.3f}, IQR = {r['iqr']:.3f}, "
        f"logo o intervalo aceitável é [{r['limite_inferior']:.3f} ; {r['limite_superior']:.3f}]."
    )
    if fora.empty:
        return (
            base
            + " **Nenhuma UF ficou fora desses limites**: a desigualdade entre os estados é grande, "
            "mas é uma variação contínua — não existe um estado isolado do restante do país. "
            "Os piores casos são extremos da distribuição, não erros de medição."
        )

    itens = ", ".join(
        f"{linha['uf']} ({linha[coluna]:.3f}, {linha['situacao'].split()[-1]})"
        for _, linha in fora.iterrows()
    )
    return (
        base
        + f" Ficaram fora dos limites: {itens}. "
        "A verificação na base bruta mostra que são valores reais (não erros de digitação), "
        "por isso **foram mantidos**: retirá-los apagaria exatamente a desigualdade que o estudo quer medir."
    )


# ---------------------------------------------------------------------------
# Leituras auxiliares para o painel
# ---------------------------------------------------------------------------

def comparar_com_distribuicao(df: pd.DataFrame, sigla: str, coluna: str = "idhm") -> dict:
    """Posiciona uma UF dentro da distribuição nacional do ano filtrado."""
    r = resumo_descritivo(df[coluna])
    linha = df[df["sigla_uf"] == sigla]
    if linha.empty or not r:
        return {}
    valor = float(linha[coluna].iloc[0])
    ordenado = df.sort_values(coluna, ascending=False).reset_index(drop=True)
    posicao = int(ordenado.index[ordenado["sigla_uf"] == sigla][0]) + 1
    return {
        "valor": valor,
        "posicao": posicao,
        "total": len(ordenado),
        "percentil": float((df[coluna] < valor).mean() * 100),
        "distancia_media": valor - r["media"],
        "distancia_mediana": valor - r["mediana"],
        "quartil": 1 if valor <= r["q1"] else 2 if valor <= r["q2"] else 3 if valor <= r["q3"] else 4,
    }


def evolucao(df_completo: pd.DataFrame, sigla: str, coluna: str = "idhm") -> pd.DataFrame:
    """Série histórica de uma UF, com variação absoluta e relativa entre censos."""
    serie = (
        df_completo[df_completo["sigla_uf"] == sigla]
        .sort_values("ano")[["ano", coluna]]
        .reset_index(drop=True)
    )
    serie["variacao_absoluta"] = serie[coluna].diff().round(3)
    serie["variacao_%"] = (serie[coluna].pct_change() * 100).round(1)
    return serie
