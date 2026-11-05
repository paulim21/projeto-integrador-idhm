"""
ETL — Extração, Transformação e Carga da base de IDHM por UF.

Cada etapa registra o que fez em um "log de tratamento", que é exibido dentro
do dashboard. Assim a limpeza não fica escondida no código: ela é um resultado
apresentável para o gestor público.

Uso:
    from src.etl import executar_etl
    df, log = executar_etl("dados/raw/idhm_uf_bruto.csv")
"""

from __future__ import annotations

import io
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from src.dados_fonte import UF_NOME, UF_REGIAO, classificar_faixa

COLUNAS_DIMENSAO = ["idhm_educacao", "idhm_renda", "idhm_longevidade"]
RAIZ = Path(__file__).resolve().parents[1]
CAMINHO_BRUTO = RAIZ / "dados" / "raw" / "idhm_uf_bruto.csv"
CAMINHO_TRATADO = RAIZ / "dados" / "processed" / "idhm_uf_tratado.csv"

NOME_PARA_SIGLA = {
    unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode().lower(): sigla
    for sigla, nome in UF_NOME.items()
}


@dataclass
class LogETL:
    """Acumula o relatório de limpeza passo a passo."""

    passos: list[dict] = field(default_factory=list)

    def registrar(self, etapa: str, detalhe: str, linhas: int) -> None:
        self.passos.append({"Etapa": etapa, "O que foi feito": detalhe, "Linhas após a etapa": linhas})

    def como_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame(self.passos)


# ---------------------------------------------------------------------------
# 1. EXTRAÇÃO
# ---------------------------------------------------------------------------

def _parece_excel(origem) -> bool:
    """Arquivos .xlsx são ZIP: começam com os bytes 'PK'."""
    if isinstance(origem, (str, Path)):
        return Path(origem).suffix.lower() in (".xlsx", ".xlsm", ".xls")
    if isinstance(origem, io.BytesIO):
        posicao = origem.tell()
        assinatura = origem.read(2)
        origem.seek(posicao)
        return assinatura == b"PK"
    return False


def extrair(origem: str | Path | io.BytesIO | io.StringIO) -> pd.DataFrame:
    """
    Lê a base bruta.

    Aceita CSV (`;` como separador de coluna, `,` como decimal, UTF-8) e também
    planilhas XLSX/XLS — o enunciado do projeto pede upload de bases do IBGE em
    CSV ou XLSX, e o SIDRA exporta nos dois formatos. Tudo entra como texto: a
    conversão de tipos é uma etapa explícita do ETL, logo adiante.
    """
    if _parece_excel(origem):
        return pd.read_excel(origem, sheet_name=0, dtype=str).fillna("")
    return pd.read_csv(
        origem,
        sep=";",
        dtype=str,
        encoding="utf-8-sig",
        keep_default_na=False,
    )


# ---------------------------------------------------------------------------
# 2. TRANSFORMAÇÃO
# ---------------------------------------------------------------------------

def _para_numero(serie: pd.Series) -> pd.Series:
    """'0,663' -> 0.663 ; '' -> NaN ; '2.010' -> 2010."""
    limpo = (
        serie.astype(str)
        .str.strip()
        .str.replace(".", "", regex=False)   # separador de milhar
        .str.replace(",", ".", regex=False)  # separador decimal
        .replace({"": None, "nan": None, "N/D": None, "-": None})
    )
    return pd.to_numeric(limpo, errors="coerce")


def _normalizar_texto(serie: pd.Series) -> pd.Series:
    return serie.astype(str).str.strip().str.replace(r"\s+", " ", regex=True)


