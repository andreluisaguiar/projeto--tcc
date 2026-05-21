from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException
import pandas as pd
import time
from selenium.webdriver.chrome.service import Service
import io
import os
import shutil
import tempfile


def criar_driver():
    # Se CHROMEDRIVER_PATH não for informado, o Selenium Manager tenta
    # localizar/baixar o driver compatível com o navegador instalado.
    driver_path = os.getenv("CHROMEDRIVER_PATH") or shutil.which("chromedriver")
    browser_path = os.getenv("CHROME_BINARY_PATH") or localizar_navegador()

    if driver_path and not os.path.isfile(driver_path):
        raise FileNotFoundError(f"CHROMEDRIVER_PATH não é um arquivo válido: {driver_path}")

    if browser_path and not os.path.isfile(browser_path):
        raise FileNotFoundError(f"CHROME_BINARY_PATH não é um arquivo válido: {browser_path}")

    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")
    options.add_argument(f"--user-data-dir={tempfile.mkdtemp(prefix='chromium-profile-')}")

    if browser_path:
        options.binary_location = browser_path

    service = Service(driver_path) if driver_path else Service()

    try:
        return webdriver.Chrome(service=service, options=options)
    except WebDriverException as exc:
        raise RuntimeError(
            "Não foi possível iniciar o Chrome/ChromeDriver. "
            "Instale o Google Chrome ou Chromium e um ChromeDriver compatível, "
            "ou defina as variáveis CHROME_BINARY_PATH e CHROMEDRIVER_PATH. "
            f"Caminho do navegador: {browser_path or 'não encontrado'}; "
            f"caminho do driver: {driver_path or 'não encontrado'}."
        ) from exc


def localizar_navegador():
    candidatos = [
        "google-chrome",
        "google-chrome-stable",
        "chromium-browser",
        "chromium",
        "/snap/bin/chromium",
        "brave-browser",
        "microsoft-edge",
    ]

    for nome in candidatos:
        caminho = shutil.which(nome)
        if caminho:
            return caminho

    return None

# Função de scraping
def scrape_monografias(url):
    driver = None
    url = (url or "").strip()

    if not url:
        raise ValueError("A URL informada está vazia.")

    if not url.startswith(("http://", "https://")):
        raise ValueError(f"URL inválida: {url}")

    try:
        driver = criar_driver()

        # Acessa o site da URL
        driver.get(url)

        # O SIGAA exige ao menos um critério. Usamos título coringa para listar
        # todas as monografias disponíveis na página do curso.
        wait = WebDriverWait(driver, 20)
        wait.until(EC.element_to_be_clickable((By.ID, "form:checkTitulo"))).click()
        titulo_input = wait.until(EC.presence_of_element_located((By.ID, "form:titulo")))
        titulo_input.clear()
        titulo_input.send_keys("%")

        search_button = wait.until(EC.element_to_be_clickable((By.ID, "form:buscar")))
        search_button.click()

        # Aguardando a tela carregar
        wait.until(lambda browser: len(browser.find_elements(By.CSS_SELECTOR, "table.table_lt")) > 0)

        # Localizar a tabela de monografias
        table = driver.find_element(By.CSS_SELECTOR, "table.table_lt")
        rows = table.find_elements(By.TAG_NAME, "tr")

        # Extrair dados da tabela
        data = []
        for i in range(1, len(rows) - 1):
            row = rows[i]
            cols = row.find_elements(By.TAG_NAME, "td")

            if len(cols) >= 5:
                ano = cols[0].text.strip()
                date = cols[1].text.strip()
                aluno = cols[2].text.strip()
                orientador = cols[3].text.strip()
                curso = cols[4].text.strip()

                # Verifica se a próxima linha contém o título
                next_row = rows[i + 1]
                next_cols = next_row.find_elements(By.TAG_NAME, "td")

                # Verificar se o <td> possui "colspan" e contém o texto "Título:"
                titulo = ""
                if len(next_cols) == 1 and "Título:" in next_cols[0].text:
                    titulo = next_cols[0].text.split("Título:")[1].strip()

                # Adicionando dados à lista
                data.append([ano, date, aluno, orientador, curso, titulo])

        # Converter para DataFrame
        df = pd.DataFrame(data, columns=["Ano", "Data", "Aluno", "Orientador", "Curso", "Título"])

        # Salvar como arquivo Excel em memória
        output = io.BytesIO()
        df.to_excel(output, index=False, engine='openpyxl')
        output.seek(0)  # Retorna ao início do arquivo para download

        return output
    
    except Exception as e:
        print(f"Erro durante o scraping: {e}")
        return None
    
    finally:
        if driver is not None:
            driver.quit()
