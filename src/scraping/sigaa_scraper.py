"""Web scraping de monografias do SIGAA."""

import io

import pandas as pd
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from src.scraping.driver import criar_driver
from src.utils.logging_config import logger


def scrape_monografias(url: str) -> io.BytesIO | None:
    """Coleta monografias do SIGAA a partir da URL fornecida.

    Acessa a página de monografias do SIGAA, preenche o campo de busca com
    um caractere curinga '%' para listar todas as monografias, e extrai os
    dados da tabela resultante.

    Args:
        url: URL da página de monografias do SIGAA.

    Returns:
        BytesIO com arquivo Excel contendo as monografias, ou None em caso de erro.

    Raises:
        ValueError: Se a URL estiver vazia ou for inválida.
    """
    url = (url or "").strip()

    if not url:
        raise ValueError("A URL informada está vazia.")

    if not url.startswith(("http://", "https://")):
        raise ValueError(f"URL inválida: {url}")

    driver = None
    try:
        driver = criar_driver()
        logger.info("Acessando URL: %s", url)
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
        data = _extrair_dados_tabela(rows)

        # Converter para DataFrame
        df = pd.DataFrame(data, columns=["Ano", "Data", "Aluno", "Orientador", "Curso", "Título"])
        logger.info("Monografias coletadas: %d registros", len(df))

        # Salvar como arquivo Excel em memória
        output = io.BytesIO()
        df.to_excel(output, index=False, engine="openpyxl")
        output.seek(0)

        return output

    except (ValueError, RuntimeError):
        raise
    except Exception as e:
        logger.error("Erro durante o scraping: %s", e)
        return None

    finally:
        if driver is not None:
            driver.quit()
            logger.info("WebDriver encerrado")


def _extrair_dados_tabela(rows: list) -> list[list[str]]:
    """Extrai dados estruturados das linhas da tabela do SIGAA.

    Args:
        rows: Lista de WebElements representando as linhas da tabela.

    Returns:
        Lista de registros [ano, data, aluno, orientador, curso, titulo].
    """
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

            titulo = ""
            if len(next_cols) == 1 and "Título:" in next_cols[0].text:
                titulo = next_cols[0].text.split("Título:")[1].strip()

            data.append([ano, date, aluno, orientador, curso, titulo])

    return data
