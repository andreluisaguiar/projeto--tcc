"""Detecção de outliers baseada em similaridade semântica com spaCy.

O modelo spaCy é carregado de forma lazy (sob demanda) para evitar
carregar ~50MB de modelo em toda importação do módulo.
"""

import pandas as pd

from src.config import SPACY_MODEL, OUTLIER_SIMILARITY_THRESHOLD
from src.utils.logging_config import logger

# ─── Lazy loading do modelo spaCy ─────────────────────────────────────────────
_nlp = None


def _get_nlp():
    """Carrega o modelo spaCy sob demanda (singleton lazy)."""
    global _nlp
    if _nlp is None:
        import spacy
        logger.info("Carregando modelo spaCy: %s", SPACY_MODEL)
        _nlp = spacy.load(SPACY_MODEL)
    return _nlp


def calcular_similaridade(titulo: str, engenharia: str) -> float:
    """Calcula a similaridade semântica entre um título e uma engenharia.

    Args:
        titulo: Texto do título da monografia.
        engenharia: Nome da engenharia.

    Returns:
        Score de similaridade entre 0 e 1.
    """
    nlp = _get_nlp()
    doc_titulo = nlp(titulo)
    doc_engenharia = nlp(engenharia)
    return doc_titulo.similarity(doc_engenharia)


def detectar_outliers(
    df: pd.DataFrame,
    titulo_col: str,
    engenharia_col: str,
    limiar: float = OUTLIER_SIMILARITY_THRESHOLD,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Detecta outliers com base na similaridade entre título e engenharia.

    Títulos que não contêm a palavra 'engenharia' na coluna de engenharia
    ou que possuem similaridade semântica abaixo do limiar são marcados
    como outliers.

    Args:
        df: DataFrame com as colunas de título e engenharia.
        titulo_col: Nome da coluna de títulos.
        engenharia_col: Nome da coluna de engenharias.
        limiar: Limiar mínimo de similaridade (default: 0.3).

    Returns:
        Tupla (df_outliers, df_sem_outliers).
    """
    logger.info(
        "Detectando outliers: coluna_titulo='%s', coluna_engenharia='%s', limiar=%.2f",
        titulo_col, engenharia_col, limiar,
    )

    # Vetorizado: verificar se a palavra "engenharia" aparece na coluna
    eng_lower = df[engenharia_col].astype(str).str.lower()
    titulo_lower = df[titulo_col].astype(str).str.lower()

    # Mask: linhas onde "engenharia" NÃO está na coluna de engenharia → outlier direto
    sem_palavra_eng = ~eng_lower.str.contains("engenharia", na=False)

    # Para as demais, calcular similaridade
    similaridades = pd.Series(0.0, index=df.index)
    mask_calcular = ~sem_palavra_eng

    for idx in df.index[mask_calcular]:
        similaridades[idx] = calcular_similaridade(
            titulo_lower[idx], eng_lower[idx]
        )

    # Outlier = sem palavra "engenharia" OU similaridade abaixo do limiar
    mask_outlier = sem_palavra_eng | (mask_calcular & (similaridades < limiar))

    df_outliers = df[mask_outlier].copy()
    df_sem_outliers = df[~mask_outlier].copy()

    logger.info(
        "Outliers detectados: %d de %d registros (%.1f%%)",
        len(df_outliers),
        len(df),
        len(df_outliers) / len(df) * 100 if len(df) > 0 else 0,
    )

    return df_outliers, df_sem_outliers
