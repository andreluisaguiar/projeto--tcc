"""Página: Remoção de Duplicatas."""

import streamlit as st
from src.preprocessing.deduplication import remover_duplicatas
from src.utils.io_helpers import merge_excel_files, dataframe_to_excel_buffer

st.set_page_config(page_title="Remoção de Duplicatas", page_icon="🧹")

st.header("🧹 Remoção de Duplicatas")
st.write(
    "Carregue um ou mais arquivos Excel para combinar e remover registros duplicados."
)

st.divider()

uploaded_files = st.file_uploader(
    "📁 Carregar arquivos Excel",
    type=["xlsx"],
    accept_multiple_files=True,
)

if uploaded_files:
    with st.spinner("Carregando e combinando arquivos..."):
        df_combinado = merge_excel_files(uploaded_files)

    st.subheader(f"📊 Dados Combinados ({len(df_combinado)} linhas)")
    st.dataframe(df_combinado, use_container_width=True)

    if st.button("🧹 Remover Duplicatas", type="primary"):
        df_sem_duplicatas = remover_duplicatas(df_combinado)
        removidas = len(df_combinado) - len(df_sem_duplicatas)

        if removidas > 0:
            st.success(f"✅ {removidas} duplicatas removidas!")
        else:
            st.info("ℹ️ Nenhuma duplicata encontrada.")

        st.subheader(f"📊 Dados sem Duplicatas ({len(df_sem_duplicatas)} linhas)")
        st.dataframe(df_sem_duplicatas, use_container_width=True)

        # Download
        buffer = dataframe_to_excel_buffer(df_sem_duplicatas)
        st.download_button(
            label="📄 Baixar Arquivo sem Duplicatas",
            data=buffer,
            file_name="dataset_sem_duplicatas.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary",
        )
