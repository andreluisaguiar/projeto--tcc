import streamlit as st
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
import seaborn as sns
import matplotlib.pyplot as plt
from nltk.corpus import stopwords
from sklearn.ensemble import RandomForestClassifier
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier
from xgboost import XGBClassifier
from sklearn.preprocessing import LabelEncoder
import joblib
import io

# Carregar stopwords em português
stop_words = stopwords.words('portuguese')

# Função para carregar os dados
def load_data(file_path):
    data = pd.read_excel(file_path)
    data = data[data['Engenharia'] != "Não migrou"]  # Filtrar registros irrelevantes
    return data['Titulo'], data['Engenharia']

# Função para dividir os dados
def split_data(X, y, test_size=0.2, random_state=42):
    return train_test_split(X, y, test_size=test_size, random_state=random_state)

# Função para pré-processamento de texto
def preprocess_text(X_train, X_test, stop_words=None, max_features=5000):
    tfidf = TfidfVectorizer(stop_words=stop_words, max_features=max_features)
    X_train_tfidf = tfidf.fit_transform(X_train)
    X_test_tfidf = tfidf.transform(X_test)
    return X_train_tfidf, X_test_tfidf, tfidf

# Função para treinar o modelo
def train_model(X_train, y_train, algorithm='random_forest', **kwargs):
    label_encoder = LabelEncoder()
    y_train_encoded = label_encoder.fit_transform(y_train)
    
    if algorithm == 'random_forest':
        model = RandomForestClassifier(**kwargs)
    elif algorithm == 'naive_bayes':
        model = MultinomialNB(**kwargs)
    elif algorithm == 'svm':
        model = SVC(**kwargs)
    elif algorithm == 'knn':
        model = KNeighborsClassifier(**kwargs)
    elif algorithm == 'decision_tree':
        model = DecisionTreeClassifier(**kwargs)
    elif algorithm == 'xgboost':
        model = XGBClassifier(**kwargs)
    else:
        raise ValueError("Algoritmo não suportado: escolha 'random_forest', 'naive_bayes', 'svm', 'knn', 'decision_tree' ou 'xgboost'.")
    
    model.fit(X_train, y_train_encoded)
    return model, label_encoder

# Função para avaliar o modelo
def evaluate_model(model, label_encoder, X_test, y_test):
    y_test_encoded = label_encoder.transform(y_test)
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test_encoded, y_pred)
    report = classification_report(y_test_encoded, y_pred, output_dict=True)
    cm = confusion_matrix(y_test_encoded, y_pred)
    return accuracy, report, cm

# Função para salvar o modelo
def save_model(model, tfidf, label_encoder, filename="model.joblib"):
    joblib.dump({'model': model, 'tfidf': tfidf, 'label_encoder': label_encoder}, filename)
    return filename

# Função para exibir o treinamento e teste com Streamlit
def exibir_treinamento_teste():
    # Upload do arquivo Excel
    uploaded_file = st.file_uploader("Escolha um arquivo Excel", type="xlsx")
    
    if uploaded_file is not None:
        # Carregar os dados a partir do arquivo Excel
        X, y = load_data(uploaded_file)
        
        # Seleção do algoritmo de machine learning
        algorithm = st.selectbox(
            'Escolha o algoritmo',
            ('random_forest', 'naive_bayes', 'svm', 'knn', 'decision_tree', 'xgboost')
        )
        
        # Seleção do tamanho de treino/teste
        test_size_options = [0.1, 0.2, 0.3]  # 90-10, 80-20, 70-30
        test_size = st.selectbox(
            'Escolha o tamanho do split de treino/teste',
            test_size_options,
            format_func=lambda x: f'{int((1 - x) * 100)}-{int(x * 100)}'
        )

        # Pré-processamento dos dados
        X_train, X_test, y_train, y_test = split_data(X, y, test_size=test_size, random_state=42)
        X_train_tfidf, X_test_tfidf, tfidf = preprocess_text(X_train, X_test, stop_words)
        
        # Ajustar parâmetros para os algoritmos
        if algorithm == 'xgboost':
            n_estimators = st.slider('Número de Estimadores (XGBoost)', min_value=50, max_value=200, value=100, step=10)
            max_depth = st.slider('Máxima Profundidade (XGBoost)', min_value=3, max_value=10, value=6)
            learning_rate = st.slider('Taxa de Aprendizado (XGBoost)', min_value=0.01, max_value=0.3, value=0.1)
            subsample = st.slider('Subamostra (XGBoost)', min_value=0.5, max_value=1.0, value=0.8)
            kwargs = {
                'n_estimators': n_estimators,
                'max_depth': max_depth,
                'learning_rate': learning_rate,
                'subsample': subsample
            }
        else:
            kwargs = {}

        # Treinamento do modelo
        model, label_encoder = train_model(X_train_tfidf, y_train, algorithm, **kwargs)
        
        # Avaliação do modelo
        accuracy, report, cm = evaluate_model(model, label_encoder, X_test_tfidf, y_test)
        
        # Exibir resultados no Streamlit
        st.write(f"Acurácia: {accuracy:.2f}")
        
        # Exibir relatório de classificação como tabela
        st.write("Relatório de Classificação:")
        report_df = pd.DataFrame(report).transpose()
        st.dataframe(report_df)
        
        # Exibir matriz de confusão
        st.write("Matriz de Confusão:")
        fig, ax = plt.subplots()
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=label_encoder.classes_, yticklabels=label_encoder.classes_)
        plt.xlabel('Previsões')
        plt.ylabel('Verdades reais')
        st.pyplot(fig)
        
        # Salvar modelo
        save_model_path = st.text_input('Caminho para salvar o modelo', 'modelo_classificacao.joblib')
        if st.button('Salvar Modelo'):
            saved_model_path = save_model(model, tfidf, label_encoder, filename=save_model_path)
            st.write(f"Modelo salvo em: {saved_model_path}")

# Interface do Streamlit
if __name__ == "__main__":
    exibir_treinamento_teste()