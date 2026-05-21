"""Pré-processamento de texto para o pipeline de NLP."""

from src.config import get_stopwords_pt
from src.utils.logging_config import logger


def normalizar_titulo(titulo: str) -> str:
    """Normaliza um título para processamento.

    Aplica lowercase e strip de espaços.

    Args:
        titulo: Título original.

    Returns:
        Título normalizado.
    """
    return titulo.strip().lower()


def get_portuguese_stopwords() -> list[str]:
    """Retorna a lista de stopwords em português do NLTK.

    Returns:
        Lista de stopwords.
    """
    stopwords = get_stopwords_pt()
    logger.info("Stopwords carregadas: %d palavras", len(stopwords))
    return stopwords
