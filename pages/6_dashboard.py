"""Página: Dashboard Analítico Interativo (Análise Descritiva)."""

from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import streamlit as st
from wordcloud import WordCloud

from src.preprocessing.text_processor import get_portuguese_stopwords
from src.utils.db import obter_todos_tccs
from src.utils.io_helpers import read_excel

st.set_page_config(page_title="Dashboard Analítico", layout="wide")

st.header("Dashboard Analítico Interativo")
st.write(
    "Explore estatísticas descritivas, nuvem de palavras de temas por engenharia, "
    "orientadores mais populares e evolução temporal de monografias no BICT."
)

st.divider()

df = None
df_db = obter_todos_tccs(incluir_outliers=False, incluir_duplicadas=False)
if not df_db.empty:
    df = df_db
    st.info(f"Carregados {len(df)} registros limpos diretamente do SQLite.")
else:
    uploaded_file = st.file_uploader(
        "Envie o arquivo Excel para análise descritiva",
        type=["xlsx"],
        help="Envie um dataset de monografias limpo ou processado para gerar os gráficos.",
    )
    if uploaded_file is not None:
        df = read_excel(uploaded_file)

@st.cache_data
def padronizar_df(df_in: pd.DataFrame) -> pd.DataFrame:
    df_temp = df_in.copy()
    # Padronizar nomes de colunas comuns
    rename_dict = {}
    for col in df_temp.columns:
        if col.lower() in ["titulo", "título"]:
            rename_dict[col] = "titulo"
        elif col.lower() in ["engenharia", "curso"]:
            rename_dict[col] = "engenharia"
        elif col.lower() in ["orientador", "orientadora"]:
            rename_dict[col] = "orientador"
        elif col.lower() in ["ano"]:
            rename_dict[col] = "ano"
    
    if rename_dict:
        df_temp = df_temp.rename(columns=rename_dict)
    return df_temp


