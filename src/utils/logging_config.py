"""Configuração de logging para o projeto."""

import logging
import sys


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Configura e retorna o logger principal do projeto.

    Args:
        level: Nível de logging (default: INFO).

    Returns:
        Logger configurado com handler para stdout.
    """
    logger = logging.getLogger("projeto_tcc")

    if logger.handlers:
        return logger

    logger.setLevel(level)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s.%(funcName)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


# Logger global pronto para uso: from src.utils.logging_config import logger
logger = setup_logging()
