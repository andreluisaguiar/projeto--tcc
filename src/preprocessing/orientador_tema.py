"""Análises para apoiar a escolha de orientador e tema de TCC."""

from __future__ import annotations

import re
import unicodedata
from collections import Counter

import pandas as pd

from src.preprocessing.text_processor import get_portuguese_stopwords


AREA_KEYWORDS: dict[str, set[str]] = {
    "Saúde Digital e Informática em Saúde": {
        "saude",
        "medico",
        "medica",
        "hospital",
        "hospitalar",
        "clinica",
        "clinico",
        "paciente",
        "prontuario",
        "telemedicina",
        "diagnostico",
        "sus",
        "epidemiologia",
    },
    "Inteligência Artificial e Machine Learning": {
        "aprendizado",
        "machine",
        "learning",
        "inteligencia",
        "artificial",
        "classificacao",
        "predicao",
        "previsao",
        "rede",
        "neural",
        "deep",
        "mineração",
        "mineracao",
    },
    "Ciência de Dados e Analytics": {
        "dados",
        "data",
        "analytics",
        "big",
        "visualizacao",
        "dashboard",
        "estatistica",
        "indicadores",
    },
    "Engenharia de Software": {
        "software",
        "requisitos",
        "arquitetura",
        "qualidade",
        "teste",
        "testes",
        "metodologia",
        "agil",
        "devops",
    },
    "Sistemas Web e Mobile": {
        "web",
        "mobile",
        "aplicativo",
        "aplicacao",
        "android",
        "ios",
        "frontend",
        "backend",
        "api",
    },
    "Redes de Computadores e Telecomunicações": {
        "redes",
        "rede",
        "protocolo",
        "comunicacao",
        "telecomunicacoes",
        "wireless",
        "5g",
        "roteamento",
    },
    "Segurança da Informação": {
        "seguranca",
        "criptografia",
        "privacidade",
        "vulnerabilidade",
        "ataque",
        "autenticacao",
        "forense",
    },
    "IoT, Sistemas Embarcados e Automação": {
        "iot",
        "internet",
        "coisas",
        "embarcado",
        "embarcados",
        "sensor",
        "sensores",
        "automacao",
        "arduino",
        "raspberry",
    },
    "Processamento de Imagens e Visão Computacional": {
        "imagem",
        "imagens",
        "visao",
        "computacional",
        "opencv",
        "reconhecimento",
        "deteccao",
    },
    "Banco de Dados e Sistemas de Informação": {
        "banco",
        "database",
        "sql",
        "nosql",
        "informacao",
        "sistema",
        "sistemas",
        "gestao",
    },
}

STOPWORDS_TITULOS = {
    "analise",
    "análise",
    "aplicacao",
    "aplicação",
    "avaliacao",
    "avaliação",
    "baseado",
    "baseada",
    "desenvolvimento",
    "estudo",
    "implementacao",
    "implementação",
    "proposta",
    "projeto",
    "sistema",
    "sistemas",
    "tcc",
    "trabalho",
    "uso",
    "utilizacao",
    "utilização",
}


def sem_acentos(texto: str) -> str:
    """Remove acentos preservando apenas caracteres ASCII equivalentes."""
    normalizado = unicodedata.normalize("NFKD", str(texto))
    return "".join(ch for ch in normalizado if not unicodedata.combining(ch))


def padronizar_colunas_tcc(df: pd.DataFrame) -> pd.DataFrame:
    """Padroniza nomes de colunas comuns de bases de TCC."""
    df_temp = df.copy()
    rename_dict: dict[str, str] = {}

    for col in df_temp.columns:
        col_lower = sem_acentos(str(col).strip().lower())
        if col_lower in {"titulo", "title"}:
            rename_dict[col] = "titulo"
        elif col_lower in {"engenharia", "curso", "graduacao"}:
            rename_dict[col] = "engenharia"
        elif col_lower in {"orientador", "orientadora", "professor", "docente"}:
            rename_dict[col] = "orientador"
        elif col_lower in {"ano", "year"}:
            rename_dict[col] = "ano"

    if rename_dict:
        df_temp = df_temp.rename(columns=rename_dict)
    return df_temp


