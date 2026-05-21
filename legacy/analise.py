# analise.py

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import classification_report, accuracy_score
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBClassifier
from imblearn.over_sampling import SMOTE
import streamlit as st
import seaborn as sns
import matplotlib.pyplot as plt

# Função para análise preditiva
def analise_predicao(dados):
    st.title("Análise preditiva das engenharias cursadas após BICT")
    
    # Verificação das colunas esperadas
    if {'titulo', 'engenharia'}.issubset(dados.columns):
        # Visualização inicial: distribuição das engenharias
        st.subheader("Distribuição das engenharias")
        distrib_eng = dados['engenharia'].value_counts()
        st.bar_chart(distrib_eng)

        # Features e Target
        X = dados['titulo']
        y = dados['engenharia']

        # Codificar as classes como números para compatibilidade com modelos
        le = LabelEncoder()
        y_encoded = le.fit_transform(y)

        # Vetorização com TF-IDF
        tfidf = TfidfVectorizer(max_features=500, min_df=2, max_df=0.8, stop_words='english')
        X_tfidf = tfidf.fit_transform(X)

        # Tratamento de desbalanceamento com SMOTE
        smote = SMOTE(random_state=42)
        X_balanced, y_balanced = smote.fit_resample(X_tfidf, y_encoded)

        # Divisão dos dados
        X_train, X_test, y_train, y_test = train_test_split(X_balanced, y_balanced, test_size=0.2, random_state=42)

        # Modelos a serem avaliados
        models = {
            "Random Forest": RandomForestClassifier(n_estimators=100, class_weight='balanced', random_state=42),
            "XGBoost": XGBClassifier(use_label_encoder=False, eval_metric='mlogloss', enable_categorical=False, random_state=42)
        }

        resultados = {}

        for nome, modelo in models.items():
            try:
                # Validação cruzada
                scores = cross_val_score(modelo, X_train, y_train, cv=5, scoring='accuracy', error_score='raise')
                modelo.fit(X_train, y_train)
                y_pred = modelo.predict(X_test)
                report = classification_report(y_test, y_pred, output_dict=True, target_names=le.classes_)

                resultados[nome] = {
                    "Acurácia Média (Validação Cruzada)": np.mean(scores),
                    "Acurácia no Teste": accuracy_score(y_test, y_pred),
                    "Relatório de Classificação": report
                }
            except Exception as e:
                st.error(f"Erro no modelo {nome}: {e}")

        # Exibição dos dados com probabilidades
        st.subheader("Dados com Probabilidades")
        prob_df_combined = pd.DataFrame(
            (models["Random Forest"].predict_proba(X_balanced) + models["XGBoost"].predict_proba(X_balanced)) / 2,
            columns=[f"Prob_{engenharia}" for engenharia in le.classes_]
        )
        dados_prob = pd.concat([dados.reset_index(), prob_df_combined], axis=1)
        st.dataframe(dados_prob)


        # Exibição dos resultados do Random Forest
        st.subheader("Resultados do Modelo Random Forest")
        st.write(f"Acurácia Média (Validação Cruzada): {resultados['Random Forest']['Acurácia Média (Validação Cruzada)']:.2f}")
        st.write(f"Acurácia no Teste: {resultados['Random Forest']['Acurácia no Teste']:.2f}")

        # Exibição dos resultados do XGBoost
        st.subheader("Resultados do Modelo XGBoost")
        st.write(f"Acurácia Média (Validação Cruzada): {resultados['XGBoost']['Acurácia Média (Validação Cruzada)']:.2f}")
        st.write(f"Acurácia no Teste: {resultados['XGBoost']['Acurácia no Teste']:.2f}")

        melhor_modelo = max(resultados, key=lambda x: resultados[x]['Acurácia Média (Validação Cruzada)'])
        st.subheader(f"O Modelo com maior precisão: {melhor_modelo}")
        st.write(f"Acurácia Média (Validação Cruzada): {resultados[melhor_modelo]['Acurácia Média (Validação Cruzada)']:.2f}")
        st.write(f"Acurácia no Teste: {resultados[melhor_modelo]['Acurácia no Teste']:.2f}")

        # Convertendo o relatório de classificação em DataFrame
        relatorio_df = pd.DataFrame(resultados[melhor_modelo]['Relatório de Classificação']).T
        relatorio_df = relatorio_df.reset_index().rename(columns={
            "index": "engenharia",
            "precision": "Precisão",
            "recall": "Revocação",
            "f1-score": "F1-Score",
            "support": "Suporte"
        })

        # Exibindo o relatório em formato de tabela
        st.subheader("Relatório de Classificação")
        st.dataframe(relatorio_df)

        # Probabilidade com base no título (combinação dos modelos)
        st.subheader("Probabilidade por Título")
        titulo_exemplo = st.text_input("Digite um título para prever a probabilidade de qual engenharia será escolhida:")
        if titulo_exemplo:
            titulo_tfidf = tfidf.transform([titulo_exemplo])

            # Calcular probabilidades para ambos os modelos
            prob_rf = models["Random Forest"].predict_proba(titulo_tfidf)
            prob_xgb = models["XGBoost"].predict_proba(titulo_tfidf)

            # Combinar as probabilidades (média simples)
            prob_combined = (prob_rf + prob_xgb) / 2
            prob_df = pd.DataFrame(prob_combined, columns=le.classes_)

            st.write("Probabilidades combinadas de escolha de engenharia com base no título:")
            st.write(prob_df.T.rename(columns={0: "Probabilidade"}).sort_values(by="Probabilidade", ascending=False))

        # Download dos dados tratados
        st.subheader("Download dos Dados com Probabilidades")
        dados_prob.to_excel("dados_com_probabilidades.xlsx", index=False)
        with open("dados_com_probabilidades.xlsx", "rb") as file:
            st.download_button(
                label="Baixar os Dados com Probabilidades",
                data=file,
                file_name="dados_com_probabilidades.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    else:
        st.error("Certifique-se de que o arquivo contém as colunas 'titulo' e 'engenharia'.")
