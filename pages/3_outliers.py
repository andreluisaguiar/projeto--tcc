import pandas as pd
import streamlit as st

from src.preprocessing.outlier_detection import detectar_outliers
from src.utils.db import atualizar_outliers, obter_todos_tccs
from src.utils.io_helpers import dataframe_to_excel_buffer, read_excel

st.set_page_config(page_title="Detecção de Outliers")

st.header("Detecção de Outliers")
st.write(
    "Identifique títulos que não correspondem semanticamente à engenharia atribuída, "
    "usando análise de similaridade com spaCy."
)

st.divider()

@st.cache_data
def cached_detectar_outliers(df: pd.DataFrame, titulo_col: str, engenharia_col: str, limiar: float):
    return detectar_outliers(df, titulo_col, engenharia_col, limiar=limiar)


df = obter_todos_tccs()
usar_db = not df.empty

if usar_db:
    st.info(f"Carregados {len(df)} registros diretamente do SQLite.")
else:
    uploaded_file = st.file_uploader("Envie o arquivo Excel", type=["xlsx"])
    if uploaded_file is not None:
        df = read_excel(uploaded_file)

if df is not None:
    st.subheader(f"Dados para análise ({len(df)} linhas)")
    st.dataframe(df, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        # Tentar pré-selecionar 'titulo'
        cols = list(df.columns)
        default_tit = cols.index("titulo") if "titulo"in cols else 0
        titulo_col = st.selectbox("Coluna de Título", cols, index=default_tit)
    with col2:
        # Tentar pré-selecionar 'engenharia'
        default_eng = cols.index("engenharia") if "engenharia"in cols else 0
        engenharia_col = st.selectbox("Coluna de Engenharia", cols, index=default_eng)

    # Validações
    if titulo_col == engenharia_col:
        st.error("As colunas de título e engenharia não podem ser as mesmas.")
    elif titulo_col.lower() != "titulo"or engenharia_col.lower() != "engenharia":
        st.error("As colunas devem ser 'titulo' e 'engenharia'.")
    else:
        limiar = st.slider(
            "Limiar de similaridade",
            min_value=0.1,
            max_value=0.9,
            value=0.3,
            step=0.05,
            help="Títulos com similaridade abaixo deste valor são considerados outliers.",
        )

        # Inicializar estados de resultado
        if "outliers_result"not in st.session_state:
            st.session_state["outliers_result"] = None

        if st.button("Detectar Outliers", type="primary"):
            with st.spinner("Calculando similaridades semânticas... Isso pode levar alguns segundos."):
                df_outliers, df_sem_outliers = cached_detectar_outliers(
                    df, titulo_col, engenharia_col, limiar=limiar
                )
                st.session_state["outliers_result"] = {
                    "outliers": df_outliers,
                    "sem_outliers": df_sem_outliers
                }

        # Exibir resultados se existirem no session_state
        res = st.session_state["outliers_result"]
        if res is not None:
            df_outliers = res["outliers"]
            df_sem_outliers = res["sem_outliers"]

            # Resultados
            col_a, col_b = st.columns(2)
            with col_a:
                st.metric("Outliers", len(df_outliers))
            with col_b:
                st.metric("Dados válidos", len(df_sem_outliers))

            st.subheader("Outliers detectados")
            st.dataframe(df_outliers, use_container_width=True)

            st.subheader("Dados sem outliers")
            st.dataframe(df_sem_outliers, use_container_width=True)

            st.divider()

            if usar_db:
                st.subheader("Persistência no SQLite")
                st.write("Marque as monografias identificadas acima como outliers no banco SQLite:")
                if st.button("Gravar Outliers no Banco de Dados", type="primary"):
                    with st.spinner("Gravando no banco..."):
                        alterados = atualizar_outliers(df_outliers[titulo_col].tolist())
                    st.success(f"{alterados} outliers gravados e persistidos no banco de dados!")
                st.write("---")

            col_dl1, col_dl2 = st.columns(2)
            with col_dl1:
                st.download_button(
                    label="Baixar Outliers (Excel)",
                    data=dataframe_to_excel_buffer(df_outliers),
                    file_name="outliers_detectados.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            with col_dl2:
                st.download_button(
                    label="Baixar Dados Limpos (Excel)",
                    data=dataframe_to_excel_buffer(df_sem_outliers),
                    file_name="dados_sem_outliers.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )

