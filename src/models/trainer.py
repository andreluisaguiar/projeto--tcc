"""Pipeline de treinamento de modelos de classificação.

CORREÇÕES APLICADAS em relação ao código original:
1. SMOTE é aplicado APÓS o train_test_split (evita data leakage)
2. Stop words configuradas para PORTUGUÊS (era 'english')
3. Lógica completamente desacoplada do Streamlit
"""

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
from imblearn.over_sampling import SMOTE

from src.config import (
    TFIDF_MAX_FEATURES,
    TFIDF_MIN_DF,
    TFIDF_MAX_DF,
    TEST_SIZE,
    RANDOM_STATE,
    SMOTE_RANDOM_STATE,
    get_stopwords_pt,
)
from src.models.registry import get_algorithm, get_display_name
from src.models.evaluator import avaliar_modelo, validacao_cruzada
from src.utils.logging_config import logger


def treinar_pipeline_predicao(
    dados: pd.DataFrame,
    algoritmos: list[str] | None = None,
    usar_smote: bool = True,
    test_size: float = TEST_SIZE,
) -> dict:
    """Executa o pipeline completo de treinamento e avaliação.

    Pipeline:
    1. Extração de features (TF-IDF com stopwords PT)
    2. Train/Test split
    3. SMOTE no conjunto de TREINO apenas (sem data leakage)
    4. Treinamento e avaliação de múltiplos modelos
    5. Cálculo de probabilidades combinadas

    Args:
        dados: DataFrame com colunas 'titulo' e 'engenharia'.
        algoritmos: Lista de nomes de algoritmos (default: RF + XGBoost).
        usar_smote: Se True, aplica SMOTE para balanceamento.
        test_size: Proporção do conjunto de teste.

    Returns:
        Dict com modelos treinados, resultados, probabilidades, e objetos auxiliares.

    Raises:
        ValueError: Se as colunas necessárias não existirem nos dados.
    """
    # Validação das colunas
    colunas_necessarias = {"titulo", "engenharia"}
    if not colunas_necessarias.issubset(dados.columns):
        colunas_faltando = colunas_necessarias - set(dados.columns)
        raise ValueError(
            f"Colunas ausentes no DataFrame: {colunas_faltando}. "
            f"Colunas disponíveis: {list(dados.columns)}"
        )

    if algoritmos is None:
        algoritmos = ["random_forest", "xgboost"]

    X = dados["titulo"]
    y = dados["engenharia"]

    # Codificar as classes
    le = LabelEncoder()
    y_encoded = le.fit_transform(y)
    logger.info("Classes encontradas: %s", list(le.classes_))

    # Vetorização com TF-IDF — CORRIGIDO: stopwords em PORTUGUÊS
    stopwords_pt = get_stopwords_pt()
    tfidf = TfidfVectorizer(
        max_features=TFIDF_MAX_FEATURES,
        min_df=TFIDF_MIN_DF,
        max_df=TFIDF_MAX_DF,
        stop_words=stopwords_pt,
    )
    X_tfidf = tfidf.fit_transform(X)
    logger.info("TF-IDF: %d features extraídas", X_tfidf.shape[1])

    # CORRIGIDO: Split ANTES do SMOTE para evitar data leakage
    X_train, X_test, y_train, y_test = train_test_split(
        X_tfidf, y_encoded, test_size=test_size, random_state=RANDOM_STATE
    )
    logger.info("Split: treino=%d, teste=%d", X_train.shape[0], X_test.shape[0])

    # SMOTE aplicado SOMENTE no conjunto de treino
    if usar_smote:
        smote = SMOTE(random_state=SMOTE_RANDOM_STATE)
        X_train, y_train = smote.fit_resample(X_train, y_train)
        logger.info("SMOTE aplicado: treino balanceado=%d amostras", X_train.shape[0])

    # Treinar e avaliar cada modelo
    modelos_treinados = {}
    resultados = {}

    for nome_algo in algoritmos:
        nome_display = get_display_name(nome_algo)
        logger.info("Treinando modelo: %s", nome_display)

        try:
            modelo = get_algorithm(nome_algo)

            # Validação cruzada
            cv_result = validacao_cruzada(modelo, X_train, y_train)

            # Treinar no conjunto completo de treino
            modelo.fit(X_train, y_train)

            # Avaliar no conjunto de teste
            eval_result = avaliar_modelo(modelo, le, X_test, y_test)

            modelos_treinados[nome_algo] = modelo
            resultados[nome_algo] = {
                "nome": nome_display,
                "acuracia_cv": cv_result["media"],
                "desvio_cv": cv_result["desvio_padrao"],
                "acuracia_teste": eval_result["acuracia"],
                "relatorio": eval_result["relatorio"],
                "matriz_confusao": eval_result["matriz_confusao"],
            }

        except Exception as e:
            logger.error("Erro no modelo %s: %s", nome_display, e)
            resultados[nome_algo] = {"nome": nome_display, "erro": str(e)}

    # Determinar melhor modelo
    modelos_validos = {
        k: v for k, v in resultados.items() if "erro" not in v
    }
    melhor_algo = max(
        modelos_validos,
        key=lambda x: modelos_validos[x]["acuracia_cv"],
    ) if modelos_validos else None

    return {
        "modelos": modelos_treinados,
        "resultados": resultados,
        "melhor_algoritmo": melhor_algo,
        "label_encoder": le,
        "tfidf": tfidf,
        "X_tfidf_completo": X_tfidf,
        "dados_originais": dados,
        "classes": list(le.classes_),
    }


def treinar_modelo_individual(
    X_train,
    y_train,
    algoritmo: str = "random_forest",
    **params,
) -> tuple:
    """Treina um único modelo com os dados fornecidos.

    Args:
        X_train: Features de treino (já vetorizadas).
        y_train: Labels de treino.
        algoritmo: Nome do algoritmo do registry.
        **params: Parâmetros adicionais para o modelo.

    Returns:
        Tupla (modelo_treinado, label_encoder).
    """
    le = LabelEncoder()
    y_encoded = le.fit_transform(y_train)

    modelo = get_algorithm(algoritmo, **params)
    modelo.fit(X_train, y_encoded)

    logger.info("Modelo %s treinado com %d amostras", algoritmo, X_train.shape[0])
    return modelo, le


def calcular_probabilidades_combinadas(
    modelos: dict,
    X,
    classes: list[str],
) -> pd.DataFrame:
    """Calcula probabilidades combinadas (média) de múltiplos modelos.

    Args:
        modelos: Dict nome -> modelo treinado.
        X: Features para predição.
        classes: Lista de nomes das classes.

    Returns:
        DataFrame com colunas Prob_<classe> para cada classe.
    """
    probas = []
    for nome, modelo in modelos.items():
        if hasattr(modelo, "predict_proba"):
            probas.append(modelo.predict_proba(X))
        else:
            logger.warning("Modelo %s não suporta predict_proba, ignorando", nome)

    if not probas:
        return pd.DataFrame()

    prob_media = np.mean(probas, axis=0)
    colunas = [f"Prob_{eng}" for eng in classes]
    return pd.DataFrame(prob_media, columns=colunas)
