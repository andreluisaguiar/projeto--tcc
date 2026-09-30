import pandas as pd

from src.preprocessing.orientador_tema import (
    filtrar_engenharia_computacao,
    inferir_areas_pesquisa,
    ranquear_orientadores,
    sugerir_temas,
    sugerir_temas_por_interesses,
)


def test_filtrar_engenharia_computacao_com_acento():
    df = pd.DataFrame(
        {
            "titulo": ["A", "B"],
            "engenharia": ["Engenharia da Computação", "Engenharia Elétrica"],
        }
    )

    filtrado = filtrar_engenharia_computacao(df)

    assert len(filtrado) == 1
    assert filtrado.iloc[0]["titulo"] == "A"


def test_ranquear_orientadores_com_areas_e_termos(monkeypatch):
    monkeypatch.setattr(
        "src.preprocessing.orientador_tema.get_portuguese_stopwords",
        lambda: ["de", "da", "do", "para", "com", "em", "e"],
    )
    df = pd.DataFrame(
        {
            "Titulo": [
                "Classificação de imagens com aprendizado de máquina",
                "Predição de evasão usando dados acadêmicos",
                "Aplicativo mobile para gestão de tarefas",
            ],
            "Curso": [
                "Engenharia da Computação",
                "Engenharia da Computação",
                "Engenharia da Computação",
            ],
            "Orientador": ["Ana Silva", "Ana Silva", "Bruno Costa"],
            "Ano": ["2024", "2023", "2024"],
        }
    )

    ranking = ranquear_orientadores(df)

    assert ranking.iloc[0]["orientador"] == "Ana Silva"
    assert ranking.iloc[0]["quantidade"] == 2
    assert "Inteligência Artificial" in ranking.iloc[0]["areas_inferidas"]
    assert "aprendizado" in ranking.iloc[0]["termos_recorrentes"]


def test_sugerir_temas_por_orientador(monkeypatch):
    monkeypatch.setattr(
        "src.preprocessing.orientador_tema.get_portuguese_stopwords",
        lambda: ["de", "da", "do", "para", "com", "em", "e"],
    )
    df = pd.DataFrame(
        {
            "titulo": [
                "Detecção de vulnerabilidade em API web",
                "Privacidade e autenticação em sistemas web",
            ],
            "orientador": ["Carla Lima", "Carla Lima"],
        }
    )

    temas = sugerir_temas(df, orientador="Carla Lima")

    assert temas
    assert any("Segurança da Informação" in tema for tema in temas)


def test_inferir_areas_sem_match_retorna_lista_vazia(monkeypatch):
    monkeypatch.setattr(
        "src.preprocessing.orientador_tema.get_portuguese_stopwords",
        lambda: ["de", "da", "do", "para", "com", "em", "e"],
    )

    assert inferir_areas_pesquisa(["Memorial descritivo de estágio"]) == []


def test_sugerir_temas_por_interesses_cruza_perfil_e_orientador(monkeypatch):
    monkeypatch.setattr(
        "src.preprocessing.orientador_tema.get_portuguese_stopwords",
        lambda: ["de", "da", "do", "para", "com", "em", "e", "na"],
    )
    df = pd.DataFrame(
        {
            "titulo": [
                "Dashboard de dados para apoio a decisão em saúde",
                "Sistema web para gestão hospitalar",
                "Rede de sensores industriais",
            ],
            "orientador": ["Ana Silva", "Ana Silva", "Bruno Costa"],
        }
    )

    sugestoes = sugerir_temas_por_interesses(
        df,
        interesses="desenvolvimento de software na saúde e análise de dados",
    )

    assert not sugestoes.empty
    assert sugestoes.iloc[0]["orientador"] == "Ana Silva"
    assert "saúde" in sugestoes.iloc[0]["temas_sugeridos"]
