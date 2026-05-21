"""Remoção de duplicatas de DataFrames."""

import pandas as pd

from src.utils.logging_config import logger


def remover_duplicatas(df: pd.DataFrame) -> pd.DataFrame:
    """Remove linhas duplicadas de um DataFrame.

    Args:
        df: DataFrame com possíveis duplicatas.

    Returns:
        DataFrame sem duplicatas.
    """
    total_antes = len(df)
    df_limpo = df.drop_duplicates()
    removidas = total_antes - len(df_limpo)

    logger.info(
        "Duplicatas removidas: %d de %d linhas (restaram %d)",
        removidas,
        total_antes,
        len(df_limpo),
    )
    return df_limpo
