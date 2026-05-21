"""Página: Gerenciamento de Dados (Banco SQLite)."""

from __future__ import annotations

import streamlit as st

from src.utils.db import inicializar_db, limpar_banco, obter_todos_tccs, salvar_dataframe_tccs
from src.utils.io_helpers import read_excel

st.set_page_config(page_title="Gerenciamento de Dados", page_icon="⚙️", layout="wide")

st.header("⚙️ Gerenciamento do Banco de Dados SQLite")
st.write(
    "Importe a planilha inicial uma única vez para alimentar o banco SQLite e usar a base persistente nas demais páginas."
)

st.divider()
inicializar_db()

df_atual = obter_todos_tccs()
total_registros = len(df_atual)
outliers_count = int(df_atual["is_outlier"].sum()) if total_registros > 0 else 0
duplicates_count = int(df_atual["is_duplicate"].sum()) if total_registros > 0 else 0

col_stat1, col_stat2, col_stat3 = st.columns(3)
with col_stat1:
    st.metric("Total de Trabalhos no Banco", total_registros)
with col_stat2:
    st.metric("Outliers Marcados", outliers_count)
with col_stat3:
    st.metric("Duplicatas Marcadas", duplicates_count)

st.divider()
st.subheader("📥 Importar dados para o SQLite")
uploaded_file = st.file_uploader("Carregar arquivo Excel", type=["xlsx"])

if uploaded_file is not None:
    try:
        df_import = read_excel(uploaded_file)
        st.success("✅ Planilha lida com sucesso!")
        st.dataframe(df_import.head(10), use_container_width=True)

        if st.button("🚀 Confirmar Importação", type="primary"):
            with st.spinner("Importando registros no SQLite..."):
                inseridos, ignorados = salvar_dataframe_tccs(df_import)

            st.success("🎉 Importação concluída.")
            st.info(f"{inseridos} novos trabalhos salvos. {ignorados} duplicatas ignoradas.")
            st.rerun()
    except Exception as exc:
        st.error(f"❌ Falha ao processar ou salvar o arquivo: {exc}")

st.divider()
st.subheader("📂 Registros no Banco de Dados")

if total_registros > 0:
    st.dataframe(df_atual.head(50), use_container_width=True)
    st.write("---")
    st.subheader("🚨 Zona de Perigo")
    st.write("Apague definitivamente todas as monografias do banco de dados local.")

    confirm_reset = st.checkbox("Confirmar que desejo apagar toda a base de dados do SQLite.")
    if st.button("🔴 Limpar Banco de Dados", type="primary", disabled=not confirm_reset):
        deleted = limpar_banco()
        st.success(f"💥 Banco de dados limpo com sucesso! {deleted} registros apagados.")
        st.rerun()
else:
    st.info("💡 O banco de dados está vazio. Carregue um Excel acima para começar.")
