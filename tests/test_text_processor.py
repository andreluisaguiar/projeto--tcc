import pytest
from src.preprocessing.text_processor import normalizar_titulo, get_portuguese_stopwords


def test_normalizar_titulo():
    # Teste de lowercase e strip de espaços
    assert normalizar_titulo("  SISTEMAS FOTOVOLTAICOS  ") == "sistemas fotovoltaicos"
    assert normalizar_titulo("Eficiência Energética") == "eficiência energética"
    assert normalizar_titulo("\n TCC de Engenharia \t") == "tcc de engenharia"


def test_get_portuguese_stopwords():
    # Teste de carregamento de stopwords em português
    stopwords = get_portuguese_stopwords()
    assert isinstance(stopwords, list)
    assert len(stopwords) > 0
    # Algumas stopwords clássicas em português
    assert "de" in stopwords
    assert "a" in stopwords
    assert "o" in stopwords
    assert "que" in stopwords
