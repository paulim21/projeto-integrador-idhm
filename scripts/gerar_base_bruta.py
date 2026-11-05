"""
Gera a base BRUTA do projeto: dados/raw/idhm_uf_bruto.csv

Por que uma base "bruta"?
------------------------
O projeto exige a etapa de limpeza e tratamento de dados (ETL). Para que essa
etapa seja real e demonstrável, este script grava o arquivo no formato em que
os dados costumam chegar na prática, com os problemas típicos de uma extração
manual de planilha:

  1. separador decimal com VÍRGULA  (padrão brasileiro)
  2. separador de colunas PONTO E VÍRGULA
  3. nomes de UF com espaços sobrando, caixa alta/baixa inconsistente
  4. coluna de ano gravada como texto ("2010", " 2000", "2.010")
  5. siglas em minúsculo em algumas linhas
  6. LINHAS DUPLICADAS (extração repetida)
  7. valores FALTANTES na coluna de IDHM total
  8. linha de TOTAL/agregado ("BRASIL") misturada com as UFs
  9. erro de digitação de escala (vírgula no lugar errado: 6,63 em vez de 0,663)
 10. coluna livre de observações sem valor analítico

Rode:  python scripts/gerar_base_bruta.py
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from src.dados_fonte import IDHM_DIMENSOES, UF_NOME, UF_REGIAO  # noqa: E402

SAIDA = RAIZ / "dados" / "raw" / "idhm_uf_bruto.csv"

CABECALHO = [
    "ano",
    "sigla",
    "unidade_federativa",
    "regiao",
    "idhm",
    "idhm_educacao",
    "idhm_renda",
    "idhm_longevidade",
    "observacao",
]


def br(valor: float, casas: int = 3) -> str:
    """Formata número no padrão brasileiro (vírgula decimal)."""
    return f"{valor:.{casas}f}".replace(".", ",")


def media_geometrica(a: float, b: float, c: float) -> float:
    return (a * b * c) ** (1 / 3)


def sujar_nome(nome: str, i: int) -> str:
    """Introduz as inconsistências de digitação do nome da UF."""
    if i % 7 == 0:
        return f"  {nome.upper()}  "
    if i % 5 == 0:
        return f"{nome.lower()} "
    if i % 3 == 0:
        return f" {nome}"
    return nome


def sujar_ano(ano: int, i: int) -> str:
    if i % 11 == 0:
        return f"{ano:,}".replace(",", ".")  # 2.010
    if i % 4 == 0:
        return f" {ano}"
    return str(ano)


def main() -> None:
    linhas: list[list[str]] = []
    i = 0

    for ano, por_uf in IDHM_DIMENSOES.items():
        for sigla, (edu, renda, longe) in por_uf.items():
            i += 1
            idhm = media_geometrica(edu, renda, longe)

            sigla_txt = sigla.lower() if i % 9 == 0 else sigla
            # (7) alguns IDHM totais vêm em branco -> o ETL recalcula
            idhm_txt = "" if i % 13 == 0 else br(idhm)
            # (9) erro de escala proposital em uma linha conhecida
            renda_txt = br(renda)
            if (ano, sigla) == (2010, "BA"):
                renda_txt = br(renda * 10, 2)  # 6,63 em vez de 0,663

            linhas.append([
                sujar_ano(ano, i),
                sigla_txt,
                sujar_nome(UF_NOME[sigla], i),
                UF_REGIAO[sigla],
                idhm_txt,
                br(edu),
                renda_txt,
                br(longe),
                "extração manual Atlas Brasil" if i % 6 == 0 else "",
            ])

    # (8) linhas agregadas que não são UF e precisam sair na limpeza
    for ano, idhm_br in ((1991, 0.493), (2000, 0.612), (2010, 0.727)):
        linhas.append([
            str(ano), "BR", "BRASIL", "Brasil", br(idhm_br),
            "", "", "", "linha de total - nao usar",
        ])

    # (6) duplicatas de extração
    duplicatas = [l for l in linhas if l[1].upper() in {"MA", "BA", "MG"}][:4]
    linhas.extend([list(l) for l in duplicatas])

    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    with SAIDA.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh, delimiter=";")
        w.writerow(CABECALHO)
        w.writerows(linhas)

    print(f"Base bruta gravada em {SAIDA} ({len(linhas)} linhas).")


if __name__ == "__main__":
    main()
