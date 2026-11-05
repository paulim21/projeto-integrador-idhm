"""
Camada de decisão: diagnóstico por persona (gestor público) e simulação do
Fundo Regional de Redução de Desigualdades.

É aqui que a estatística vira recomendação. Nada neste módulo inventa número:
tudo sai das três dimensões do IDHM tratadas no ETL.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.dados_fonte import PERSONAS, classificar_faixa
from src.estatistica import comparar_com_distribuicao, resumo_descritivo

DIMENSOES = ["idhm_educacao", "idhm_renda", "idhm_longevidade"]
NOME_DIMENSAO = {
    "idhm_educacao": "Educação",
    "idhm_renda": "Renda",
    "idhm_longevidade": "Longevidade",
}

# O que cada dimensão mede, em linguagem de gestor
SIGNIFICADO = {
    "idhm_educacao": (
        "escolaridade da população adulta e fluxo escolar da população jovem "
        "(frequência e conclusão nas idades certas)"
    ),
    "idhm_renda": "renda média mensal por habitante (poder de compra das famílias)",
    "idhm_longevidade": "expectativa de vida ao nascer (saúde, saneamento e mortalidade)",
}

# Frentes de política pública associadas a cada dimensão
ALAVANCAS = {
    "idhm_educacao": [
        "busca ativa escolar e combate à distorção idade-série",
        "ensino médio em tempo integral e correção de fluxo",
        "educação de jovens e adultos para elevar a escolaridade adulta",
    ],
    "idhm_renda": [
        "qualificação profissional ligada às cadeias produtivas locais",
        "crédito e formalização de microempreendedores",
        "transferência de renda condicionada à frequência escolar",
    ],
    "idhm_longevidade": [
        "atenção básica e cobertura de saúde da família",
        "saneamento básico e água tratada (impacto direto na mortalidade infantil)",
        "redução de mortes evitáveis: pré-natal, vacinação e urgência",
    ],
}


# ---------------------------------------------------------------------------
# Diagnóstico de uma UF para a sua persona
# ---------------------------------------------------------------------------

def _br(valor, casas: int = 3) -> str:
    """Número no padrão brasileiro, com vírgula decimal."""
    if valor is None or valor != valor:
        return "—"
    return f"{valor:.{casas}f}".replace(".", ",")


def diagnostico_uf(df_ano: pd.DataFrame, df_completo: pd.DataFrame, sigla: str) -> dict:
    """
    Monta o diagnóstico completo de uma UF no ano filtrado.

    Duas leituras diferentes — e as duas importam:

    * **gargalo interno**: a dimensão de MENOR valor. Como o IDHM é média
      geométrica, é ela que segura o índice do estado.
    * **maior defasagem**: a dimensão em que o estado está MAIS LONGE do resto
      do país. Pode não ser a mesma, porque as três dimensões têm patamares
      nacionais distintos (a Longevidade do Brasil inteiro é alta; a Educação,
      baixa). É essa leitura que orienta o rateio do fundo.

    A simulação de ganho escolhe a dimensão de **maior retorno**: aquela que,
    levada sozinha até o referencial nacional, mais eleva o IDHM do estado.
    """
    linha = df_ano[df_ano["sigla_uf"] == sigla]
    if linha.empty:
        return {}
    linha = linha.iloc[0]

    posicao = comparar_com_distribuicao(df_ano, sigla, "idhm")
    valores = {c: float(linha[c]) for c in DIMENSOES}
    idhm = float(linha["idhm"])
    mais_fraca = min(valores, key=valores.get)
    mais_forte = max(valores, key=valores.get)

    medias = {c: float(df_ano[c].mean()) for c in DIMENSOES}
    lacunas = {c: medias[c] - valores[c] for c in DIMENSOES}
    maior_defasagem = max(lacunas, key=lacunas.get)

    # Referencial da simulação: usa a média das UFs; se o estado já estiver
    # acima dela em todas as dimensões, sobe o sarrafo para o Q3 e, depois,
    # para o melhor desempenho do país.
    referenciais = [
        ("a média das 27 UFs", medias),
        ("o 3º quartil (Q3) das UFs", {c: float(df_ano[c].quantile(0.75)) for c in DIMENSOES}),
        ("o melhor desempenho do país", {c: float(df_ano[c].max()) for c in DIMENSOES}),
    ]
    nome_referencial, alvo = referenciais[0]
    for nome, candidato in referenciais:
        if any(valores[c] < candidato[c] for c in DIMENSOES):
            nome_referencial, alvo = nome, candidato
            break

    ganhos = {}
    for coluna in DIMENSOES:
        simulado = dict(valores)
        simulado[coluna] = max(valores[coluna], alvo[coluna])
        ganhos[coluna] = float(np.prod(list(simulado.values())) ** (1 / 3)) - idhm
    maior_retorno = max(ganhos, key=ganhos.get)

    serie = df_completo[df_completo["sigla_uf"] == sigla].sort_values("ano")
    ganho_historico = None
    if len(serie) >= 2:
        ganho_historico = float(serie["idhm"].iloc[-1] - serie["idhm"].iloc[0])

    return {
        "sigla": sigla,
        "uf": linha["uf"],
        "regiao": linha["regiao"],
        "ano": int(linha["ano"]),
        "persona": PERSONAS.get(sigla, {}),
        "idhm": idhm,
        "faixa": linha["faixa_idhm"],
        "valores": valores,
        "medias_nacionais": medias,
        "lacunas": lacunas,
        "dimensao_mais_fraca": mais_fraca,
        "dimensao_mais_forte": mais_forte,
        "dimensao_maior_defasagem": maior_defasagem,
        "dimensao_maior_retorno": maior_retorno,
        "referencial": nome_referencial,
        "alvo": alvo,
        "ganhos_por_dimensao": ganhos,
        "desequilibrio_interno": float(linha["desequilibrio_interno"]),
        "idhm_melhor_cenario": idhm + ganhos[maior_retorno],
        "ganho_idhm_potencial": ganhos[maior_retorno],
        "posicao": posicao,
        "ganho_historico": ganho_historico,
        "serie": serie[["ano", "idhm"] + DIMENSOES],
    }


def texto_diagnostico(d: dict) -> str:
    """Parágrafo de consultoria para a persona — pronto para a roda de conversa."""
    if not d:
        return ""
    persona = d.get("persona", {})
    nome_gestor, cargo = persona.get("nome", ""), persona.get("cargo", "")
    quem = f"{nome_gestor} ({cargo})" if nome_gestor and cargo else (nome_gestor or d["uf"])
    fraca = d["dimensao_mais_fraca"]
    forte = d["dimensao_mais_forte"]
    defasada = d["dimensao_maior_defasagem"]
    retorno = d["dimensao_maior_retorno"]
    pos = d["posicao"]
    distancia = pos.get("distancia_media", 0.0)
    lado = "acima" if distancia >= 0 else "abaixo"

    partes = [
        f"**{quem}** — {d['uf']} fechou o Censo de {d['ano']} com IDHM de "
        f"**{_br(d['idhm'])}** (faixa *{d['faixa']}*), na "
        f"**{pos.get('posicao', '—')}ª posição entre {pos.get('total', 27)} UFs**, "
        f"{_br(abs(distancia))} ponto {lado} da média nacional e no "
        f"{pos.get('quartil', '—')}º quartil da distribuição.",

        f"O índice é a média geométrica das três dimensões — basta uma ficar para trás "
        f"para derrubar o conjunto. O **gargalo interno** de {d['uf']} é "
        f"**{NOME_DIMENSAO[fraca]}** ({_br(d['valores'][fraca])}), que mede {SIGNIFICADO[fraca]}. "
        f"A dimensão mais forte é **{NOME_DIMENSAO[forte]}** ({_br(d['valores'][forte])}), e a "
        f"distância entre a melhor e a pior dimensão do estado é de "
        f"**{_br(d['desequilibrio_interno'])}** ponto.",
    ]

    folga = d["lacunas"][defasada]
    if folga <= 0:
        partes.append(
            f"{d['uf']} está **acima da média das 27 UFs nas três dimensões**. A menor folga "
            f"é em **{NOME_DIMENSAO[defasada]}** ({_br(abs(folga))} ponto acima da média), "
            f"e é aí que o estado é mais facilmente alcançado por quem vem atrás. "
            f"Para um estado nessa posição, a referência útil deixa de ser a média e passa a "
            f"ser o grupo de ponta do país."
        )
    elif defasada != fraca:
        partes.append(
            f"Atenção a uma leitura que o número exige: a dimensão em que {d['uf']} está mais "
            f"**distante do resto do país** não é a mesma. É **{NOME_DIMENSAO[defasada]}**, "
            f"{_br(folga)} ponto abaixo da média das 27 UFs, contra "
            f"{_br(d['lacunas'][fraca])} ponto em {NOME_DIMENSAO[fraca]}. "
            f"Os patamares nacionais das três dimensões são diferentes — a Longevidade é alta "
            f"no Brasil inteiro e a Educação é baixa em quase todo lugar —, então *ter o menor "
            f"valor* e *estar mais atrás do país* são coisas distintas. O fundo trabalha com a "
            f"segunda leitura, porque é nela que o estado perde posição relativa."
        )
    else:
        partes.append(
            f"Neste caso as duas leituras coincidem: **{NOME_DIMENSAO[fraca]}** é ao mesmo tempo "
            f"o menor valor do estado e a dimensão em que ele está mais distante da média "
            f"nacional ({_br(folga)} ponto abaixo). O diagnóstico é inequívoco."
        )

    ganho = d["ganho_idhm_potencial"]
    if ganho > 0.0005:
        partes.append(
            f"Simulação de maior retorno: se **{NOME_DIMENSAO[retorno]}** subisse sozinha até "
            f"{d['referencial']} ({_br(d['alvo'][retorno])}), o IDHM de {d['uf']} iria de "
            f"{_br(d['idhm'])} para **{_br(d['idhm_melhor_cenario'])}** "
            f"(+{_br(ganho)}). Entre as três dimensões, é a que mais eleva o índice por ponto "
            f"ganho — e é por aí que a recomendação começa."
        )
    else:
        partes.append(
            f"{d['uf']} já está em {d['referencial']} ou acima nas três dimensões: não há ganho "
            f"a extrair de uma simulação de convergência. O caso deste estado não é de "
            f"recuperação, e sim de manter o ritmo e servir de referência para os demais."
        )
    return "\n\n".join(partes)


def anos_para_convergir(d: dict, meta: float) -> float | None:
    """
    Em quantos anos a UF alcança a meta mantendo o ritmo histórico observado
    entre o primeiro e o último censo da base (crescimento geométrico).
    """
    serie = d.get("serie")
    if serie is None or len(serie) < 2:
        return None
    inicio, fim = float(serie["idhm"].iloc[0]), float(serie["idhm"].iloc[-1])
    anos = int(serie["ano"].iloc[-1]) - int(serie["ano"].iloc[0])
    if inicio <= 0 or fim <= inicio or anos <= 0:
        return None
    taxa = (fim / inicio) ** (1 / anos) - 1
    if fim >= meta:
        return 0.0
    return float(np.log(meta / fim) / np.log(1 + taxa))


# ---------------------------------------------------------------------------
# Fundo Regional de Redução de Desigualdades
# ---------------------------------------------------------------------------

def simular_fundo(
    df_ano: pd.DataFrame,
    valor_total: float,
    referencia: float | None = None,
    concentracao: float = 1.0,
    teto_por_uf: float = 0.35,
) -> tuple[pd.DataFrame, dict]:
    """
    Rateia um fundo entre as UFs que estão ABAIXO de uma referência de IDHM.

    Critério (transparente e auditável):
      1. elegível  -> IDHM da UF < referência;
      2. lacuna_i  -> referência - IDHM_i;
      3. peso_i    -> lacuna_i ** concentracao   (expoente > 1 concentra mais
                      recurso nos estados mais distantes da referência);
      4. cota_i    -> valor_total * peso_i / soma(pesos), com teto por UF;
      5. dentro de cada UF, a cota é dividida entre as três dimensões na
         proporção da lacuna de cada dimensão até a média nacional —
         quem está mais atrás recebe mais.

    Devolve (tabela do rateio, parâmetros/resumo).
    """
    if referencia is None:
        referencia = float(df_ano["idhm"].median())

    base = df_ano.copy()
    base["lacuna_idhm"] = (referencia - base["idhm"]).round(4)
    elegiveis = base[base["lacuna_idhm"] > 0].copy()

    resumo = {
        "referencia": referencia,
        "faixa_referencia": classificar_faixa(referencia),
        "valor_total": valor_total,
        "concentracao": concentracao,
        "n_elegiveis": int(len(elegiveis)),
        "n_total": int(len(base)),
    }
    if elegiveis.empty:
        return pd.DataFrame(), resumo

    elegiveis["peso"] = elegiveis["lacuna_idhm"] ** concentracao
    elegiveis["cota_%"] = elegiveis["peso"] / elegiveis["peso"].sum()

    # teto por UF, com redistribuição proporcional do excedente
    excedente = (elegiveis["cota_%"] - teto_por_uf).clip(lower=0).sum()
    elegiveis["cota_%"] = elegiveis["cota_%"].clip(upper=teto_por_uf)
    if excedente > 0 and elegiveis["cota_%"].sum() > 0:
        elegiveis["cota_%"] = elegiveis["cota_%"] / elegiveis["cota_%"].sum()

    elegiveis["valor_R$"] = (elegiveis["cota_%"] * valor_total).round(2)

    # repartição interna por dimensão (lacuna até a média nacional das UFs)
    medias = {c: float(df_ano[c].mean()) for c in DIMENSOES}
    lacunas = pd.DataFrame(
        {c: (medias[c] - elegiveis[c]).clip(lower=0.001) for c in DIMENSOES},
        index=elegiveis.index,
    )
    proporcao = lacunas.div(lacunas.sum(axis=1), axis=0)
    for coluna in DIMENSOES:
        elegiveis[f"para_{NOME_DIMENSAO[coluna].lower()}_R$"] = (
            elegiveis["valor_R$"] * proporcao[coluna]
        ).round(2)

    elegiveis["prioridade"] = (
        elegiveis["lacuna_idhm"].rank(ascending=False, method="min").astype(int)
    )
    elegiveis["maior_defasagem"] = (
        lacunas.idxmax(axis=1).map(NOME_DIMENSAO)
    )

    colunas = [
        "prioridade", "sigla_uf", "uf", "regiao", "idhm", "lacuna_idhm",
        "cota_%", "valor_R$",
        "para_educação_R$", "para_renda_R$", "para_longevidade_R$",
        "dimensao_mais_fraca", "maior_defasagem",
    ]
    tabela = elegiveis.sort_values("lacuna_idhm", ascending=False)[colunas].reset_index(drop=True)

    resumo.update({
        "total_rateado": float(tabela["valor_R$"].sum()),
        "por_educacao": float(tabela["para_educação_R$"].sum()),
        "por_renda": float(tabela["para_renda_R$"].sum()),
        "por_longevidade": float(tabela["para_longevidade_R$"].sum()),
    })
    return tabela, resumo


def indicadores_desigualdade(df_ano: pd.DataFrame, coluna: str = "idhm") -> dict:
    """
    Medidas que respondem "a desigualdade entre os estados está grande?".
    Usa as mesmas estatísticas descritivas do projeto.
    """
    r = resumo_descritivo(df_ano[coluna])
    if not r:
        return {}
    melhor = df_ano.loc[df_ano[coluna].idxmax()]
    pior = df_ano.loc[df_ano[coluna].idxmin()]
    return {
        "amplitude": r["amplitude"],
        "iqr": r["iqr"],
        "coef_variacao": r["coef_variacao"],
        "desvio_padrao": r["desvio_padrao"],
        "melhor_uf": f"{melhor['uf']} ({_br(melhor[coluna])})",
        "pior_uf": f"{pior['uf']} ({_br(pior[coluna])})",
        "razao_melhor_pior": float(melhor[coluna] / pior[coluna]) if pior[coluna] else float("nan"),
        "n_abaixo_media": int((df_ano[coluna] < r["media"]).sum()),
    }
