"""Configurações centralizadas do projeto."""

import os
from pathlib import Path

# ─── Diretórios ───────────────────────────────────────────────────────────────
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
MODELS_DIR = DATA_DIR / "models"

# Garante que os diretórios existem
for _dir in (RAW_DATA_DIR, PROCESSED_DATA_DIR, MODELS_DIR):
    _dir.mkdir(parents=True, exist_ok=True)

# ─── Selenium / Chrome ────────────────────────────────────────────────────────
CHROME_BINARY_PATH: str | None = os.getenv("CHROME_BINARY_PATH")
CHROMEDRIVER_PATH: str | None = os.getenv("CHROMEDRIVER_PATH")

CHROME_CANDIDATES: list[str] = [
    "google-chrome",
    "google-chrome-stable",
    "chromium-browser",
    "chromium",
    "/snap/bin/chromium",
    "brave-browser",
    "microsoft-edge",
]

# ─── NLP ──────────────────────────────────────────────────────────────────────
SPACY_MODEL: str = "pt_core_news_md"
OUTLIER_SIMILARITY_THRESHOLD: float = 0.3

# ─── Machine Learning ────────────────────────────────────────────────────────
TFIDF_MAX_FEATURES: int = 5000
TFIDF_MIN_DF: int = 2
TFIDF_MAX_DF: float = 0.8
TEST_SIZE: float = 0.2
RANDOM_STATE: int = 42
SMOTE_RANDOM_STATE: int = 42
CV_FOLDS: int = 5

# ─── Stopwords ────────────────────────────────────────────────────────────────
# Carregamento lazy para evitar download automático do NLTK no import
_STOPWORDS_PT: list[str] | None = None


def get_stopwords_pt() -> list[str]:
    """Retorna stopwords em português (com cache)."""
    global _STOPWORDS_PT
    if _STOPWORDS_PT is None:
        from nltk.corpus import stopwords
        _STOPWORDS_PT = stopwords.words("portuguese")
    return _STOPWORDS_PT
