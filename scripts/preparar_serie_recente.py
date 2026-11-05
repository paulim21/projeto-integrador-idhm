"""
Prepara a SÉRIE RECENTE do IDHM por UF: dados/raw/idhm_uf_serie_recente.csv

Origem
------
PNUD, Fundação João Pinheiro e IBGE.
"RADAR IDHM: evolução do IDHM e de seus componentes no período de 2012 a 2024".
As tabelas do anexo trazem, por Unidade da Federação e ano:

    Tabela 5 -> IDHM
    Tabela 6 -> IDHM Longevidade
    Tabela 7 -> IDHM Educação
    Tabela 8 -> IDHM Renda

Resultado: 27 UFs × 13 anos (2012 a 2024) = 351 registros.

ATENÇÃO METODOLÓGICA
--------------------
Esta série NÃO é comparável linha a linha com a série censitária de 1991, 2000
e 2010 usada no restante do painel. A série dos Censos é calculada sobre o
Censo Demográfico; a série 2012–2024 é estimada a partir da PNAD Contínua e de
registros administrativos, com metodologia revisada. Por isso o painel mantém
as duas em abas separadas e avisa o usuário — juntá-las em um único gráfico
produziria uma comparação falsa.

Uso
---
    python scripts/preparar_serie_recente.py <caminho-do-pdf-do-radar-idhm>

O PDF do Radar IDHM pode ser obtido em https://www.atlasbrasil.org.br/ (acervo)
ou no portal do PNUD Brasil (https://www.undp.org/pt/brazil). Requer `pypdf`.

O CSV resultante já vem versionado no repositório; este script serve para
reconstruir ou atualizar a base quando sair uma edição nova do Radar.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from src.dados_fonte import UF_NOME  # noqa: E402

SAIDA = RAIZ / "dados" / "raw" / "idhm_uf_serie_recente.csv"

# número da tabela no anexo -> nome da coluna no nosso esquema
TABELAS = {
    "TABELA 5.": "idhm",
    "TABELA 6.": "idhm_longevidade",
    "TABELA 7.": "idhm_educacao",
    "TABELA 8.": "idhm_renda",
}

NOME_PARA_SIGLA = {nome.lower(): sigla for sigla, nome in UF_NOME.items()}

LINHA = re.compile(
    r"^\s*\d{1,2}\s+(?P<uf>[A-Za-zÀ-ÿ\s]+?)\s+(?P<valores>(?:0\.\d{3}\s*){10,})$"
)


def parsear_tabela(texto: str) -> tuple[list[int], dict[str, list[float]]]:
    """Extrai (anos, {sigla_uf: [valores por ano]}) de uma página de tabela do anexo."""
    linhas = texto.split("\n")

    # a linha de cabeçalho é a que começa com RANKING e lista os anos
    anos: list[int] = []
    for linha in linhas:
        if "RANKING" in linha.upper():
            anos = [int(a) for a in re.findall(r"\b(20[12]\d)\b", linha)]
            if anos:
                break
    if not anos:
        return [], {}

    dados: dict[str, list[float]] = {}
    for linha in linhas:
        m = LINHA.match(linha)
        if not m:
            continue
        nome = re.sub(r"\s+", " ", m.group("uf")).strip().lower()
        sigla = NOME_PARA_SIGLA.get(nome)
        if sigla is None:
            continue
        valores = [float(v) for v in m.group("valores").split()]
        # a linha só vale se tiver exatamente um valor por ano do cabeçalho
        if len(valores) == len(anos):
            dados[sigla] = valores
    return anos, dados


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit(
            "Informe o PDF do Radar IDHM:\n"
            "    python scripts/preparar_serie_recente.py <caminho-do-pdf>\n"
            "Veja no cabeçalho deste arquivo onde baixá-lo."
        )
    caminho = Path(sys.argv[1])
    if not caminho.exists():
        raise SystemExit(f"Arquivo não encontrado: {caminho}")

    from pypdf import PdfReader

    leitor = PdfReader(str(caminho))
    coletado: dict[str, dict] = {}
    anos_ref: list[int] = []

    for pagina in leitor.pages:
        texto = pagina.extract_text() or ""
        for marcador, coluna in TABELAS.items():
            if marcador in texto and "Unidades da Federação" in texto and coluna not in coletado:
                anos, dados = parsear_tabela(texto)
                if len(dados) == 27:
                    coletado[coluna] = dados
                    anos_ref = anos_ref or anos

    faltando = [c for c in TABELAS.values() if c not in coletado]
    if faltando:
        raise SystemExit(f"Não encontrei as tabelas de: {faltando}. O PDF é o Radar IDHM correto?")

    linhas = []
    for sigla in UF_NOME:
        for i, ano in enumerate(anos_ref):
            linhas.append({
                "ano": ano,
                "sigla_uf": sigla,
                "idhm": coletado["idhm"][sigla][i],
                "idhm_educacao": coletado["idhm_educacao"][sigla][i],
                "idhm_renda": coletado["idhm_renda"][sigla][i],
                "idhm_longevidade": coletado["idhm_longevidade"][sigla][i],
            })

    df = pd.DataFrame(linhas).sort_values(["ano", "sigla_uf"]).reset_index(drop=True)

    # conferência: o IDHM publicado deve ser a média geométrica das 3 dimensões
    calculado = (df.idhm_educacao * df.idhm_renda * df.idhm_longevidade) ** (1 / 3)
    erro = (df.idhm - calculado).abs().max()
    print(f"Registros: {len(df)}  |  anos: {anos_ref[0]}–{anos_ref[-1]}")
    print(f"Maior divergência IDHM publicado x média geométrica: {erro:.4f}")

    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(SAIDA, sep=";", index=False, decimal=",", encoding="utf-8", float_format="%.3f")
    print(f"Série recente gravada em {SAIDA}")


if __name__ == "__main__":
    main()
