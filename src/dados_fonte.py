"""
Base de referência do IDHM por Unidade da Federação.

Fonte primária: Atlas do Desenvolvimento Humano no Brasil (PNUD / Ipea / FJP),
série dos Censos Demográficos do IBGE de 1991, 2000 e 2010 — a série oficial
comparável do IDHM por UF.

Cada registro traz as TRÊS dimensões que compõem o índice:
    - educacao     -> IDHM Educação
    - renda        -> IDHM Renda
    - longevidade  -> IDHM Longevidade

O IDHM total é a MÉDIA GEOMÉTRICA das três dimensões:

    IDHM = (IDHM_Educacao * IDHM_Renda * IDHM_Longevidade) ** (1/3)

Os valores abaixo foram conferidos um a um: a média geométrica das três
dimensões reproduz o IDHM publicado para as 27 UFs nos 3 anos (erro <= 0,001).
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Metadados geográficos
# ---------------------------------------------------------------------------

UF_NOME = {
    "AC": "Acre",
    "AL": "Alagoas",
    "AP": "Amapá",
    "AM": "Amazonas",
    "BA": "Bahia",
    "CE": "Ceará",
    "DF": "Distrito Federal",
    "ES": "Espírito Santo",
    "GO": "Goiás",
    "MA": "Maranhão",
    "MT": "Mato Grosso",
    "MS": "Mato Grosso do Sul",
    "MG": "Minas Gerais",
    "PA": "Pará",
    "PB": "Paraíba",
    "PR": "Paraná",
    "PE": "Pernambuco",
    "PI": "Piauí",
    "RJ": "Rio de Janeiro",
    "RN": "Rio Grande do Norte",
    "RS": "Rio Grande do Sul",
    "RO": "Rondônia",
    "RR": "Roraima",
    "SC": "Santa Catarina",
    "SP": "São Paulo",
    "SE": "Sergipe",
    "TO": "Tocantins",
}

UF_REGIAO = {
    "AC": "Norte", "AP": "Norte", "AM": "Norte", "PA": "Norte",
    "RO": "Norte", "RR": "Norte", "TO": "Norte",
    "AL": "Nordeste", "BA": "Nordeste", "CE": "Nordeste", "MA": "Nordeste",
    "PB": "Nordeste", "PE": "Nordeste", "PI": "Nordeste", "RN": "Nordeste",
    "SE": "Nordeste",
    "DF": "Centro-Oeste", "GO": "Centro-Oeste", "MT": "Centro-Oeste",
    "MS": "Centro-Oeste",
    "ES": "Sudeste", "MG": "Sudeste", "RJ": "Sudeste", "SP": "Sudeste",
    "PR": "Sul", "RS": "Sul", "SC": "Sul",
}

# ---------------------------------------------------------------------------
# Personas atendidas pela consultoria (gestores públicos do projeto)
# ---------------------------------------------------------------------------

PERSONAS = {
    "MA": {"nome": "João", "cargo": "Governador do Maranhão"},
    "PA": {"nome": "Helder", "cargo": "Governador do Pará"},
    "AC": {"nome": "Gladson", "cargo": "Governador do Acre"},
    "BA": {"nome": "Susu", "cargo": "Governador da Bahia"},
    "MG": {"nome": "Verinha", "cargo": "Governadora de Minas Gerais"},
}

# ---------------------------------------------------------------------------
# Dados: {ano: {sigla_uf: (educacao, renda, longevidade)}}
# ---------------------------------------------------------------------------

IDHM_DIMENSOES = {
    1991: {
        "DF": (0.419, 0.762, 0.731),
        "SP": (0.363, 0.729, 0.730),
        "SC": (0.329, 0.648, 0.753),
        "RJ": (0.392, 0.696, 0.690),
        "RS": (0.328, 0.667, 0.729),
        "PR": (0.298, 0.644, 0.679),
        "ES": (0.304, 0.619, 0.686),
        "MS": (0.259, 0.641, 0.699),
        "GO": (0.273, 0.633, 0.668),
        "MG": (0.257, 0.618, 0.689),
        "RR": (0.240, 0.643, 0.628),
        "MT": (0.221, 0.627, 0.654),
        "AP": (0.254, 0.620, 0.668),
        "PE": (0.232, 0.569, 0.617),
        "AM": (0.204, 0.605, 0.645),
        "RN": (0.242, 0.547, 0.591),
        "SE": (0.211, 0.552, 0.581),
        "PA": (0.194, 0.567, 0.640),
        "RO": (0.181, 0.585, 0.635),
        "CE": (0.204, 0.532, 0.613),
        "AC": (0.176, 0.574, 0.645),
        "BA": (0.182, 0.543, 0.582),
        "PB": (0.191, 0.515, 0.565),
        "AL": (0.174, 0.527, 0.552),
        "TO": (0.155, 0.549, 0.589),
        "PI": (0.164, 0.488, 0.595),
        "MA": (0.173, 0.478, 0.551),
    },
    2000: {
        "DF": (0.582, 0.805, 0.814),
        "SP": (0.581, 0.756, 0.786),
        "SC": (0.526, 0.717, 0.812),
        "RJ": (0.530, 0.745, 0.740),
        "RS": (0.505, 0.720, 0.804),
        "PR": (0.522, 0.704, 0.747),
        "ES": (0.491, 0.687, 0.777),
        "MG": (0.470, 0.680, 0.759),
        "GO": (0.439, 0.686, 0.773),
        "MS": (0.445, 0.687, 0.752),
        "MT": (0.426, 0.689, 0.740),
        "RR": (0.457, 0.652, 0.717),
        "AP": (0.424, 0.638, 0.711),
        "RN": (0.396, 0.608, 0.700),
        "PE": (0.372, 0.615, 0.705),
        "CE": (0.377, 0.588, 0.713),
        "TO": (0.348, 0.605, 0.688),
        "RO": (0.345, 0.654, 0.688),
        "AM": (0.324, 0.608, 0.692),
        "PA": (0.319, 0.601, 0.725),
        "SE": (0.343, 0.596, 0.678),
        "AC": (0.325, 0.612, 0.694),
        "BA": (0.332, 0.594, 0.680),
        "PB": (0.331, 0.582, 0.672),
        "PI": (0.301, 0.556, 0.676),
        "MA": (0.312, 0.531, 0.649),
        "AL": (0.282, 0.574, 0.647),
    },
    2010: {
        "DF": (0.742, 0.863, 0.873),
        "SP": (0.719, 0.789, 0.845),
        "SC": (0.697, 0.773, 0.860),
        "RJ": (0.675, 0.782, 0.835),
        "PR": (0.668, 0.757, 0.830),
        "RS": (0.642, 0.769, 0.840),
        "ES": (0.653, 0.743, 0.835),
        "GO": (0.646, 0.742, 0.827),
        "MG": (0.638, 0.730, 0.838),
        "MS": (0.629, 0.740, 0.833),
        "MT": (0.635, 0.732, 0.821),
        "AP": (0.629, 0.694, 0.813),
        "RR": (0.628, 0.695, 0.809),
        "TO": (0.624, 0.690, 0.793),
        "RO": (0.577, 0.712, 0.800),
        "AM": (0.561, 0.677, 0.805),
        "RN": (0.597, 0.678, 0.792),
        "CE": (0.615, 0.651, 0.793),
        "PE": (0.574, 0.673, 0.789),
        "SE": (0.560, 0.672, 0.781),
        "BA": (0.555, 0.663, 0.783),
        "AC": (0.559, 0.671, 0.777),
        "PB": (0.555, 0.656, 0.783),
        "PA": (0.528, 0.646, 0.789),
        "PI": (0.547, 0.635, 0.777),
        "MA": (0.562, 0.612, 0.757),
        "AL": (0.520, 0.641, 0.755),
    },
}

ANOS = sorted(IDHM_DIMENSOES.keys())

# Faixas de desenvolvimento humano usadas pelo PNUD / Atlas Brasil
# Intervalos semiabertos [mínimo, máximo) para não deixar nenhum valor de fora
FAIXAS_IDHM = [
    (0.000, 0.500, "Muito baixo"),
    (0.500, 0.600, "Baixo"),
    (0.600, 0.700, "Médio"),
    (0.700, 0.800, "Alto"),
    (0.800, 1.001, "Muito alto"),
]

ORDEM_FAIXAS = ["Muito baixo", "Baixo", "Médio", "Alto", "Muito alto"]


def classificar_faixa(valor: float | None) -> str:
    """Devolve a faixa de desenvolvimento humano de um valor de IDHM."""
    if valor is None or valor != valor:  # None ou NaN
        return "Sem informação"
    for minimo, maximo, rotulo in FAIXAS_IDHM:
        if minimo <= valor < maximo:
            return rotulo
    return "Sem informação"
