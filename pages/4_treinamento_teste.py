"""Página: Treinamento e Teste de Algoritmos."""

import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

from src.models.registry import list_algorithms, get_display_name, get_algorithm
from src.models.evaluator import avaliar_modelo, relatorio_para_dataframe
from src.models.predictor import salvar_modelo
from src.preprocessing.text_processor import get_portuguese_stopwords
from src.utils.io_helpers import read_excel

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder

st.set_page_config(page_title="Treinamento e Teste", page_icon="🧪")

st.header("🧪 Treinamento e Teste de Algoritmos")
st.write(
    "Compare diferentes algoritmos de Machine Learning com diferentes "
    "configurações de treino/teste."
)

st.divider()

uploaded_file = st.file_uploader("📁 Escolha um arquivo Excel", type="xlsx")

if uploaded_file is not None:
    data = pd.read_excel(uploaded_file)

    # Filtrar registros irrelevantes
    if "Engenharia" in data.columns:
        eng_col = "Engenharia"
    elif "engenharia" in data.columns:
        eng_col = "engenharia"
    else:
        st.error("❌ Coluna 'Engenharia' não encontrada no arquivo.")
        st.stop()

    if "Titulo" in data.columns:
        tit_col = "Titulo"
    elif "titulo" in data.columns:
        tit_col = "titulo"
    else:
        st.error("❌ Coluna 'Titulo' não encontrada no arquivo.")
        st.stop()

    data = data[data[eng_col] != "Não migrou"]
    X = data[tit_col]
    y = data[eng_col]

    st.info(f"📊 {len(data)} registros carregados ({y.nunique()} classes)")

    # ─── Configurações ────────────────────────────────────────────────────
    col1, col2 = st.columns(2)

    with col1:
        algos = list_algorithms()
        algo_selecionado = st.selectbox(
            "🤖 Algoritmo",
            algos,
            format_func=get_display_name,
        )

    with col2:
        test_size_options = [0.1, 0.2, 0.3]
        test_size = st.selectbox(
            "📐 Split Treino/Teste",
            test_size_options,
            index=1,
            format_func=lambda x: f"{int((1 - x) * 100)}-{int(x * 100)}",
        )

    # Parâmetros específicos do XGBoost
    kwargs = {}
    if algo_selecionado == "xgboost":
        st.subheader("⚙️ Parâmetros do XGBoost")
        col_a, col_b = st.columns(2)
        with col_a:
            kwargs["n_estimators"] = st.slider("Estimadores", 50, 200, 100, 10)
            kwargs["max_depth"] = st.slider("Profundidade máxima", 3, 10, 6)
        with col_b:
            kwargs["learning_rate"] = st.slider("Taxa de aprendizado", 0.01, 0.3, 0.1)
            kwargs["subsample"] = st.slider("Subamostra", 0.5, 1.0, 0.8)

    if st.button("🚀 Treinar e Avaliar", type="primary"):
        with st.spinner(f"Treinando {get_display_name(algo_selecionado)}..."):
            # Pré-processamento
            stop_words = get_portuguese_stopwords()
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=42
            )

            tfidf = TfidfVectorizer(stop_words=stop_words, max_features=5000)
            X_train_tfidf = tfidf.fit_transform(X_train)
            X_test_tfidf = tfidf.transform(X_test)

            # Treinar
            label_encoder = LabelEncoder()
            y_train_encoded = label_encoder.fit_transform(y_train)
            y_test_encoded = label_encoder.transform(y_test)

            modelo = get_algorithm(algo_selecionado, **kwargs)
            modelo.fit(X_train_tfidf, y_train_encoded)

            # Avaliar
            resultado = avaliar_modelo(modelo, label_encoder, X_test_tfidf, y_test)

        # ─── Resultados ───────────────────────────────────────────────────
        st.success(f"✅ Treinamento concluído!")

        st.metric("Acurácia", f"{resultado['acuracia']:.2%}")

        # Relatório de classificação
        st.subheader("📋 Relatório de Classificação")
        report_df = relatorio_para_dataframe(resultado["relatorio"])
        st.dataframe(report_df, use_container_width=True)

        # Matriz de confusão
        st.subheader("🔢 Matriz de Confusão")
        fig, ax = plt.subplots(figsize=(8, 6))
        sns.heatmap(
            resultado["matriz_confusao"],
            annot=True,
            fmt="d",
            cmap="Blues",
            xticklabels=label_encoder.classes_,
            yticklabels=label_encoder.classes_,
            ax=ax,
        )
        ax.set_xlabel("Previsões")
        ax.set_ylabel("Valores Reais")
        st.pyplot(fig)

        # Salvar modelo
        st.divider()
        st.subheader("💾 Salvar Modelo")
        save_path = st.text_input(
            "Caminho do arquivo",
            value="data/models/modelo_classificacao.joblib",
        )
        if st.button("💾 Salvar"):
            saved = salvar_modelo(modelo, tfidf, label_encoder, filepath=save_path)
            st.success(f"✅ Modelo salvo em: {saved}")
