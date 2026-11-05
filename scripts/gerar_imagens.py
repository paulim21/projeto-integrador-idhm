"""
Gera as imagens ilustrativas do dashboard (pasta assets/).

São duas figuras explicativas, desenhadas com Matplotlib para não depender de
imagens de terceiros com licença incerta:

  1. assets/idhm_composicao.png  -> como as três dimensões formam o IDHM
  2. assets/faixas_idhm.png      -> a régua de faixas do PNUD com os estados
                                    atendidos posicionados nela

Rode:  python scripts/gerar_imagens.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from src.dados_fonte import IDHM_DIMENSOES, PERSONAS, UF_NOME  # noqa: E402

ASSETS = RAIZ / "assets"

AZUL = "#2a78d6"
LARANJA = "#eb6834"
AGUA = "#1baf7a"
TINTA = "#0b0b0b"
TINTA2 = "#52514e"
FUNDO = "#fcfcfb"


def _caixa(ax, x, y, largura, altura, cor, titulo, valor, legenda):
    ax.add_patch(
        FancyBboxPatch(
            (x, y), largura, altura,
            boxstyle="round,pad=0.015,rounding_size=0.02",
            linewidth=2.2, edgecolor=cor, facecolor="white",
        )
    )
    ax.text(x + largura / 2, y + altura * 0.70, titulo, ha="center", va="center",
            fontsize=13, fontweight="bold", color=cor)
    ax.text(x + largura / 2, y + altura * 0.44, valor, ha="center", va="center",
            fontsize=11, color=TINTA)
    ax.text(x + largura / 2, y + altura * 0.17, legenda, ha="center", va="center",
            fontsize=9, color=TINTA2, wrap=True)


def figura_composicao() -> Path:
    fig, ax = plt.subplots(figsize=(10, 4.6), facecolor=FUNDO)
    ax.set_facecolor(FUNDO)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    ax.text(0.5, 0.95, "Como o IDHM é formado", ha="center", va="top",
            fontsize=16, fontweight="bold", color=TINTA)
    ax.text(0.5, 0.875, "três dimensões com o mesmo peso, combinadas por média geométrica",
            ha="center", va="top", fontsize=10.5, color=TINTA2)

    caixas = [
        (0.03, AZUL, "Educação", "escolaridade do adulto\n+ fluxo escolar do jovem"),
        (0.355, LARANJA, "Renda", "renda mensal\nper capita"),
        (0.68, AGUA, "Longevidade", "expectativa de vida\nao nascer"),
    ]
    for x, cor, titulo, legenda in caixas:
        _caixa(ax, x, 0.42, 0.29, 0.30, cor, titulo, "índice de 0 a 1", legenda)

    for x in (0.175, 0.5, 0.825):
        ax.add_patch(
            FancyArrowPatch((x, 0.41), (0.5 if x != 0.5 else 0.5, 0.30),
                            arrowstyle="-|>", mutation_scale=14,
                            linewidth=1.4, color=TINTA2,
                            connectionstyle="arc3,rad=0" if x == 0.5 else
                            ("arc3,rad=0.15" if x < 0.5 else "arc3,rad=-0.15"))
        )

    ax.add_patch(
        FancyBboxPatch((0.22, 0.08), 0.56, 0.19,
                       boxstyle="round,pad=0.015,rounding_size=0.02",
                       linewidth=2.4, edgecolor=TINTA, facecolor="white")
    )
    ax.text(0.5, 0.215, "IDHM", ha="center", va="center",
            fontsize=15, fontweight="bold", color=TINTA)
    ax.text(0.5, 0.135, r"$IDHM=\sqrt[3]{\,Educação \times Renda \times Longevidade\,}$",
            ha="center", va="center", fontsize=12.5, color=TINTA2)

    ax.text(0.5, 0.015,
            "Média geométrica: uma dimensão baixa derruba o índice inteiro — por isso o diagnóstico "
            "começa pela dimensão mais fraca de cada estado.",
            ha="center", va="bottom", fontsize=9, color=TINTA2, style="italic")

    ASSETS.mkdir(parents=True, exist_ok=True)
    destino = ASSETS / "idhm_composicao.png"
    fig.savefig(destino, dpi=160, bbox_inches="tight", facecolor=FUNDO)
    plt.close(fig)
    return destino


def figura_faixas(ano: int = 2010) -> Path:
    faixas = [
        (0.000, 0.500, "Muito baixo", "#cde2fb"),
        (0.500, 0.600, "Baixo", "#9ec5f4"),
        (0.600, 0.700, "Médio", "#6da7ec"),
        (0.700, 0.800, "Alto", "#3987e5"),
        (0.800, 1.000, "Muito alto", "#1c5cab"),
    ]

    fig, ax = plt.subplots(figsize=(10, 3.4), facecolor=FUNDO)
    ax.set_facecolor(FUNDO)

    for inicio, fim, rotulo, cor in faixas:
        ax.barh(0, fim - inicio, left=inicio, height=0.34, color=cor,
                edgecolor=FUNDO, linewidth=2)
        ax.text((inicio + fim) / 2, 0, rotulo, ha="center", va="center",
                fontsize=9.5, fontweight="bold",
                color="white" if inicio >= 0.7 else TINTA)

    dados_ano = IDHM_DIMENSOES[ano]
    marcados = []
    for sigla, pessoa in PERSONAS.items():
        edu, renda, longe = dados_ano[sigla]
        idhm = (edu * renda * longe) ** (1 / 3)
        marcados.append((idhm, sigla, pessoa["nome"]))
    marcados.sort()

    # Os estados atendidos ficam muito próximos no eixo. Para que os rótulos não
    # se sobreponham, cada rótulo é afastado o mínimo necessário e ligado ao seu
    # ponto por uma linha-guia.
    espaco = 0.115
    rotulo_x = []
    for idhm, _, _ in marcados:
        alvo = idhm if not rotulo_x else max(idhm, rotulo_x[-1] + espaco)
        rotulo_x.append(alvo)
    deslocamento = ((marcados[0][0] + marcados[-1][0]) / 2) - ((rotulo_x[0] + rotulo_x[-1]) / 2)
    rotulo_x = [min(max(x + deslocamento, 0.06), 0.94) for x in rotulo_x]

    for (idhm, sigla, nome), lx in zip(marcados, rotulo_x):
        ax.plot([idhm, idhm, lx, lx], [0.17, 0.30, 0.38, 0.46],
                color=LARANJA, linewidth=1.3, solid_capstyle="round")
        ax.scatter([idhm], [0.17], s=62, color=LARANJA, zorder=5,
                   edgecolor=FUNDO, linewidth=1.6)
        ax.text(lx, 0.605, f"{sigla} · {idhm:.3f}".replace(".", ","),
                ha="center", va="bottom", fontsize=9.4, fontweight="bold", color=TINTA)
        ax.text(lx, 0.585, nome, ha="center", va="top",
                fontsize=8.6, color=TINTA2)

    ax.set_xlim(0, 1)
    ax.set_ylim(-0.32, 0.80)
    ax.set_yticks([])
    ax.set_xticks([0, 0.5, 0.6, 0.7, 0.8, 1.0])
    ax.set_xticklabels(["0", "0,500", "0,600", "0,700", "0,800", "1,000"],
                       fontsize=9, color=TINTA2)
    for lado in ("top", "right", "left"):
        ax.spines[lado].set_visible(False)
    ax.spines["bottom"].set_color("#d8d7d2")
    ax.tick_params(axis="x", length=0, pad=6)

    ax.set_title(
        f"Faixas de desenvolvimento humano do PNUD e os estados atendidos — Censo {ano}",
        fontsize=13, fontweight="bold", color=TINTA, pad=14, loc="left",
    )

    ASSETS.mkdir(parents=True, exist_ok=True)
    destino = ASSETS / "faixas_idhm.png"
    fig.savefig(destino, dpi=160, bbox_inches="tight", facecolor=FUNDO)
    plt.close(fig)
    return destino


if __name__ == "__main__":
    print("Gerado:", figura_composicao())
    print("Gerado:", figura_faixas())
    print("UFs das personas:", ", ".join(UF_NOME[s] for s in PERSONAS))
