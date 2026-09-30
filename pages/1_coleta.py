"""Página: Coleta de Dados do SIGAA."""

import streamlit as st
from src.scraping.sigaa_scraper import scrape_monografias

st.set_page_config(page_title="Coleta de Dados")

st.header("Coleta de Dados")
st.write(
    "Extraia monografias diretamente do SIGAA. Insira a URL da página de "
    "monografias do curso desejado e clique em **Buscar Monografias**. Use a "
    "URL completa do curso, normalmente com parâmetros como `id=...`."
)

st.divider()

url_input = st.text_input(
    "URL do SIGAA",
    placeholder="https://sigaa.ufma.br/sigaa/public/curso/monografias_curso.jsf?lc=pt_BR&id=...",
)

if st.button("Buscar Monografias", type="primary"):
    url_input = url_input.strip()
    if not url_input:
        st.error("Por favor, insira uma URL válida.")
    else:
        with st.spinner("Extraindo monografias do SIGAA... Isso pode levar alguns segundos."):
            try:
                excel_data = scrape_monografias(url_input)
                if excel_data:
                    st.success("Coleta concluída com sucesso!")
                    st.download_button(
                        label="Baixar Arquivo Excel",
                        data=excel_data,
                        file_name="dataset_monografias.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        type="primary",
                    )
                else:
                    st.error(
                        "Não foi possível concluir a coleta. Verifique se a URL é a página "
                        "pública completa de monografias do curso no SIGAA."
                    )
            except (ValueError, RuntimeError) as exc:
                st.error(f"{exc}")
