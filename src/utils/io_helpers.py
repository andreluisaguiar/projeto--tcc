"""Utilitários de I/O para leitura e escrita de arquivos."""

import io
from pathlib import Path

import pandas as pd

from src.utils.logging_config import logger


def read_excel(file_or_path) -> pd.DataFrame:
    """Lê um arquivo Excel e retorna um DataFrame.

    Args:
        file_or_path: Caminho do arquivo, objeto Path, ou file-like (upload Streamlit).

    Returns:
        DataFrame com os dados do arquivo.

    Raises:
        FileNotFoundError: Se o arquivo não existir (quando é um caminho).
        ValueError: Se o arquivo estiver vazio ou inválido.
    """
    if isinstance(file_or_path, (str, Path)):
        path = Path(file_or_path)
        if not path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {path}")
        logger.info("Lendo arquivo: %s", path)

    df = pd.read_excel(file_or_path)

    if df.empty:
        raise ValueError("O arquivo está vazio.")

    logger.info("Arquivo carregado: %d linhas x %d colunas", len(df), len(df.columns))
    return df


def dataframe_to_excel_buffer(df: pd.DataFrame) -> io.BytesIO:
    """Converte um DataFrame para um buffer Excel em memória.

    Args:
        df: DataFrame a ser convertido.

    Returns:
        BytesIO buffer com o arquivo Excel pronto para download.
    """
    buffer = io.BytesIO()
    df.to_excel(buffer, index=False, engine="openpyxl")
    buffer.seek(0)
    return buffer


def merge_excel_files(files: list) -> pd.DataFrame:
    """Carrega e concatena múltiplos arquivos Excel.

    Args:
        files: Lista de caminhos ou file-like objects.

    Returns:
        DataFrame combinado de todos os arquivos.

    Raises:
        ValueError: Se a lista de arquivos estiver vazia.
    """
    if not files:
        raise ValueError("Nenhum arquivo fornecido.")

    dataframes = []
    for f in files:
        df = read_excel(f)
        dataframes.append(df)

    combined = pd.concat(dataframes, ignore_index=True)
    logger.info(
        "Arquivos combinados: %d arquivos → %d linhas totais",
        len(files),
        len(combined),
    )
    return combined
