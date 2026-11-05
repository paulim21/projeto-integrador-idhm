"""
Prepara a base MUNICIPAL do IDHM: dados/raw/idhm_municipios_bruto.csv

Origem
------
Atlas do Desenvolvimento Humano no Brasil (PNUD / Ipea / Fundação João Pinheiro),
arquivo de dados brutos `atlas2013_dadosbrutos_pt.xlsx`, construído sobre os
Censos Demográficos do IBGE de 1991, 2000 e 2010. São 5.565 municípios × 3 anos
= 16.695 registros e mais de 200 indicadores.

O arquivo original do Atlas tem ~230 colunas e dezenas de megabytes. Este script
recorta apenas as colunas que o painel usa e grava um CSV enxuto, no mesmo
formato brasileiro do arquivo de origem (`;` como separador de coluna e `,`
como separador decimal).

Colunas mantidas
----------------
ANO, UF (código IBGE), Codmun7 (código IBGE do município), Município,
IDHM, IDHM_E (Educação), IDHM_L (Longevidade), IDHM_R (Renda),
ESPVIDA (expectativa de vida, em anos), RDPC (renda domiciliar per capita, R$),
POPT (população residente total).

Uso
---
    python scripts/preparar_base_municipal.py <caminho-do-arquivo-de-origem>

Se o caminho não for passado, o script procura `atlas_municipal_bruto.csv` ou
`atlas2013_dadosbrutos_pt.xlsx` na pasta `dados/externo/`.

Onde obter o arquivo de origem
------------------------------
O endereço histórico do Atlas (`atlasbrasil.org.br/2013/data/rawData/`) saiu do
ar. Hoje o caminho é:

  1. https://www.atlasbrasil.org.br/  → seção Acervo → download da base completa;
  2. https://dados.gov.br/  → conjunto "Atlas do Desenvolvimento Humano no Brasil";
  3. espelho em CSV do mesmo arquivo, usado para montar esta base:
     https://raw.githubusercontent.com/mauriciocramos/IDHM/master/municipal.csv

O CSV recortado já vem versionado no repositório, então este script só é
necessário para reconstruir ou atualizar a base.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
SAIDA = RAIZ / "dados" / "raw" / "idhm_municipios_bruto.csv"
PASTA_EXTERNO = RAIZ / "dados" / "externo"

COLUNAS = [
    "ANO", "UF", "Codmun7", "Município",
    "IDHM", "IDHM_E", "IDHM_L", "IDHM_R",
    "ESPVIDA", "RDPC", "POPT",
]
COLUNAS_NUMERICAS = ["IDHM", "IDHM_E", "IDHM_L", "IDHM_R", "ESPVIDA", "RDPC"]


def localizar_origem(argumento: str | None) -> Path:
    if argumento:
        caminho = Path(argumento)
        if not caminho.exists():
            raise SystemExit(f"Arquivo não encontrado: {caminho}")
        return caminho
    for nome in ("atlas_municipal_bruto.csv", "atlas2013_dadosbrutos_pt.xlsx"):
        candidato = PASTA_EXTERNO / nome
        if candidato.exists():
            return candidato
    raise SystemExit(
        "Informe o arquivo de origem do Atlas Brasil:\n"
        "    python scripts/preparar_base_municipal.py <caminho>\n"
        f"ou coloque-o em {PASTA_EXTERNO}. Veja no cabeçalho deste arquivo onde baixá-lo."
    )


def ler(origem: Path) -> pd.DataFrame:
    if origem.suffix.lower() in (".xlsx", ".xls"):
        bruto = pd.read_excel(origem, sheet_name=0)
        faltando = [c for c in COLUNAS if c not in bruto.columns]
        if faltando:
            raise SystemExit(f"Colunas ausentes no arquivo de origem: {faltando}")
        return bruto[COLUNAS].copy()
    return pd.read_csv(origem, sep=";", usecols=COLUNAS, decimal=",", encoding="utf-8")


def main() -> None:
    origem = localizar_origem(sys.argv[1] if len(sys.argv) > 1 else None)
    df = ler(origem)[COLUNAS]
    print(f"Origem: {origem}  ->  {df.shape[0]} linhas x {df.shape[1]} colunas")

    # Conferência de integridade: o IDHM publicado tem de ser a média geométrica
    # das três dimensões. Se isso não fechar, o recorte pegou coluna errada.
    calculado = (df["IDHM_E"] * df["IDHM_L"] * df["IDHM_R"]) ** (1 / 3)
    erro = (df["IDHM"] - calculado).abs().max()
    print(f"Maior divergência IDHM publicado x média geométrica: {erro:.4f}")
    if erro > 0.002:
        raise SystemExit("Divergência acima do tolerável — confira as colunas de origem.")

    por_ano = df.groupby("ANO")["Codmun7"].nunique().to_dict()
    print("Municípios por ano:", por_ano)

    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(SAIDA, sep=";", index=False, decimal=",", encoding="utf-8",
              float_format="%.3f")
    tamanho = SAIDA.stat().st_size / 1024 / 1024
    print(f"Base municipal gravada em {SAIDA} ({tamanho:.1f} MB).")


if __name__ == "__main__":
    main()
