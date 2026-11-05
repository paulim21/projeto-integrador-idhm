"""
Números que Falam — Descobrindo o Brasil
Seção individual: Índice de Desenvolvimento Humano (IDH / IDHM)

Como rodar:
    pip install -r requirements.txt
    python scripts/gerar_base_bruta.py     (só na primeira vez)
    python scripts/gerar_imagens.py        (só na primeira vez)
    streamlit run app.py
"""

from __future__ import annotations

import streamlit as st

from secao_idhm import SUBTITULO, TITULO, renderizar_secao

st.set_page_config(
    page_title="IDHM · Números que Falam",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


def pagina_sobre() -> None:
    st.title("Sobre esta seção")
    st.markdown(f"**Tema individual:** {TITULO}")
    st.markdown(SUBTITULO)

    st.markdown(
        """
        ### Gestores atendidos (personas)

        | Persona | Cargo | UF |
        |---|---|---|
        | João | Governador do Maranhão | MA |
        | Helder | Governador do Pará | PA |
        | Gladson | Governador do Acre | AC |
        | Susu | Governador da Bahia | BA |
        | Verinha | Governadora de Minas Gerais | MG |

        ### Perguntas de negócio que o painel responde

        1. Qual das três dimensões do IDHM puxa o índice para baixo em cada estado?
        2. Quanto o IDHM do estado subiria se só esse gargalo fosse corrigido?
        3. Qual a evolução do IDHM desde os anos 2000 até o dado mais recente?
        4. Quais municípios têm os menores e os maiores índices, e qual é a dispersão
           (IQR e desvio padrão) dentro de cada estado?
        5. Existem estados ou municípios tão distantes do conjunto que se caracterizam
           como outliers pela regra de 1,5 × IQR?
        6. Existe correlação entre o IDHM e o investimento público por habitante?
        7. Como ratear um Fundo Regional de Redução de Desigualdades com critério auditável?

        ### Como a seção entra no painel do grupo

        ```python
        import streamlit as st
        from secao_idhm import renderizar_secao

        secao = st.sidebar.radio("Seções", [..., "IDH / IDHM", ...])
        if secao == "IDH / IDHM":
            renderizar_secao()          # com os próprios filtros na barra lateral
            # ou renderizar_secao(usar_sidebar=False) para usar os filtros do grupo
        ```

        ### Estrutura do código

        | Arquivo | Responsabilidade |
        |---|---|
        | `src/dados_fonte.py` | base estadual de referência, metadados de UF e personas |
        | `src/etl.py` | extração, limpeza, validação e enriquecimento (com log), estadual e municipal |
        | `src/estatistica.py` | média, mediana, moda, quartis, IQR, amplitude, desvio padrão, outliers |
        | `src/graficos.py` | todos os gráficos, com paleta e regras de leitura fixas |
        | `src/personas.py` | diagnóstico por gestor e simulador do fundo regional |
        | `secao_idhm.py` | a seção do dashboard (abas, filtros, textos) |
        | `app.py` | aplicação Streamlit individual |
        | `scripts/gerar_base_bruta.py` | grava o CSV estadual bruto, com os problemas típicos de extração |
        | `scripts/preparar_base_municipal.py` | recorta a base municipal do Atlas Brasil |
        | `scripts/preparar_serie_recente.py` | extrai a série 2012–2024 do Radar IDHM |
        | `scripts/coletar_investimento_publico.py` | consome a API do Siconfi / Tesouro Nacional |
        | `scripts/gerar_imagens.py` | desenha as figuras explicativas de `assets/` |

        ### Fontes dos dados

        | Base | Fonte |
        |---|---|
        | IDHM por UF e por município, Censos de 1991, 2000 e 2010 | Atlas do Desenvolvimento Humano no Brasil — PNUD / Ipea / Fundação João Pinheiro |
        | IDHM por UF, série anual de 2012 a 2024 | Radar IDHM — PNUD, Fundação João Pinheiro e IBGE |
        | Despesa pública estadual por função | Siconfi — Secretaria do Tesouro Nacional (DCA, Anexo I-E) |
        | Variáveis de origem do índice | IBGE — Censo Demográfico |

        As duas séries de IDHM **não são comparáveis linha a linha**: a de 1991–2010 é
        censitária e a de 2012–2024 é estimada pela PNAD Contínua, com metodologia
        revisada. O painel as mantém separadas e avisa o leitor.
        """
    )


def main() -> None:
    st.sidebar.markdown("## Números que Falam")
    st.sidebar.caption("Descobrindo o Brasil · projeto integrador")

    pagina = st.sidebar.radio(
        "Navegação",
        ["Dashboard — IDH / IDHM", "Sobre esta seção"],
        key="nav_principal",
    )
    st.sidebar.markdown("---")

    if pagina == "Dashboard — IDH / IDHM":
        renderizar_secao(usar_sidebar=True)
    else:
        pagina_sobre()


if __name__ == "__main__":
    main()
