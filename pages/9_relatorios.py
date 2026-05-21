"""Página: Relatórios em PDF."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.utils.db import obter_todos_tccs
from src.utils.pdf_generator import gerar_relatorio_pdf

st.set_page_config(page_title="Relatórios PDF", page_icon="🧾", layout="wide")

st.header("🧾 Relatórios PDF")
st.write(
    "Gere um relatório executivo com estatísticas consolidadas a partir da base SQLite."
)

st.divider()

df = obter_todos_tccs(incluir_outliers=False, incluir_duplicadas=False)
if df.empty:
    st.info("Carregue dados na página de Gerenciamento para habilitar a exportação do PDF.")
    st.stop()

resumo = {
    "total_registros_validos": len(df),
    "outliers_marcados": int(df["is_outlier"].sum()),
    "duplicatas_marcadas": int(df["is_duplicate"].sum()),
    "engenharias_ativas": int(df["engenharia"].nunique()),
    "orientadores_ativos": int(df["orientador"].nunique()),
}

por_engenharia = df["engenharia"].value_counts().to_dict()
por_ano = df["ano"].astype(str).value_counts().to_dict()
top_orientadores = df["orientador"].value_counts().head(10).to_dict()

estatisticas = {
    "resumo": resumo,
    "por_engenharia": por_engenharia,
    "por_ano": por_ano,
    "top_orientadores": top_orientadores,
}

st.subheader("Pré-visualização")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total", len(df))
with col2:
    st.metric("Engenharias", df["engenharia"].nunique())
with col3:
    st.metric("Orientadores", df["orientador"].nunique())

st.dataframe(df.head(25), use_container_width=True)

pdf_bytes = gerar_relatorio_pdf(
    estatisticas=estatisticas,
    outliers_detectados=resumo["outliers_marcados"],
    total_tccs=resumo["total_registros_validos"],
)

st.download_button(
    label="Baixar relatório em PDF",
    data=pdf_bytes,
    file_name="relatorio_projeto_tcc.pdf",
    mime="application/pdf",
    type="primary",
)