def transformar(bruto: pd.DataFrame) -> tuple[pd.DataFrame, LogETL]:
    log = LogETL()
    df = bruto.copy()
    log.registrar("1. Extração", f"Leitura do CSV bruto com {df.shape[1]} colunas, tudo como texto.", len(df))

    # --- 2.1 padronização de nomes de colunas e de texto -------------------
    df.columns = [c.strip().lower() for c in df.columns]
    df = df.rename(columns={"sigla": "sigla_uf", "unidade_federativa": "uf", "regiao": "regiao_origem"})
    for coluna in ["sigla_uf", "uf", "regiao_origem", "observacao"]:
        if coluna in df:
            df[coluna] = _normalizar_texto(df[coluna])
    df["sigla_uf"] = df["sigla_uf"].str.upper()
    df["uf"] = df["uf"].str.title()
    log.registrar(
        "2. Padronização de texto",
        "Removidos espaços duplicados/extras, siglas em MAIÚSCULO e nomes de UF em Capitalizado.",
        len(df),
    )

    # --- 2.2 conversão de tipos -------------------------------------------
    df["ano"] = _para_numero(df["ano"]).astype("Int64")
    for coluna in ["idhm"] + COLUNAS_DIMENSAO:
        df[coluna] = _para_numero(df[coluna])
    log.registrar(
        "3. Conversão de tipos",
        "Vírgula decimal convertida para ponto; 'ano' virou inteiro e os índices viraram float.",
        len(df),
    )

    # --- 2.3 remoção de linhas agregadas (não são UF) ----------------------
    antes = len(df)
    df = df[df["sigla_uf"].isin(UF_NOME.keys())].copy()
    log.registrar(
        "4. Remoção de agregados",
        f"Excluídas {antes - len(df)} linha(s) de total/consolidado (ex.: 'BRASIL'), que não são UF.",
        len(df),
    )

    # --- 2.4 descarte de colunas sem valor analítico -----------------------
    df = df.drop(columns=[c for c in ["observacao", "regiao_origem"] if c in df])
    log.registrar("5. Seleção de colunas", "Descartadas colunas livres de anotação sem uso analítico.", len(df))

    # --- 2.5 duplicatas ----------------------------------------------------
    antes = len(df)
    df = df.drop_duplicates(subset=["ano", "sigla_uf"], keep="first").copy()
    log.registrar(
        "6. Duplicatas",
        f"Removidas {antes - len(df)} duplicata(s) de ano+UF (chave que identifica cada registro).",
        len(df),
    )

    # --- 2.6 erro de escala: índice precisa estar entre 0 e 1 --------------
    correcoes = 0
    for coluna in COLUNAS_DIMENSAO:
        fora = df[coluna] > 1
        correcoes += int(fora.sum())
        df.loc[fora, coluna] = df.loc[fora, coluna] / 10
    log.registrar(
        "7. Faixa válida (0 a 1)",
        f"Corrigido(s) {correcoes} valor(es) fora do intervalo teórico do índice "
        "(erro de posição da vírgula na digitação: 6,63 -> 0,663).",
        len(df),
    )

    # --- 2.7 recomposição do IDHM faltante --------------------------------
    df["idhm_calculado"] = (
        df["idhm_educacao"] * df["idhm_renda"] * df["idhm_longevidade"]
    ) ** (1 / 3)
    faltantes = int(df["idhm"].isna().sum())
    df["idhm_origem"] = np.where(df["idhm"].isna(), "recalculado", "publicado")
    df["idhm"] = df["idhm"].fillna(df["idhm_calculado"]).round(3)
    log.registrar(
        "8. Dados faltantes",
        f"{faltantes} IDHM em branco foram RECALCULADOS pela média geométrica das 3 dimensões "
        "— não houve exclusão de UF nem preenchimento por média.",
        len(df),
    )

    # --- 2.8 validação do índice publicado --------------------------------
    df["divergencia"] = (df["idhm"] - df["idhm_calculado"]).abs().round(4)
    divergentes = int((df["divergencia"] > 0.001).sum())
    log.registrar(
        "9. Validação",
        f"Conferência IDHM publicado x média geométrica recalculada: {divergentes} divergência(s) "
        "acima de 0,001 em 81 registros.",
        len(df),
    )

    # --- 2.9 enriquecimento -----------------------------------------------
    df["regiao"] = df["sigla_uf"].map(UF_REGIAO)
    df["uf"] = df["sigla_uf"].map(UF_NOME)
    df["faixa_idhm"] = df["idhm"].apply(classificar_faixa)
    rotulo_dimensao = {
        "idhm_educacao": "Educação",
        "idhm_renda": "Renda",
        "idhm_longevidade": "Longevidade",
    }
    df["dimensao_mais_fraca"] = df[COLUNAS_DIMENSAO].idxmin(axis=1).map(rotulo_dimensao)
    df["dimensao_mais_forte"] = df[COLUNAS_DIMENSAO].idxmax(axis=1).map(rotulo_dimensao)
    # amplitude interna: quão desequilibradas são as 3 dimensões da UF
    df["desequilibrio_interno"] = (
        df[COLUNAS_DIMENSAO].max(axis=1) - df[COLUNAS_DIMENSAO].min(axis=1)
    ).round(3)
    log.registrar(
        "10. Enriquecimento",
        "Criadas as colunas região, faixa de desenvolvimento humano (PNUD), dimensão mais fraca/forte "
        "e desequilíbrio interno (maior - menor dimensão).",
        len(df),
    )

    colunas_finais = [
        "ano", "sigla_uf", "uf", "regiao", "idhm", "faixa_idhm",
        "idhm_educacao", "idhm_renda", "idhm_longevidade",
        "dimensao_mais_fraca", "dimensao_mais_forte", "desequilibrio_interno",
        "idhm_origem", "divergencia",
    ]
    df = df[colunas_finais].sort_values(["ano", "idhm"], ascending=[True, False]).reset_index(drop=True)
    return df, log


