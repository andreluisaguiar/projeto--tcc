"""Página: Busca Semântica de TCCs."""

from __future__ import annotations

import streamlit as st

from src.preprocessing.search import buscar_titulos_similares
from src.utils.db import obter_todos_tccs

st.set_page_config(page_title="Busca Semântica", page_icon="🔎", layout="wide")

st.header("🔎 Busca Semântica de Títulos")
st.write(
    "Pesquise TCCs por similaridade semântica usando os vetores nativos do spaCy e a base persistida no SQLite."
)

st.divider()

base = obter_todos_tccs(incluir_outliers=False, incluir_duplicadas=False)
if base.empty:
    st.info("Carregue dados na página de Gerenciamento para habilitar a busca.")
    st.stop()

col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    query = st.text_input(
        "Digite o tema, problema ou palavras-chave do TCC",
        placeholder="Ex: eficiência energética em sistemas fotovoltaicos",
    )
with col2:
    limite = st.slider("Limite de resultados", 1, 20, 5)
with col3:
    limiar = st.slider("Similaridade mínima", 0.0, 1.0, 0.45, 0.05)

colf1, colf2 = st.columns(2)
with colf1:
    filtro_engenharia = st.selectbox(
        "Filtrar por engenharia",
        ["Todas"] + sorted(base["engenharia"].dropna().astype(str).unique().tolist()),
    )
with colf2:
    filtro_ano = st.selectbox(
        "Filtrar por ano",
        ["Todos"] + sorted(base["ano"].dropna().astype(str).unique().tolist()),
    )

if st.button("Buscar", type="primary"):
    if not query.strip():
        st.warning("Digite uma consulta antes de buscar.")
    else:
        resultados = buscar_titulos_similares(
            query=query,
            limit=limite,
            limiar_minimo=limiar,
            filtro_engenharia=filtro_engenharia,
            filtro_ano=filtro_ano,
        )

        if resultados.empty:
            st.info("Nenhum resultado atingiu o limiar configurado.")
        else:
            st.success(f"{len(resultados)} resultados encontrados.")
            st.dataframe(resultados, use_container_width=True)

            st.subheader("Resultados em cards")
            for _, row in resultados.iterrows():
                with st.container(border=True):
                    st.markdown(f"### {row['titulo']}")
                    st.write(f"**Engenharia:** {row['engenharia']}")
                    st.write(f"**Orientador:** {row.get('orientador', 'Não Informado')}")
                    st.write(f"**Ano:** {row.get('ano', 'Não Informado')}")
                    st.metric("Similaridade", f"{row['similaridade']:.2%}")