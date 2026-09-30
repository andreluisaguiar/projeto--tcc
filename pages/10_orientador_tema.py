"""Página: Apoio à escolha de orientador e tema de TCC."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from src.preprocessing.orientador_tema import (
    filtrar_engenharia_computacao,
    padronizar_colunas_tcc,
    ranquear_orientadores,
    sugerir_temas,
    sugerir_temas_por_interesses,
)
from src.utils.db import obter_todos_tccs
from src.utils.io_helpers import read_excel

st.set_page_config(page_title="Orientador e Tema", layout="wide")

st.header("Orientador e Tema para TCC")
st.write(
    "Analise os TCCs de Engenharia da Computação para identificar orientadores "
    "mais recorrentes, áreas aproximadas de pesquisa e ideias iniciais de temas."
)

st.divider()

df: pd.DataFrame | None = None
df_db = obter_todos_tccs(incluir_outliers=False, incluir_duplicadas=False)
if not df_db.empty:
    df = df_db
    st.info(f"Carregados {len(df)} registros limpos diretamente do SQLite.")
else:
    uploaded_file = st.file_uploader(
        "Envie uma planilha com TCCs de Engenharia da Computação",
        type=["xlsx"],
        help=(
            "Use colunas como titulo, engenharia/curso, orientador/orientadora e ano. "
            "Se o banco SQLite estiver vazio, a análise usa este arquivo."
        ),
    )
    if uploaded_file is not None:
        df = read_excel(uploaded_file)

if df is None:
    st.info("Importe uma planilha no Gerenciamento de Dados ou envie um Excel acima.")
    st.stop()

df = padronizar_colunas_tcc(df)
colunas_obrigatorias = {"titulo", "orientador"}
if not colunas_obrigatorias.issubset(df.columns):
    st.error("A base precisa conter pelo menos as colunas 'titulo' e 'orientador'.")
    st.stop()

if "engenharia" not in df.columns:
    st.warning(
        "A coluna de curso/engenharia não foi encontrada. A análise usará toda a base."
    )
    df_comp = df.copy()
else:
    df_comp = filtrar_engenharia_computacao(df)
    if df_comp.empty:
        st.warning(
            "Não encontrei registros com curso parecido com Engenharia da Computação. "
            "A análise abaixo usará toda a base disponível."
        )
        df_comp = df.copy()

if "ano" not in df_comp.columns:
    df_comp["ano"] = "Não Informado"

df_comp["ano"] = df_comp["ano"].astype(str).str.strip()
df_comp["orientador"] = df_comp["orientador"].astype(str).str.title().str.strip()

st.sidebar.header("Filtros")
anos_disponiveis = sorted(df_comp["ano"].dropna().unique())
anos_selecionados = st.sidebar.multiselect(
    "Ano",
    options=anos_disponiveis,
    default=anos_disponiveis,
)

min_trabalhos = st.sidebar.slider(
    "Mínimo de TCCs por orientador",
    min_value=1,
    max_value=max(1, int(df_comp["orientador"].value_counts().max())),
    value=1,
)

top_n = st.sidebar.slider("Quantidade no ranking", 5, 30, 10, 1)

df_filtrado = df_comp[df_comp["ano"].isin(anos_selecionados)]
if df_filtrado.empty:
    st.warning("Nenhum registro encontrado com os filtros selecionados.")
    st.stop()

ranking = ranquear_orientadores(df_filtrado, min_trabalhos=min_trabalhos)
if ranking.empty:
    st.warning("Nenhum orientador atingiu o mínimo de TCCs escolhido.")
    st.stop()

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
with kpi1:
    st.metric("TCCs analisados", len(df_filtrado))
with kpi2:
    st.metric("Orientadores no ranking", len(ranking))
with kpi3:
    st.metric("Maior volume por orientador", int(ranking["quantidade"].max()))
with kpi4:
    st.metric("Anos analisados", df_filtrado["ano"].nunique())

st.divider()

col_grafico, col_tabela = st.columns([1.1, 1.4])

with col_grafico:
    st.subheader("Professores que mais aparecem")
    ranking_top = ranking.head(top_n)
    fig = px.bar(
        ranking_top,
        x="quantidade",
        y="orientador",
        orientation="h",
        color="quantidade",
        color_continuous_scale=px.colors.sequential.Teal,
        labels={
            "orientador": "Orientador",
            "quantidade": "TCCs orientados",
        },
    )
    fig.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig, use_container_width=True)

with col_tabela:
    st.subheader("Áreas e termos por orientador")
    st.dataframe(
        ranking_top[
            [
                "orientador",
                "quantidade",
                "areas_inferidas",
                "termos_recorrentes",
                "anos",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )

st.divider()

st.subheader("Temas alinhados ao seu perfil")
interesses_aluno = st.text_area(
    "Descreva suas áreas de atuação e interesse",
    value=(
        "desenvolvimento de software na área da saúde, sistemas web, dashboards, "
        "ciência de dados, análise de dados e apoio à decisão"
    ),
    height=90,
)

col_perfil1, col_perfil2 = st.columns([1, 1])
with col_perfil1:
    limite_matches = st.slider("Orientadores compatíveis", 3, 10, 5, 1)
with col_perfil2:
    temas_por_professor = st.slider("Temas por orientador", 2, 5, 3, 1)

sugestoes_perfil = sugerir_temas_por_interesses(
    df_filtrado,
    interesses=interesses_aluno,
    limite_orientadores=limite_matches,
    temas_por_orientador=temas_por_professor,
)

if sugestoes_perfil.empty:
    st.info(
        "Ainda não encontrei orientadores com aderência lexical ao seu perfil. "
        "Depois de importar mais TCCs, tente termos como saúde, dados, software, "
        "web, dashboard, paciente, hospital ou predição."
    )
else:
    st.dataframe(
        sugestoes_perfil[
            [
                "orientador",
                "aderencia",
                "areas_inferidas",
                "termos_em_comum",
                "temas_sugeridos",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )

st.divider()

st.subheader("Explorar um orientador")
orientador_escolhido = st.selectbox(
    "Selecione um orientador para ver padrões e possíveis temas",
    options=ranking["orientador"].tolist(),
)

df_orientador = df_filtrado[
    df_filtrado["orientador"].astype(str).str.title().str.strip() == orientador_escolhido
]
linha_orientador = ranking[ranking["orientador"] == orientador_escolhido].iloc[0]

col_resumo, col_temas = st.columns([1, 1])
with col_resumo:
    st.write("**Resumo do orientador**")
    st.metric("TCCs orientados", int(linha_orientador["quantidade"]))
    st.write(f"**Áreas inferidas:** {linha_orientador['areas_inferidas']}")
    st.write(f"**Termos recorrentes:** {linha_orientador['termos_recorrentes']}")
    st.write(f"**Anos:** {linha_orientador['anos']}")

with col_temas:
    st.write("**Ideias iniciais de tema**")
    temas = sugerir_temas(df_filtrado, orientador=orientador_escolhido, limite=6)
    if temas:
        for tema in temas:
            st.markdown(f"- {tema}")
    else:
        st.info("Não há termos suficientes para sugerir temas para este orientador.")

st.write("**Títulos já orientados**")
colunas_titulos = ["titulo", "ano"]
if "engenharia" in df_orientador.columns:
    colunas_titulos.append("engenharia")
st.dataframe(
    df_orientador[colunas_titulos].sort_values("ano", ascending=False),
    use_container_width=True,
    hide_index=True,
)

st.caption(
    "As áreas são inferidas automaticamente a partir dos títulos. Use o resultado "
    "como triagem inicial e confirme a linha de pesquisa no currículo, laboratório "
    "ou página institucional do professor."
)
