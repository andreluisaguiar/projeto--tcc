"""Predição com modelos treinados (salvos ou em memória)."""

import joblib
import pandas as pd
from pathlib import Path

from src.utils.logging_config import logger


def prever_engenharia(
    titulo: str,
    modelos: dict,
    tfidf,
    label_encoder,
) -> pd.DataFrame:
    """Prediz a engenharia para um título usando múltiplos modelos.

    Args:
        titulo: Título da monografia para predição.
        modelos: Dict nome -> modelo treinado.
        tfidf: TfidfVectorizer já ajustado (fitted).
        label_encoder: LabelEncoder para decodificar as classes.

    Returns:
        DataFrame com probabilidades por engenharia para cada modelo.
    """
    titulo_tfidf = tfidf.transform([titulo])
    resultados = {}

    for nome, modelo in modelos.items():
        if hasattr(modelo, "predict_proba"):
            probs = modelo.predict_proba(titulo_tfidf)[0]
            resultados[nome] = dict(zip(label_encoder.classes_, probs))
        else:
            pred = modelo.predict(titulo_tfidf)[0]
            eng = label_encoder.inverse_transform([pred])[0]
            resultados[nome] = {eng: 1.0}

    df = pd.DataFrame(resultados)
    df.index.name = "Engenharia"

    logger.info("Predição para título '%s': %s", titulo[:50], df.idxmax().to_dict())
    return df


def prever_com_modelo_salvo(
    titulo: str,
    modelo_path: str | Path,
) -> dict:
    """Carrega um modelo salvo e realiza predição.

    Args:
        titulo: Título da monografia.
        modelo_path: Caminho do arquivo .joblib com o modelo salvo.

    Returns:
        Dict com predição e probabilidades (se disponível).

    Raises:
        FileNotFoundError: Se o arquivo do modelo não existir.
    """
    path = Path(modelo_path)
    if not path.exists():
        raise FileNotFoundError(f"Modelo não encontrado: {path}")

    artefatos = joblib.load(path)
    modelo = artefatos["model"]
    tfidf = artefatos["tfidf"]
    le = artefatos["label_encoder"]

    titulo_tfidf = tfidf.transform([titulo])
    pred_encoded = modelo.predict(titulo_tfidf)[0]
    engenharia = le.inverse_transform([pred_encoded])[0]

    resultado = {"engenharia_predita": engenharia}

    if hasattr(modelo, "predict_proba"):
        probs = modelo.predict_proba(titulo_tfidf)[0]
        resultado["probabilidades"] = dict(zip(le.classes_, probs))

    logger.info("Predição (modelo salvo): '%s' → %s", titulo[:50], engenharia)
    return resultado


def salvar_modelo(
    modelo,
    tfidf,
    label_encoder,
    filepath: str | Path = "modelo_classificacao.joblib",
) -> Path:
    """Salva modelo, vetorizador e encoder em um único arquivo.

    Args:
        modelo: Modelo treinado.
        tfidf: TfidfVectorizer ajustado.
        label_encoder: LabelEncoder.
        filepath: Caminho de destino.

    Returns:
        Path do arquivo salvo.
    """
    path = Path(filepath)
    joblib.dump(
        {"model": modelo, "tfidf": tfidf, "label_encoder": label_encoder},
        path,
    )
    logger.info("Modelo salvo em: %s", path)
    return path