def filtrar_engenharia_computacao(df: pd.DataFrame) -> pd.DataFrame:
    """Retorna registros cujo curso parece ser Engenharia da Computação."""
    if "engenharia" not in df.columns:
        return df.iloc[0:0].copy()

    curso = df["engenharia"].astype(str).map(lambda valor: sem_acentos(valor).lower())
    mascara = curso.str.contains("engenharia", na=False) & curso.str.contains(
        "comput", na=False
    )
    return df[mascara].copy()


def tokenizar_titulos(titulos: pd.Series | list[str]) -> list[str]:
    """Tokeniza títulos removendo stopwords acadêmicas e palavras curtas."""
    try:
        stopwords = {sem_acentos(palavra).lower() for palavra in get_portuguese_stopwords()}
    except LookupError:
        stopwords = {
            "a",
            "as",
            "com",
            "da",
            "das",
            "de",
            "do",
            "dos",
            "e",
            "em",
            "no",
            "nos",
            "o",
            "os",
            "para",
            "por",
            "um",
            "uma",
        }

    stopwords.update({sem_acentos(palavra).lower() for palavra in STOPWORDS_TITULOS})
    texto = " ".join(str(titulo) for titulo in titulos)
    texto = sem_acentos(texto).lower()
    tokens = re.findall(r"[a-z0-9]+", texto)
    return [
        token
        for token in tokens
        if len(token) >= 3 and token not in stopwords and not token.isdigit()
    ]


def termos_frequentes(titulos: pd.Series | list[str], limite: int = 8) -> list[str]:
    """Extrai os termos mais frequentes em uma lista de títulos."""
    contagem = Counter(tokenizar_titulos(titulos))
    return [termo for termo, _ in contagem.most_common(limite)]


def inferir_areas_pesquisa(titulos: pd.Series | list[str], limite: int = 3) -> list[str]:
    """Infere áreas de pesquisa por aproximação lexical a partir dos títulos."""
    tokens = set(tokenizar_titulos(titulos))
    pontuacoes = []
    for area, keywords in AREA_KEYWORDS.items():
        keywords_norm = {sem_acentos(keyword).lower() for keyword in keywords}
        score = len(tokens & keywords_norm)
        if score:
            pontuacoes.append((area, score))

    pontuacoes.sort(key=lambda item: (-item[1], item[0]))
    return [area for area, _ in pontuacoes[:limite]]


def ranquear_orientadores(
    df: pd.DataFrame,
    min_trabalhos: int = 1,
    top_termos: int = 6,
) -> pd.DataFrame:
    """Monta ranking de orientadores com termos e áreas recorrentes."""
    df_temp = padronizar_colunas_tcc(df)
    colunas_minimas = {"titulo", "orientador"}
    if df_temp.empty or not colunas_minimas.issubset(df_temp.columns):
        return pd.DataFrame(
            columns=[
                "orientador",
                "quantidade",
                "engenharias",
                "anos",
                "termos_recorrentes",
                "areas_inferidas",
            ]
        )

    df_temp = df_temp.copy()
    if "engenharia" not in df_temp.columns:
        df_temp["engenharia"] = "Não Informado"
    if "ano" not in df_temp.columns:
        df_temp["ano"] = "Não Informado"

    df_temp["orientador"] = (
        df_temp["orientador"].fillna("Não Informado").astype(str).str.title().str.strip()
    )
    df_temp["titulo"] = df_temp["titulo"].fillna("").astype(str).str.strip()
    df_temp = df_temp[
        df_temp["titulo"].ne("")
        & df_temp["orientador"].ne("")
        & df_temp["orientador"].ne("Não Informado")
    ]

    linhas = []
    for orientador, grupo in df_temp.groupby("orientador"):
        quantidade = len(grupo)
        if quantidade < min_trabalhos:
            continue

        engenharias = sorted(grupo["engenharia"].dropna().astype(str).unique())
        anos = sorted(grupo["ano"].dropna().astype(str).unique())
        termos = termos_frequentes(grupo["titulo"], limite=top_termos)
        areas = inferir_areas_pesquisa(grupo["titulo"])

        linhas.append(
            {
                "orientador": orientador,
                "quantidade": quantidade,
                "engenharias": ", ".join(engenharias),
                "anos": ", ".join(anos),
                "termos_recorrentes": ", ".join(termos) if termos else "Sem termos suficientes",
                "areas_inferidas": ", ".join(areas) if areas else "Área não inferida",
            }
        )

    ranking = pd.DataFrame(linhas)
    if ranking.empty:
        return ranking
    return ranking.sort_values(["quantidade", "orientador"], ascending=[False, True]).reset_index(
        drop=True
    )