if df is not None:
    df = padronizar_df(df)
    
    # Validar colunas essenciais
    colunas_obrigatorias = ["titulo"]
    colunas_presentes = [c for c in colunas_obrigatorias if c in df.columns]
    
    if not colunas_presentes:
        st.error("O arquivo precisa conter pelo menos a coluna 'titulo' ou 'título'.")
        st.stop()
        
    # Preencher colunas ausentes comuns com valores genéricos para não falhar a renderização
    if "ano"not in df.columns:
        df["ano"] = "Não Informado"
    if "orientador"not in df.columns:
        df["orientador"] = "Não Informado"
    if "engenharia"not in df.columns:
        df["engenharia"] = "Geral"

    # Limpar dados
    df["ano"] = df["ano"].astype(str).str.strip()
    df["orientador"] = df["orientador"].astype(str).str.title().str.strip()
    df["engenharia"] = df["engenharia"].astype(str).str.strip()

    # ─── Filtros Interativos na Barra Lateral ───────────────────────────────
    st.sidebar.header("Filtros Interativos")
    
    # Filtro por Engenharia/Curso
    engenharias_disponiveis = sorted(df["engenharia"].unique())
    eng_selecionadas = st.sidebar.multiselect(
        "Engenharia / Curso",
        options=engenharias_disponiveis,
        default=engenharias_disponiveis,
    )
    
    # Filtro por Ano
    anos_disponiveis = sorted(df["ano"].unique())
    anos_selecionados = st.sidebar.multiselect(
        "Ano de Publicação",
        options=anos_disponiveis,
        default=anos_disponiveis,
    )

    # Filtrar DataFrame com base nas seleções
    df_filtrado = df[
        (df["engenharia"].isin(eng_selecionadas)) & 
        (df["ano"].isin(anos_selecionados))
    ]

    if df_filtrado.empty:
        st.warning("Nenhum registro encontrado com os filtros selecionados.")
        st.stop()

    # ─── KPIS Principais ──────────────────────────────────────────────────
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.metric("Total de Monografias", len(df_filtrado))
    with kpi2:
        st.metric("Cursos / Engenharias", df_filtrado["engenharia"].nunique())
    with kpi3:
        st.metric("Orientadores Ativos", df_filtrado["orientador"].nunique())
    with kpi4:
        media_orient = len(df_filtrado) / df_filtrado["orientador"].nunique() if df_filtrado["orientador"].nunique() > 0 else 0
        st.metric("Média Monografias / Orientador", f"{media_orient:.1f}")

    st.divider()

    # ─── Distribuição Temporal e Orientadores ───────────────────────────────
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.subheader("Evolução Temporal de Publicações")
        df_temporal = df_filtrado.groupby(["ano", "engenharia"]).size().reset_index(name="Quantidade")
        df_temporal = df_temporal.sort_values("ano")
        fig_temporal = px.bar(
            df_temporal, 
            x="ano", 
            y="Quantidade", 
            color="engenharia",
            title="Monografias por Ano e Engenharia",
            barmode="group",
            labels={"ano": "Ano", "Quantidade": "Quantidade", "engenharia": "Engenharia/Curso"},
            color_discrete_sequence=px.colors.qualitative.Safe
        )
        st.plotly_chart(fig_temporal, use_container_width=True)
        
    with col_chart2:
        st.subheader("‍ Top 10 Orientadores")
        df_orientadores = df_filtrado["orientador"].value_counts().reset_index()
        df_orientadores.columns = ["Orientador", "Quantidade"]
        top_orientadores = df_orientadores.head(10)
        fig_orientadores = px.bar(
            top_orientadores, 
            y="Orientador", 
            x="Quantidade", 
            orientation="h",
            title="Orientadores com mais trabalhos dirigidos",
            labels={"Orientador": "Orientador", "Quantidade": "Monografias Orientadas"},
            color="Quantidade",
            color_continuous_scale=px.colors.sequential.Viridis
        )
        fig_orientadores.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_orientadores, use_container_width=True)

    st.divider()

    # ─── Análise de Temas por Nuvem de Palavras ─────────────────────────────
    st.subheader("Nuvem de Palavras por Engenharia (Word Cloud)")
    st.write(
        "Veja visualmente quais termos e temas são mais recorrentes nos títulos dos TCCs."
    )
    
    col_wc1, col_wc2 = st.columns([1, 3])
    
    with col_wc1:
        st.write("**Parâmetros da Nuvem:**")
        # Filtro de curso específico para a nuvem
        curso_wc = st.selectbox(
            "Selecione um curso para a Nuvem de Palavras",
            options=["Todos"] + list(engenharias_disponiveis)
        )
        max_words = st.slider("Máximo de palavras", 30, 200, 100, 10)
        bg_color = st.selectbox("Cor de Fundo", ["white", "black"])
        
    with col_wc2:
        # Filtrar títulos para a nuvem
        if curso_wc == "Todos":
            titulos_wc = df_filtrado["titulo"].dropna().tolist()
        else:
            titulos_wc = df_filtrado[df_filtrado["engenharia"] == curso_wc]["titulo"].dropna().tolist()
            
        texto_wc = " ".join(titulos_wc)
        
        if texto_wc.strip():
            # Stopwords em português
            stopwords_pt = get_portuguese_stopwords()
            # Adicionar algumas stopwords comuns em títulos acadêmicos
            stopwords_adicionais = [
                "estudo", "analise", "desenvolvimento", "aplicacao", "projeto", 
                "usando", "bict", "compara", "base", "partir", "uso", "sob", "tcc",
                "analise", "estudo", "avaliação", "desenvolvimento", "projeto",
                "aplicação", "sistema", "sistemas"
            ]
            stopwords_completo = set(stopwords_pt + stopwords_adicionais)
            
            with st.spinner("Gerando nuvem de palavras..."):
                wc = WordCloud(
                    width=800,
                    height=400,
                    max_words=max_words,
                    background_color=bg_color,
                    stopwords=stopwords_completo,
                    colormap="viridis",
                    random_state=42
                ).generate(texto_wc)
                
                fig_wc, ax = plt.subplots(figsize=(10, 5))
                ax.imshow(wc, interpolation="bilinear")
                ax.axis("off")
                plt.tight_layout(pad=0)
                st.pyplot(fig_wc)
        else:
            st.info("ℹ Não há títulos suficientes para gerar a nuvem de palavras.")
            
else:
    st.info("Por favor, envie um arquivo Excel na barra superior para iniciar o dashboard!")
    
    # Mostrar um exemplo visual se houver arquivos em data/raw/
    import os
    from pathlib import Path
    
    data_raw_dir = Path("data/raw")
    if data_raw_dir.exists():
        excel_files = list(data_raw_dir.glob("*.xlsx"))
        if excel_files:
            st.write("---")
            st.subheader("Arquivos de exemplo detectados:")
            st.write("Você pode testar usando um dos arquivos já disponíveis na pasta de dados:")
            for f in excel_files:
                st.info(f"Caminho do arquivo: `{f}`")
