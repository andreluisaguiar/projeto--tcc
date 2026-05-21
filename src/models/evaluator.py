"""Avaliação de modelos de Machine Learning."""

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
)
from sklearn.model_selection import cross_val_score
from sklearn.preprocessing import LabelEncoder

from src.config import CV_FOLDS
from src.utils.logging_config import logger


def avaliar_modelo(
    modelo,
    label_encoder: LabelEncoder,
    X_test,
    y_test,
) -> dict:
    """Avalia um modelo treinado com métricas de classificação.

    Args:
        modelo: Modelo treinado com .predict().
        label_encoder: Encoder usado para codificar as classes.
        X_test: Features do conjunto de teste.
        y_test: Labels do conjunto de teste (encoded).

    Returns:
        Dict com acurácia, relatório de classificação, e matriz de confusão.
    """
    y_pred = modelo.predict(X_test)
    acuracia = accuracy_score(y_test, y_pred)

    report = classification_report(
        y_test,
        y_pred,
        output_dict=True,
        target_names=label_encoder.classes_,
    )

    cm = confusion_matrix(y_test, y_pred)

    logger.info("Acurácia no teste: %.4f", acuracia)
    return {
        "acuracia": acuracia,
        "relatorio": report,
        "matriz_confusao": cm,
        "y_pred": y_pred,
    }


def validacao_cruzada(
    modelo,
    X_train,
    y_train,
    cv: int = CV_FOLDS,
) -> dict:
    """Executa validação cruzada e retorna estatísticas dos scores.

    Args:
        modelo: Modelo (não treinado) para validação.
        X_train: Features de treino.
        y_train: Labels de treino.
        cv: Número de folds para validação cruzada.

    Returns:
        Dict com scores, média e desvio padrão.
    """
    scores = cross_val_score(modelo, X_train, y_train, cv=cv, scoring="accuracy")
    resultado = {
        "scores": scores,
        "media": float(np.mean(scores)),
        "desvio_padrao": float(np.std(scores)),
    }

    logger.info(
        "Validação cruzada (%d folds): média=%.4f ± %.4f",
        cv,
        resultado["media"],
        resultado["desvio_padrao"],
    )
    return resultado


def relatorio_para_dataframe(relatorio: dict) -> pd.DataFrame:
    """Converte o relatório de classificação (dict) em DataFrame formatado.

    Args:
        relatorio: Output de classification_report(output_dict=True).

    Returns:
        DataFrame com colunas renomeadas para português.
    """
    df = pd.DataFrame(relatorio).T
    df = df.reset_index().rename(columns={
        "index": "Classe",
        "precision": "Precisão",
        "recall": "Revocação",
        "f1-score": "F1-Score",
        "support": "Suporte",
    })
    return df
