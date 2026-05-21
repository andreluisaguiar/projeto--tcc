# 🎓 Projeto TCC — NLP para Previsão de Engenharia

Aplicação que utiliza **Processamento de Linguagem Natural (NLP)** para prever a escolha de engenharia a partir de títulos de TCC no BICT (Bacharelado Interdisciplinar em Ciência e Tecnologia).

## 📋 Funcionalidades

| Funcionalidade | Descrição |
|---|---|
| **Coleta de Dados** | Web scraping automatizado do SIGAA para extrair monografias |
| **Remoção de Duplicatas** | Merge de múltiplos arquivos Excel com deduplicação |
| **Detecção de Outliers** | Análise semântica com spaCy para identificar títulos inconsistentes |
| **Treinamento e Teste** | Comparação de 6 algoritmos de ML (RF, NB, SVM, KNN, DT, XGBoost) |
| **Treinamento e Predição** | Pipeline completo com SMOTE + previsão de engenharia por título |

## 🛠️ Stack Tecnológica

- **Interface**: Streamlit (multi-page app)
- **ML/NLP**: scikit-learn, XGBoost, spaCy, NLTK
- **Scraping**: Selenium + ChromeDriver
- **Dados**: pandas, openpyxl

## 🚀 Como Executar

### Pré-requisitos

- Python 3.10+
- Google Chrome ou Chromium (para a funcionalidade de coleta)
- ChromeDriver compatível

### Instalação

```bash
# Clonar o repositório
git clone <URL_DO_REPOSITORIO>
cd projeto-tcc

# Criar ambiente virtual
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Instalar dependências
pip install -r requirements.txt

# Baixar modelo spaCy para português
python -m spacy download pt_core_news_md

# Baixar stopwords do NLTK
python -c "import nltk; nltk.download('stopwords')"
```

### Configuração (opcional)

Crie um arquivo `.env` na raiz do projeto:

```env
CHROME_BINARY_PATH=/usr/bin/google-chrome
CHROMEDRIVER_PATH=/usr/bin/chromedriver
```

### Executar

```bash
streamlit run app.py
```

A aplicação estará disponível em `http://localhost:8501`.

## 📁 Estrutura do Projeto

```
projeto-tcc/
├── app.py                  # Entry point do Streamlit
├── pages/                  # Páginas do Streamlit (multi-page)
│   ├── 1_coleta.py
│   ├── 2_duplicatas.py
│   ├── 3_outliers.py
│   ├── 4_treinamento_teste.py
│   └── 5_predicao.py
├── src/                    # Lógica de negócio
│   ├── config.py
│   ├── scraping/
│   ├── preprocessing/
│   ├── models/
│   └── utils/
├── data/                   # Dados (não versionados)
├── tests/                  # Testes automatizados
└── requirements.txt
```

## 📄 Licença

Este projeto é parte de um Trabalho de Conclusão de Curso (TCC).