def sugerir_temas(df: pd.DataFrame, orientador: str | None = None, limite: int = 8) -> list[str]:
    """Gera ideias iniciais de temas com base nos padrões da base."""
    df_temp = padronizar_colunas_tcc(df)
    if df_temp.empty or "titulo" not in df_temp.columns:
        return []

    if orientador and "orientador" in df_temp.columns:
        orientador_norm = str(orientador).strip().lower()
        df_temp = df_temp[df_temp["orientador"].astype(str).str.lower().str.strip() == orientador_norm]

    termos = termos_frequentes(df_temp["titulo"], limite=limite)
    areas = inferir_areas_pesquisa(df_temp["titulo"], limite=4)

    sugestoes: list[str] = []
    for area in areas or ["Engenharia da Computação"]:
        for termo in termos[:3]:
            sugestoes.append(f"{area}: estudo aplicado envolvendo {termo}")

    return sugestoes[:limite]


def sugerir_temas_por_interesses(
    df: pd.DataFrame,
    interesses: str,
    limite_orientadores: int = 5,
    temas_por_orientador: int = 3,
) -> pd.DataFrame:
    """Cruza interesses do aluno com o histórico dos orientadores."""
    ranking = ranquear_orientadores(df)
    if ranking.empty:
        return pd.DataFrame(
            columns=["orientador", "aderencia", "areas_inferidas", "temas_sugeridos"]
        )

    tokens_interesse = set(tokenizar_titulos([interesses]))
    areas_interesse = set(inferir_areas_pesquisa([interesses], limite=5))
    linhas = []

    df_padronizado = padronizar_colunas_tcc(df)
    for _, linha in ranking.iterrows():
        orientador = linha["orientador"]
        titulos = df_padronizado[
            df_padronizado["orientador"].astype(str).str.title().str.strip() == orientador
        ]["titulo"]
        tokens_orientador = set(tokenizar_titulos(titulos))
        areas_orientador = {
            area.strip()
            for area in str(linha["areas_inferidas"]).split(",")
            if area.strip() and area.strip() != "Área não inferida"
        }

        termos_em_comum = sorted(tokens_interesse & tokens_orientador)
        areas_em_comum = sorted(areas_interesse & areas_orientador)
        aderencia = len(termos_em_comum) + (2 * len(areas_em_comum))

        if aderencia == 0:
            continue

        temas = _montar_temas_combinados(
            termos_interesse=sorted(tokens_interesse),
            termos_orientador=sorted(tokens_orientador),
            areas=areas_em_comum or sorted(areas_orientador) or sorted(areas_interesse),
            limite=temas_por_orientador,
        )
        linhas.append(
            {
                "orientador": orientador,
                "aderencia": aderencia,
                "areas_inferidas": linha["areas_inferidas"],
                "termos_em_comum": ", ".join(termos_em_comum) or "Sem termo literal em comum",
                "temas_sugeridos": "\n".join(temas),
            }
        )

    sugestoes = pd.DataFrame(linhas)
    if sugestoes.empty:
        return sugestoes
    return sugestoes.sort_values(
        ["aderencia", "orientador"], ascending=[False, True]
    ).head(limite_orientadores)


def _montar_temas_combinados(
    termos_interesse: list[str],
    termos_orientador: list[str],
    areas: list[str],
    limite: int,
) -> list[str]:
    """Monta frases de temas a partir de áreas e termos cruzados."""
    termos_prioritarios = []
    for termo in termos_interesse + termos_orientador:
        if termo not in termos_prioritarios:
            termos_prioritarios.append(termo)

    area_base = areas[0] if areas else "Engenharia da Computação"
    templates = [
        "Plataforma web para apoio à decisão em saúde usando análise de dados",
        "Sistema de gestão e visualização de indicadores para serviços de saúde",
        "Dashboard inteligente para monitoramento de pacientes e processos clínicos",
        "Aplicação para triagem, acompanhamento ou priorização de atendimentos em saúde",
        "Mineração de dados de saúde para identificar padrões e apoiar decisões clínicas",
        "Arquitetura de software para integração de dados em saúde digital",
    ]

    temas = [f"{area_base}: {template[0].lower() + template[1:]}" for template in templates]
    for termo in termos_prioritarios[:3]:
        temas.append(f"{area_base}: solução de software em saúde com foco em {termo}")

    return temas[:limite]
