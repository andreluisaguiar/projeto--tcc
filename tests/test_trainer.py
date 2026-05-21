import pandas as pd
import pytest
from src.models.trainer import treinar_pipeline_predicao


def test_treinar_pipeline_predicao():
    # Criação de um dataset fake balanceado com exemplos suficientes (10 amostras por classe)
    # para que após o split (test_size=0.2) restem pelo menos 8 amostras de cada classe no treino,
    # permitindo que o SMOTE (que requer default k_neighbors=5, exigindo no mínimo 6 amostras) execute sem erros.
    dados = {
        "titulo": [
            # Engenharia Elétrica (10 amostras)
            "Estudo de subestações elétricas de alta tensão",
            "Análise de redes de energia elétrica inteligente",
            "Desenvolvimento de gerador eólico trifásico",
            "Instalações elétricas residenciais seguras",
            "Eficiência em motores elétricos industriais",
            "Projeto de linhas de transmissão elétrica",
            "Simulação de sistemas de potência elétrica",
            "Proteção de geradores e transformadores elétricos",
            "Energias renováveis e redes inteligentes de energia",
            "Análise de estabilidade em sistemas elétricos interconectados",
            # Engenharia de Computação (10 amostras)
            "Desenvolvimento de compiladores para microcontroladores",
            "Criação de um sistema operacional embarcado em tempo real",
            "Algoritmo de roteamento para redes de computadores",
            "Interface de hardware e software para robótica",
            "Processamento de imagens digitais com arquitetura CUDA",
            "Arquitetura de computadores e processadores paralelos",
            "Estudo de banco de dados distribuídos de alta performance",
            "Segurança cibernética em dispositivos de Internet das Coisas",
            "Desenvolvimento de drivers de dispositivos Linux",
            "Processamento de sinais em sistemas de telecomunicações",
        ],
        "engenharia": [
            "Engenharia Elétrica",
            "Engenharia Elétrica",
            "Engenharia Elétrica",
            "Engenharia Elétrica",
            "Engenharia Elétrica",
            "Engenharia Elétrica",
            "Engenharia Elétrica",
            "Engenharia Elétrica",
            "Engenharia Elétrica",
            "Engenharia Elétrica",
            "Engenharia de Computação",
            "Engenharia de Computação",
            "Engenharia de Computação",
            "Engenharia de Computação",
            "Engenharia de Computação",
            "Engenharia de Computação",
            "Engenharia de Computação",
            "Engenharia de Computação",
            "Engenharia de Computação",
            "Engenharia de Computação",
        ],
    }
    df = pd.DataFrame(dados)

    # Executa o pipeline de treino com Random Forest (apenas RF para ser mais rápido)
    resultado = treinar_pipeline_predicao(
        df, algoritmos=["random_forest"], usar_smote=True, test_size=0.2
    )

    # Asserções
    assert "modelos" in resultado
    assert "random_forest" in resultado["modelos"]
    assert "resultados" in resultado
    assert "random_forest" in resultado["resultados"]
    assert "label_encoder" in resultado
    assert "tfidf" in resultado

    # Testa se conseguimos obter métricas
    res_rf = resultado["resultados"]["random_forest"]
    assert "acuracia_cv" in res_rf
    assert "acuracia_teste" in res_rf
