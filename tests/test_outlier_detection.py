import pandas as pd
import pytest
from src.preprocessing.outlier_detection import calcular_similaridade, detectar_outliers


def test_calcular_similaridade():
    # Verifica se a similaridade de palavras idênticas é alta
    sim1 = calcular_similaridade("Engenharia Elétrica", "Engenharia Elétrica")
    assert sim1 > 0.8

    # Verifica se palavras muito distantes têm similaridade menor
    sim2 = calcular_similaridade("Filosofia Antiga", "Engenharia de Computação")
    assert sim2 < sim1


def test_detectar_outliers():
    # Dataset contendo outliers e registros normais
    dados = {
        "titulo": [
            "Estudo de Linhas de Transmissão de Alta Tensão",
            "Análise do Comportamento Humano na Grécia Antiga",
            "Desenvolvimento de Robô Seguidor de Linha",
            "Monografia sobre Culinária Vegana",  # Sem a palavra "engenharia" na classe -> Outlier automático
        ],
        "engenharia": [
            "Engenharia Elétrica",
            "Engenharia Mecânica",
            "Engenharia de Computação",
            "Administração",  # Classe inválida (sem "engenharia")
        ],
    }
    df = pd.DataFrame(dados)

    # Execução
    df_outliers, df_sem_outliers = detectar_outliers(
        df, "titulo", "engenharia", limiar=0.3
    )

    # Asserções
    assert len(df_outliers) >= 1
    assert "Monografia sobre Culinária Vegana" in df_outliers["titulo"].values
    assert "Estudo de Linhas de Transmissão de Alta Tensão" in df_sem_outliers["titulo"].values
