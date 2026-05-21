"""Página: Detecção de Outliers."""

import streamlit as st
import pandas as pd
from src.preprocessing.outlier_detection import detectar_outliers
from src.utils.io_helpers import dataframe_to_excel_buffer

st.set_page_config(page_title="Detecção de Outliers", page_icon="🔍")

st.header("🔍 Detecção de Outliers")
st.write(
    "Identifique títulos que não correspondem semanticamente à engenharia atribuída, "
    "usando análise de similaridade com spaCy."
)

st.divider()

uploaded_file = st.file_uploader("📁 Envie o arquivo Excel", type=["xlsx"])

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)

    st.subheader(f"📊 Dados carregados ({len(df)} linhas)")
    st.dataframe(df, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        titulo_col = st.selectbox("Coluna de Título", df.columns)
    with col2:
        engenharia_col = st.selectbox("Coluna de Engenharia", df.columns)

    # Validações
    if titulo_col == engenharia_col:
        st.error("❌ As colunas de título e engenharia não podem ser as mesmas.")
    elif titulo_col.lower() != "titulo" or engenharia_col.lower() != "engenharia":
        st.error("❌ As colunas devem ser 'titulo' e 'engenharia'.")
    else:
        limiar = st.slider(
            "Limiar de similaridade",
            min_value=0.1,
            max_value=0.9,
            value=0.3,
            step=0.05,
            help="Títulos com similaridade abaixo deste valor são considerados outliers.",
        )

        if st.button("🔍 Detectar Outliers", type="primary"):
            with st.spinner("Calculando similaridades semânticas... Isso pode levar alguns segundos."):
                df_outliers, df_sem_outliers = detectar_outliers(
                    df, titulo_col, engenharia_col, limiar=limiar
                )

            # Resultados
            col_a, col_b = st.columns(2)
            with col_a:
                st.metric("Outliers", len(df_outliers))
            with col_b:
                st.metric("Dados válidos", len(df_sem_outliers))

            st.subheader("⚠️ Outliers detectados")
            st.dataframe(df_outliers, use_container_width=True)

            st.subheader("✅ Dados sem outliers")
            st.dataframe(df_sem_outliers, use_container_width=True)

            # Downloads
            col_dl1, col_dl2 = st.columns(2)
            with col_dl1:
                st.download_button(
                    label="📄 Baixar Outliers",
                    data=dataframe_to_excel_buffer(df_outliers),
                    file_name="outliers_detectados.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            with col_dl2:
                st.download_button(
                    label="📄 Baixar Dados Limpos",
                    data=dataframe_to_excel_buffer(df_sem_outliers),
                    file_name="dados_sem_outliers.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
