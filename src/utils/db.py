"""Módulo para persistência de dados utilizando SQLite."""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

import pandas as pd

from src.config import DB_PATH

logger = logging.getLogger("projeto_tcc.db")

COLUNAS_DB = [
    "id",
    "titulo",
    "engenharia",
    "orientador",
    "ano",
    "is_outlier",
    "is_duplicate",
]


def obter_conexao() -> sqlite3.Connection:
    """Retorna uma conexão ativa com o banco de dados SQLite."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _normalizar_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df_temp = df.copy()
    rename_dict: dict[str, str] = {}

    for col in df_temp.columns:
        col_lower = str(col).strip().lower()
        if col_lower in {"titulo", "título"}:
            rename_dict[col] = "titulo"
        elif col_lower in {"engenharia", "curso"}:
            rename_dict[col] = "engenharia"
        elif col_lower in {"orientador", "orientadora"}:
            rename_dict[col] = "orientador"
        elif col_lower == "ano":
            rename_dict[col] = "ano"

    if rename_dict:
        df_temp = df_temp.rename(columns=rename_dict)

    if "titulo" not in df_temp.columns or "engenharia" not in df_temp.columns:
        raise ValueError("O DataFrame precisa conter as colunas 'titulo' e 'engenharia'.")

    if "orientador" not in df_temp.columns:
        df_temp["orientador"] = "Não Informado"
    if "ano" not in df_temp.columns:
        df_temp["ano"] = "Não Informado"

    df_temp = df_temp[[c for c in ["titulo", "engenharia", "orientador", "ano"] if c in df_temp.columns]]
    df_temp["titulo"] = df_temp["titulo"].astype(str).str.strip()
    df_temp["engenharia"] = df_temp["engenharia"].astype(str).str.strip()
    df_temp["orientador"] = df_temp["orientador"].astype(str).str.title().str.strip()
    df_temp["ano"] = df_temp["ano"].astype(str).str.strip()
    df_temp = df_temp[df_temp["titulo"].ne("") & df_temp["engenharia"].ne("")]
    return df_temp


def _garantir_schema(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS tccs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT UNIQUE NOT NULL,
            engenharia TEXT NOT NULL,
            orientador TEXT,
            ano TEXT,
            is_outlier INTEGER NOT NULL DEFAULT 0,
            is_duplicate INTEGER NOT NULL DEFAULT 0
        )
        """
    )

    cursor.execute("PRAGMA table_info(tccs)")
    colunas_existentes = {row[1] for row in cursor.fetchall()}
    colunas_default = {
        "orientador": "TEXT DEFAULT 'Não Informado'",
        "ano": "TEXT DEFAULT 'Não Informado'",
        "is_outlier": "INTEGER NOT NULL DEFAULT 0",
        "is_duplicate": "INTEGER NOT NULL DEFAULT 0",
    }

    for coluna, ddl in colunas_default.items():
        if coluna not in colunas_existentes:
            cursor.execute(f"ALTER TABLE tccs ADD COLUMN {coluna} {ddl}")

    conn.commit()


def inicializar_db() -> None:
    """Cria a tabela 'tccs' no banco de dados se ela ainda não existir."""
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    logger.info("Inicializando banco de dados em: %s", DB_PATH)
    with obter_conexao() as conn:
        _garantir_schema(conn)
    logger.info("Banco de dados inicializado com sucesso.")


def salvar_dataframe_tccs(df: pd.DataFrame) -> tuple[int, int]:
    """Salva um DataFrame de TCCs no banco de dados."""
    inicializar_db()
    df_temp = _normalizar_dataframe(df)
    registros = list(df_temp[["titulo", "engenharia", "orientador", "ano"]].itertuples(index=False, name=None))

    if not registros:
        return 0, 0

    with obter_conexao() as conn:
        before = conn.total_changes
        cursor = conn.cursor()
        cursor.executemany(
            """
            INSERT OR IGNORE INTO tccs (titulo, engenharia, orientador, ano)
            VALUES (?, ?, ?, ?)
            """,
            registros,
        )
        conn.commit()
        inseridos = conn.total_changes - before

    ignorados = len(registros) - inseridos
    logger.info(
        "Importação SQLite concluída: %d inseridos, %d duplicatas ignoradas",
        inseridos,
        ignorados,
    )
    return int(inseridos), int(ignorados)


def obter_todos_tccs(
    incluir_outliers: bool = True,
    incluir_duplicadas: bool = True,
) -> pd.DataFrame:
    """Retorna todos os TCCs salvos no banco como um DataFrame."""
    inicializar_db()

    query = "SELECT id, titulo, engenharia, orientador, ano, is_outlier, is_duplicate FROM tccs WHERE 1=1"
    if not incluir_outliers:
        query += " AND COALESCE(is_outlier, 0) = 0"
    if not incluir_duplicadas:
        query += " AND COALESCE(is_duplicate, 0) = 0"

    with obter_conexao() as conn:
        df = pd.read_sql_query(query, conn)

    if df.empty:
        return pd.DataFrame(columns=COLUNAS_DB)

    for coluna in ["is_outlier", "is_duplicate"]:
        df[coluna] = df[coluna].fillna(0).astype(int)
    return df


def atualizar_outliers(titulos_outliers: list[str]) -> int:
    """Marca os títulos informados como outliers (is_outlier = 1)."""
    inicializar_db()
    titulos_limpos = [titulo.strip() for titulo in titulos_outliers if titulo and str(titulo).strip()]

    with obter_conexao() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE tccs SET is_outlier = 0")
        alterados = 0
        for titulo in titulos_limpos:
            cursor.execute("UPDATE tccs SET is_outlier = 1 WHERE titulo = ?", (titulo,))
            alterados += cursor.rowcount
        conn.commit()

    logger.info("Marcados %d registros como outliers no banco.", alterados)
    return alterados


def atualizar_duplicatas(titulos_duplicados: list[str]) -> int:
    """Marca os títulos informados como duplicatas (is_duplicate = 1)."""
    inicializar_db()
    titulos_limpos = [titulo.strip() for titulo in titulos_duplicados if titulo and str(titulo).strip()]

    with obter_conexao() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE tccs SET is_duplicate = 0")
        alterados = 0
        for titulo in titulos_limpos:
            cursor.execute("UPDATE tccs SET is_duplicate = 1 WHERE titulo = ?", (titulo,))
            alterados += cursor.rowcount
        conn.commit()

    logger.info("Marcados %d registros como duplicados no banco.", alterados)
    return alterados


def limpar_banco() -> int:
    """Remove todas as linhas da tabela 'tccs' e zera a sequência de IDs."""
    inicializar_db()
    with obter_conexao() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM tccs")
        total = int(cursor.fetchone()[0])
        cursor.execute("DELETE FROM tccs")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='tccs'")
        conn.commit()

    logger.info("Banco de dados resetado: %d registros excluídos.", total)
    return total


def salvar_tccs(df: pd.DataFrame) -> tuple[int, int]:
    """Compatibilidade com a API anterior."""
    return salvar_dataframe_tccs(df)


def remover_todos_tccs() -> int:
    """Compatibilidade com a API anterior."""
    return limpar_banco()