# ---------------------------------------------------------------------------
# 3. CARGA
# ---------------------------------------------------------------------------

def carregar(df: pd.DataFrame, destino: str | Path = CAMINHO_TRATADO) -> Path:
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(destino, index=False, encoding="utf-8")
    return destino


def executar_etl(origem: str | Path | io.BytesIO | None = None) -> tuple[pd.DataFrame, LogETL]:
    """Pipeline completo: extrai, transforma e devolve (dados tratados, log)."""
    origem = origem if origem is not None else CAMINHO_BRUTO
    return transformar(extrair(origem))


if __name__ == "__main__":
    dados, relatorio = executar_etl()
    destino = carregar(dados)
    print(relatorio.como_dataframe().to_string(index=False))
    print(f"\nBase tratada: {destino}  |  {dados.shape[0]} linhas x {dados.shape[1]} colunas")
    print(dados.head(8).to_string(index=False))


# ===========================================================================
# BASE MUNICIPAL — 5.565 municípios x 3 Censos (1991, 2000, 2010)
# ===========================================================================

CAMINHO_MUNICIPAL = RAIZ / "dados" / "raw" / "idhm_municipios_bruto.csv"
CAMINHO_SERIE_RECENTE = RAIZ / "dados" / "raw" / "idhm_uf_serie_recente.csv"
CAMINHO_INVESTIMENTO = RAIZ / "dados" / "raw" / "investimento_publico_uf.csv"

# código IBGE de 2 dígitos -> sigla da UF
CODIGO_PARA_SIGLA = {
    11: "RO", 12: "AC", 13: "AM", 14: "RR", 15: "PA", 16: "AP", 17: "TO",
    21: "MA", 22: "PI", 23: "CE", 24: "RN", 25: "PB", 26: "PE", 27: "AL",
    28: "SE", 29: "BA", 31: "MG", 32: "ES", 33: "RJ", 35: "SP",
    41: "PR", 42: "SC", 43: "RS", 50: "MS", 51: "MT", 52: "GO", 53: "DF",
}


