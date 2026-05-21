# previsao.py

import joblib
import streamlit as st

# Função para prever nova engenharia com base no título
def prever_titulo(titulo_novo):
    # Carregar os objetos salvos
    modelo_rf = joblib.load("modelo_random_forest.pkl")
    modelo_xgb = joblib.load("modelo_xgboost.pkl")
    tfidf = joblib.load("tfidf_vectorizer.pkl")
    le = joblib.load("label_encoder.pkl")

    # Transformar o título novo usando o TF-IDF
    titulo_tfidf = tfidf.transform([titulo_novo])

    # Realizar previsões com ambos os modelos
    previsao_rf = modelo_rf.predict(titulo_tfidf)
    previsao_xgb = modelo_xgb.predict(titulo_tfidf)

    # Decodificar a previsão
    engenharia_rf = le.inverse_transform(previsao_rf)[0]
    engenharia_xgb = le.inverse_transform(previsao_xgb)[0]

    return engenharia_rf, engenharia_xgb

# Streamlit para capturar input do usuário e exibir a previsão
st.title("Previsão de Engenharia com Base no Título")
titulo_input = st.text_input("Digite o título:", "")

if titulo_input:
    engenharia_rf, engenharia_xgb = prever_titulo(titulo_input)
    st.write(f"Previsão com Random Forest: {engenharia_rf}")
    st.write(f"Previsão com XGBoost: {engenharia_xgb}")
