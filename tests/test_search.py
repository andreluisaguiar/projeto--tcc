import numpy as np
import pandas as pd

import src.preprocessing.search as search_module


class _FakeDoc:
    def __init__(self, vector):
        self.vector = np.array(vector, dtype=float)
        self.has_vector = bool(np.linalg.norm(self.vector) > 0)


class _FakeNLP:
    def __call__(self, text):
        mapping = {
            "energia solar": [1.0, 0.0],
            "sistema fotovoltaico": [0.9, 0.1],
            "análise térmica": [0.0, 1.0],
        }
        return _FakeDoc(mapping.get(text.lower(), [0.0, 0.0]))


def test_buscar_titulos_similares(monkeypatch):
    monkeypatch.setattr(search_module, "_get_nlp", lambda: _FakeNLP())
    monkeypatch.setattr(
        search_module,
        "obter_todos_tccs",
        lambda **kwargs: pd.DataFrame(
            {
                "titulo": ["Sistema Fotovoltaico", "Análise Térmica"],
                "engenharia": ["Engenharia Elétrica", "Engenharia Mecânica"],
                "orientador": ["Ana", "Bruno"],
                "ano": ["2024", "2023"],
                "is_outlier": [0, 0],
                "is_duplicate": [0, 0],
            }
        ),
    )

    resultado = search_module.buscar_titulos_similares("energia solar", limit=5, limiar_minimo=0.1)
    assert list(resultado["titulo"]) == ["Sistema Fotovoltaico"]
    assert resultado.iloc[0]["similaridade"] > 0