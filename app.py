"""
Projeto TCC — NLP para Previsão de Engenharia a partir de Títulos de TCC no BICT.

Este é o entry point do Streamlit multi-page app.
As páginas individuais estão no diretório pages/.
"""

import streamlit as st

st.set_page_config(
    page_title="Projeto TCC — NLP para Engenharia",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Home Page ────────────────────────────────────────────────────────────────

st.title("🎓 Projeto TCC")
st.subheader(
    "Utilizando Processamento de Linguagem Natural para Prever a Escolha "
    "de Engenharia a Partir de Títulos de TCC no BICT"
)

st.divider()

st.markdown("""
## 🚀 Como usar

Navegue pelas funcionalidades usando o **menu lateral** à esquerda:

| Página | Descrição |
|---|---|
| ⚙️ **Gerenciamento de Dados** | Importe a base uma vez e mantenha os dados no SQLite |
| 📊 **Dashboard** | Explore estatísticas interativas e nuvem de palavras dos temas |
| 📥 **Coleta** | Extraia monografias diretamente do SIGAA |
| 🧹 **Duplicatas** | Combine arquivos e remova registros duplicados |
| 🔍 **Outliers** | Detecte títulos inconsistentes via similaridade semântica |
| 🔎 **Busca Semântica** | Pesquise títulos por similaridade com spaCy |
| 🧪 **Treinamento e Teste** | Compare algoritmos de ML com diferentes configurações |
| 🎯 **Predição** | Treine modelos e preveja engenharias por título |
| 🧾 **Relatórios** | Exporte um PDF consolidado com estatísticas do projeto |

---

## 📊 Pipeline do Projeto

```
   Coleta (SIGAA)
        │
        ▼
   Remoção de Duplicatas
        │
        ▼
   Detecção de Outliers
        │
        ▼
   Busca / Persistência SQLite
        │
        ▼
   Treinamento de Modelos
        │
        ▼
   Predição de Engenharia
```

---

## 🛠️ Stack Tecnológica

- **Interface**: Streamlit
- **ML/NLP**: scikit-learn, XGBoost, spaCy, NLTK
- **Scraping**: Selenium + ChromeDriver
- **Dados**: pandas, openpyxl, SQLite
- **Relatórios**: fpdf2
- **Deploy**: Docker
""")

# Sidebar info
st.sidebar.success("👆 Selecione uma página acima.")
st.sidebar.divider()
st.sidebar.markdown("**Projeto de TCC** — UFMA")
