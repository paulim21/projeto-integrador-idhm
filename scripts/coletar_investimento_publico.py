"""
Coleta o INVESTIMENTO PÚBLICO ESTADUAL: dados/raw/investimento_publico_uf.csv

Origem
------
Siconfi — Sistema de Informações Contábeis e Fiscais do Setor Público Brasileiro,
Secretaria do Tesouro Nacional. API pública de dados abertos:

    https://apidatalake.tesouro.gov.br/ords/siconfi/tt/dca
    Anexo I-E da DCA (Declaração de Contas Anuais) — Despesas por Função.

Por que esta base
-----------------
O IBGE e o Atlas Brasil não publicam gasto público: o IDHM mede resultado
social, não esforço orçamentário. Para responder à pergunta de negócio
"existe correlação entre IDHM e investimento público?" é preciso cruzar com
a base fiscal oficial, e a do Tesouro é a fonte primária.

O que é coletado, por estado e por ano:
    * despesa total (Despesas Exceto Intraorçamentárias, empenhadas)
    * despesa da função 10 — Saúde
    * despesa da função 12 — Educação
    * despesa da função 08 — Assistência Social
    * população do ente (a própria API devolve)

O painel usa esses valores em REAIS POR HABITANTE. A soma de Saúde + Educação +
Assistência Social é tratada como "investimento social", que é a parcela do
orçamento ligada diretamente às três dimensões do IDHM.

LIMITE DA LEITURA
-----------------
Trata-se de despesa EMPENHADA no exercício pelo GOVERNO ESTADUAL. Não inclui
gasto dos municípios nem da União dentro do estado, e despesa empenhada não é
sinônimo de investimento executado. É uma medida de esforço orçamentário do
estado, e o painel diz isso ao lado do gráfico. Correlação aqui não é causa:
o IDHM responde a décadas de política pública, não ao orçamento de um ano.

Uso
---
    python scripts/coletar_investimento_publico.py [ano]

O ano padrão é 2024, para casar com o último ano da série recente do IDHM.
O CSV já vem versionado no repositório; o script serve para atualizar.
"""

from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from src.dados_fonte import UF_NOME  # noqa: E402

SAIDA = RAIZ / "dados" / "raw" / "investimento_publico_uf.csv"
API = "https://apidatalake.tesouro.gov.br/ords/siconfi/tt/dca"

# código IBGE de 2 dígitos de cada UF (id_ente dos governos estaduais no Siconfi)
CODIGO_UF = {
    "RO": 11, "AC": 12, "AM": 13, "RR": 14, "PA": 15, "AP": 16, "TO": 17,
    "MA": 21, "PI": 22, "CE": 23, "RN": 24, "PB": 25, "PE": 26, "AL": 27,
    "SE": 28, "BA": 29, "MG": 31, "ES": 32, "RJ": 33, "SP": 35,
    "PR": 41, "SC": 42, "RS": 43, "MS": 50, "MT": 51, "GO": 52, "DF": 53,
}

FUNCOES = {
    "despesa_saude": "10 - Saúde",
    "despesa_educacao": "12 - Educação",
    "despesa_assistencia_social": "08 - Assistência Social",
}
TOTAL = "Despesas Exceto Intraorçamentárias"
COLUNA = "Despesas Empenhadas"


def consultar(ano: int, codigo: int, tentativas: int = 3) -> list[dict]:
    url = f"{API}?an_exercicio={ano}&no_anexo=DCA-Anexo%20I-E&id_ente={codigo}"
    for tentativa in range(1, tentativas + 1):
        try:
            with urllib.request.urlopen(url, timeout=90) as resposta:
                return json.loads(resposta.read().decode("utf-8")).get("items", [])
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as erro:
            if tentativa == tentativas:
                print(f"  falhou após {tentativas} tentativas: {erro}")
                return []
            time.sleep(2 * tentativa)
    return []


def main() -> None:
    ano = int(sys.argv[1]) if len(sys.argv) > 1 else 2024
    linhas = []

    for sigla, codigo in CODIGO_UF.items():
        itens = consultar(ano, codigo)
        if not itens:
            print(f"{sigla}: sem dados para {ano}")
            continue

        registro = {"ano": ano, "sigla_uf": sigla, "uf": UF_NOME[sigla],
                    "populacao": itens[0].get("populacao")}
        for chave, conta in {"despesa_total": TOTAL, **FUNCOES}.items():
            valor = next(
                (i["valor"] for i in itens
                 if i.get("coluna") == COLUNA and (i.get("conta") or "").strip() == conta),
                None,
            )
            registro[chave] = valor
        linhas.append(registro)
        print(f"{sigla}: total R$ {registro['despesa_total']:,.0f}  |  pop {registro['populacao']:,}")

    df = pd.DataFrame(linhas)
    if len(df) < 27:
        print(f"\nAVISO: {len(df)} de 27 UFs coletadas.")

    df["investimento_social"] = (
        df[["despesa_saude", "despesa_educacao", "despesa_assistencia_social"]].sum(axis=1)
    )
    for coluna in ["despesa_total", "despesa_saude", "despesa_educacao",
                   "despesa_assistencia_social", "investimento_social"]:
        df[f"{coluna}_per_capita"] = (df[coluna] / df["populacao"]).round(2)

    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    df.sort_values("sigla_uf").to_csv(
        SAIDA, sep=";", index=False, decimal=",", encoding="utf-8", float_format="%.2f"
    )
    print(f"\nGravado em {SAIDA} ({len(df)} UFs, exercício {ano}).")


if __name__ == "__main__":
    main()