def executar_etl_municipal(origem: str | Path | io.BytesIO | None = None):
    """
    ETL da base municipal do Atlas Brasil.

    Mesmo pipeline da base estadual, adaptado à escala: conversão de tipos,
    padronização de nomes, tradução do código IBGE da UF para sigla e região,
    validação do índice pela média geométrica e enriquecimento.
    """
    origem = origem if origem is not None else CAMINHO_MUNICIPAL
    log = LogETL()

    df = pd.read_csv(origem, sep=";", dtype=str, encoding="utf-8", keep_default_na=False)
    df.columns = [c.strip() for c in df.columns]
    log.registrar("1. Extração", f"Leitura da base municipal do Atlas Brasil ({df.shape[1]} colunas).", len(df))

    df = df.rename(columns={
        "ANO": "ano", "UF": "codigo_uf", "Codmun7": "codigo_municipio",
        "Município": "municipio", "IDHM": "idhm", "IDHM_E": "idhm_educacao",
        "IDHM_L": "idhm_longevidade", "IDHM_R": "idhm_renda",
        "ESPVIDA": "expectativa_vida", "RDPC": "renda_per_capita", "POPT": "populacao",
    })

    numericas = ["idhm", "idhm_educacao", "idhm_longevidade", "idhm_renda",
                 "expectativa_vida", "renda_per_capita"]
    for coluna in numericas:
        df[coluna] = _para_numero(df[coluna])
    df["ano"] = pd.to_numeric(df["ano"], errors="coerce").astype("Int64")
    df["codigo_uf"] = pd.to_numeric(df["codigo_uf"], errors="coerce").astype("Int64")
    df["codigo_municipio"] = pd.to_numeric(df["codigo_municipio"], errors="coerce").astype("Int64")
    df["populacao"] = pd.to_numeric(df["populacao"], errors="coerce").astype("Int64")
    log.registrar(
        "2. Conversão de tipos",
        "Vírgula decimal convertida para ponto; códigos IBGE e população como inteiros.",
        len(df),
    )

    # nomes em CAIXA ALTA no arquivo original
    df["municipio"] = df["municipio"].str.strip().str.title()
    df["sigla_uf"] = df["codigo_uf"].map(CODIGO_PARA_SIGLA)
    df["uf"] = df["sigla_uf"].map(UF_NOME)
    df["regiao"] = df["sigla_uf"].map(UF_REGIAO)
    log.registrar(
        "3. Padronização e geografia",
        "Nomes de município de CAIXA ALTA para Capitalizado; código IBGE da UF traduzido "
        "para sigla, nome e região.",
        len(df),
    )

    antes = len(df)
    df = df.dropna(subset=["idhm", "sigla_uf"]).drop_duplicates(subset=["ano", "codigo_municipio"])
    log.registrar(
        "4. Integridade",
        f"Removidas {antes - len(df)} linha(s) sem índice ou com chave ano+município repetida.",
        len(df),
    )

    df["idhm_calculado"] = (
        df["idhm_educacao"] * df["idhm_longevidade"] * df["idhm_renda"]
    ) ** (1 / 3)
    divergentes = int(((df["idhm"] - df["idhm_calculado"]).abs() > 0.002).sum())
    log.registrar(
        "5. Validação",
        f"IDHM publicado conferido contra a média geométrica das 3 dimensões: "
        f"{divergentes} divergência(s) acima de 0,002 em {len(df)} registros.",
        len(df),
    )

    df["faixa_idhm"] = df["idhm"].apply(classificar_faixa)
    rotulo = {"idhm_educacao": "Educação", "idhm_renda": "Renda", "idhm_longevidade": "Longevidade"}
    df["dimensao_mais_fraca"] = df[COLUNAS_DIMENSAO].idxmin(axis=1).map(rotulo)
    df["desequilibrio_interno"] = (
        df[COLUNAS_DIMENSAO].max(axis=1) - df[COLUNAS_DIMENSAO].min(axis=1)
    ).round(3)
    log.registrar(
        "6. Enriquecimento",
        "Criadas faixa do PNUD, dimensão mais fraca e desequilíbrio interno de cada município.",
        len(df),
    )

    colunas = [
        "ano", "codigo_municipio", "municipio", "sigla_uf", "uf", "regiao",
        "idhm", "faixa_idhm", "idhm_educacao", "idhm_renda", "idhm_longevidade",
        "dimensao_mais_fraca", "desequilibrio_interno",
        "expectativa_vida", "renda_per_capita", "populacao",
    ]
    df = df[colunas].sort_values(["ano", "idhm"], ascending=[True, False]).reset_index(drop=True)
    return df, log


# ===========================================================================
# SÉRIE RECENTE (2012–2024) e INVESTIMENTO PÚBLICO
# ===========================================================================

def carregar_serie_recente(origem: str | Path | None = None) -> pd.DataFrame:
    """
    Série anual do IDHM por UF, 2012–2024 (PNUD/FJP/IBGE, Radar IDHM).

    ATENÇÃO: metodologia diferente da série censitária de 1991/2000/2010.
    Nunca deve ser concatenada com ela no mesmo gráfico.
    """
    origem = origem if origem is not None else CAMINHO_SERIE_RECENTE
    df = pd.read_csv(origem, sep=";", decimal=",", encoding="utf-8")
    df["uf"] = df["sigla_uf"].map(UF_NOME)
    df["regiao"] = df["sigla_uf"].map(UF_REGIAO)
    df["faixa_idhm"] = df["idhm"].apply(classificar_faixa)
    rotulo = {"idhm_educacao": "Educação", "idhm_renda": "Renda", "idhm_longevidade": "Longevidade"}
    df["dimensao_mais_fraca"] = df[COLUNAS_DIMENSAO].idxmin(axis=1).map(rotulo)
    df["dimensao_mais_forte"] = df[COLUNAS_DIMENSAO].idxmax(axis=1).map(rotulo)
    df["desequilibrio_interno"] = (
        df[COLUNAS_DIMENSAO].max(axis=1) - df[COLUNAS_DIMENSAO].min(axis=1)
    ).round(3)
    return df


def carregar_investimento(origem: str | Path | None = None) -> pd.DataFrame:
    """Despesa pública estadual por habitante (Siconfi / Tesouro Nacional)."""
    origem = origem if origem is not None else CAMINHO_INVESTIMENTO
    df = pd.read_csv(origem, sep=";", decimal=",", encoding="utf-8")
    df["regiao"] = df["sigla_uf"].map(UF_REGIAO)
    return df
