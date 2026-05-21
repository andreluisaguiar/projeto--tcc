import pandas as pd
from src.preprocessing.deduplication import remover_duplicatas


def test_remover_duplicatas():
    # Criação de um DataFrame de teste com registros duplicados
    dados = {
        "Titulo": [
            "Sistema Fotovoltaico",
            "Análise Térmica",
            "Sistema Fotovoltaico",  # Duplicado completo
            "Eficiência de Redes",
        ],
        "Engenharia": [
            "Engenharia Elétrica",
            "Engenharia Mecânica",
            "Engenharia Elétrica",  # Duplicado completo
            "Engenharia de Computação",
        ],
    }
    df = pd.DataFrame(dados)

    # Execução
    df_limpo = remover_duplicatas(df)

    # Asserções
    assert len(df_limpo) == 3
    assert "Análise Térmica" in df_limpo["Titulo"].values
    assert df_limpo.duplicated().sum() == 0
