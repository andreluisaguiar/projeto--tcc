"""Página: Treinamento e Predição."""

import streamlit as st
import pandas as pd

from src.models.trainer import treinar_pipeline_predicao, calcular_probabilidades_combinadas
from src.models.evaluator import relatorio_para_dataframe
from src.models.predictor import prever_engenharia
from src.utils.io_helpers import dataframe_to_excel_buffer

st.set_page_config(page_title="Treinamento e Predição", page_icon="🎯")

st.header("🎯 Treinamento e Predição")
st.write(
    "Treine modelos (Random Forest + XGBoost) e faça predições de engenharia "
    "com base no título da monografia."
)

st.divider()

uploaded_file = st.file_uploader("📁 Envie o arquivo Excel", type=["xlsx"])

@st.cache_resource
def cached_treinar_pipeline_predicao(df: pd.DataFrame):
    return treinar_pipeline_predicao(df)


if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)

    # Verificar colunas necessárias
    if not {"titulo", "engenharia"}.issubset(df.columns):
        st.error("❌ O arquivo deve conter as colunas 'titulo' e 'engenharia'.")
        st.stop()

    st.info(f"📊 {len(df)} registros carregados")

    # Distribuição das engenharias
    st.subheader("📊 Distribuição das Engenharias")
    st.bar_chart(df["engenharia"].value_counts())

    # Inicializar ou carregar resultado do cache / session_state
    resultado = None
    if "resultado_predicao" in st.session_state:
        resultado = st.session_state["resultado_predicao"]

    if st.button("🚀 Treinar Modelos", type="primary"):
        with st.spinner("Treinando/Carregando modelos (Random Forest + XGBoost)..."):
            try:
                # Usar a versão cacheada
                resultado = cached_treinar_pipeline_predicao(df)
                st.session_state["resultado_predicao"] = resultado
            except ValueError as e:
                st.error(f"❌ {e}")
                st.stop()

    if resultado is not None:
        # Exibir resultados
        st.success("✅ Treinamento concluído!")

        for algo, res in resultado["resultados"].items():
            if "erro" in res:
                st.error(f"❌ {res['nome']}: {res['erro']}")
                continue

            st.subheader(f"📈 {res['nome']}")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Acurácia CV", f"{res['acuracia_cv']:.2%}")
            with col2:
                st.metric("Acurácia Teste", f"{res['acuracia_teste']:.2%}")

        # Melhor modelo
        if resultado["melhor_algoritmo"]:
            melhor = resultado["resultados"][resultado["melhor_algoritmo"]]
            st.subheader(f"🏆 Melhor Modelo: {melhor['nome']}")

            # Relatório de classificação
            relatorio_df = relatorio_para_dataframe(melhor["relatorio"])
            st.dataframe(relatorio_df, use_container_width=True)

        # Dados com probabilidades
        st.subheader("📊 Dados com Probabilidades")
        prob_df = calcular_probabilidades_combinadas(
            resultado["modelos"],
            resultado["X_tfidf_completo"],
            resultado["classes"],
        )
        dados_prob = pd.concat([df.reset_index(drop=True), prob_df], axis=1)
        st.dataframe(dados_prob, use_container_width=True)

        # Download — CORRIGIDO: usa BytesIO ao invés de salvar em disco
        buffer = dataframe_to_excel_buffer(dados_prob)
        st.download_button(
            label="📄 Baixar Dados com Probabilidades",
            data=buffer,
            file_name="dados_com_probabilidades.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary",
        )

    # ─── Predição por título ──────────────────────────────────────────────
    st.divider()
    st.subheader("🔮 Predição por Título")

    if "resultado_predicao" in st.session_state:
        resultado = st.session_state["resultado_predicao"]

        titulo_input = st.text_input(
            "Digite um título para prever a engenharia:",
            placeholder="Ex: Análise de eficiência energética em sistemas fotovoltaicos",
        )

        if titulo_input:
            prob_titulo = prever_engenharia(
                titulo_input,
                resultado["modelos"],
                resultado["tfidf"],
                resultado["label_encoder"],
            )

            # Calcular média dos modelos
            prob_titulo["Média"] = prob_titulo.mean(axis=1)
            prob_titulo = prob_titulo.sort_values("Média", ascending=False)

            st.write("**Probabilidades por engenharia:**")
            st.dataframe(
                prob_titulo.style.format("{:.2%}").highlight_max(axis=0),
                use_container_width=True,
            )

            # Destaque da predição
            eng_predita = prob_titulo["Média"].idxmax()
            prob_max = prob_titulo["Média"].max()
            st.success(f"🎯 Engenharia predita: **{eng_predita}** (confiança: {prob_max:.1%})")
    else:
        st.info("ℹ️ Treine os modelos primeiro para usar a predição por título.")
