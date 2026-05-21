"""Módulo para busca semântica de monografias."""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from src.config import SPACY_MODEL
from src.utils.db import obter_todos_tccs

logger = logging.getLogger("projeto_tcc.search")

_nlp = None


def _get_nlp():
    """Carrega o modelo spaCy sob demanda (singleton lazy)."""
    global _nlp
    if _nlp is None:
        import spacy

        logger.info("Carregando modelo spaCy para busca: %s", SPACY_MODEL)
        _nlp = spacy.load(SPACY_MODEL)
    return _nlp


def _similaridade_cosseno(vetor_a: np.ndarray, vetor_b: np.ndarray) -> float:
    norma_a = float(np.linalg.norm(vetor_a))
    norma_b = float(np.linalg.norm(vetor_b))
    if norma_a == 0.0 or norma_b == 0.0:
        return 0.0
    return float(np.dot(vetor_a, vetor_b) / (norma_a * norma_b))


def buscar_titulos_similares(
    query: str,
    limit: int = 5,
    limiar_minimo: float = 0.5,
    filtro_engenharia: str = "Todas",
    filtro_ano: str = "Todos",
) -> pd.DataFrame:
    """Busca títulos de TCC semanticamente similares à consulta do usuário."""
    consulta = query.strip()
    if not consulta:
        return pd.DataFrame()

    df = obter_todos_tccs(incluir_outliers=False, incluir_duplicadas=False)
    if df.empty:
        return pd.DataFrame()

    if filtro_engenharia != "Todas":
        df = df[df["engenharia"] == filtro_engenharia]

    if filtro_ano != "Todos":
        df = df[df["ano"].astype(str) == str(filtro_ano)]

    if df.empty:
        return pd.DataFrame()

    nlp = _get_nlp()
    doc_query = nlp(consulta)
    if not doc_query.has_vector:
        return pd.DataFrame()

    similaridades = []
    for titulo in df["titulo"].astype(str):
        doc_titulo = nlp(titulo)
        if doc_titulo.has_vector:
            score = _similaridade_cosseno(doc_query.vector, doc_titulo.vector)
        else:
            score = 0.0
        similaridades.append(score)

    df_resultado = df.copy()
    df_resultado["similaridade"] = similaridades
    df_resultado = df_resultado[df_resultado["similaridade"] >= limiar_minimo]
    df_resultado = df_resultado.sort_values(by="similaridade", ascending=False).head(limit)
    return df_resultado.reset_index(drop=True)
