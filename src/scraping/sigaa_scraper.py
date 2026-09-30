"""Web scraping de monografias do SIGAA."""

import io

import pandas as pd
from selenium.common.exceptions import (
    NoAlertPresentException,
    TimeoutException,
    UnexpectedAlertPresentException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from src.scraping.driver import criar_driver
from src.utils.logging_config import logger

ALERTA_BOTAO_VOLTAR = "botão voltar"


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

        alerta_inicial = _aceitar_alerta_se_existir(driver)
        if alerta_inicial:
            logger.warning("Alerta exibido pelo SIGAA ao abrir a página: %s", alerta_inicial)
            if ALERTA_BOTAO_VOLTAR in alerta_inicial.lower():
                raise RuntimeError(
                    "O SIGAA recusou a URL informada com o aviso de uso do botão voltar. "
                    "Abra a página pública do curso pelo próprio SIGAA e copie a URL completa "
                    "da tela de monografias, incluindo os parâmetros da URL, como 'id=...'."
                )

        # O SIGAA exige ao menos um critério. Usamos título coringa para listar
        # todas as monografias disponíveis na página do curso.
        wait = WebDriverWait(driver, 20)
        try:
            wait.until(EC.element_to_be_clickable((By.ID, "form:checkTitulo"))).click()
        except UnexpectedAlertPresentException as exc:
            alerta = _aceitar_alerta_se_existir(driver) or str(exc)
            raise RuntimeError(_mensagem_alerta_sigaa(alerta)) from exc
        except TimeoutException as exc:
            raise RuntimeError(
                "Não encontrei o formulário de busca de monografias nessa página. "
                "Verifique se a URL é a tela pública de monografias de um curso específico "
                "do SIGAA, e não apenas a URL genérica 'monografias_curso.jsf'."
            ) from exc

        titulo_input = wait.until(EC.presence_of_element_located((By.ID, "form:titulo")))
        titulo_input.clear()
        titulo_input.send_keys("%")

        search_button = wait.until(EC.element_to_be_clickable((By.ID, "form:buscar")))
        search_button.click()
        alerta_busca = _aceitar_alerta_se_existir(driver)
        if alerta_busca:
            raise RuntimeError(_mensagem_alerta_sigaa(alerta_busca))

        # Aguardando a tela carregar
        try:
            wait.until(lambda browser: len(browser.find_elements(By.CSS_SELECTOR, "table.table_lt")) > 0)
        except UnexpectedAlertPresentException as exc:
            alerta = _aceitar_alerta_se_existir(driver) or str(exc)
            raise RuntimeError(_mensagem_alerta_sigaa(alerta)) from exc
        except TimeoutException as exc:
            raise RuntimeError(
                "A busca foi enviada, mas a tabela de monografias não apareceu. "
                "Tente novamente com a URL completa do curso no SIGAA ou reduza o critério de busca."
            ) from exc

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


def _aceitar_alerta_se_existir(driver) -> str | None:
    """Aceita um alerta JavaScript aberto e retorna seu texto, se existir."""
    try:
        alert = driver.switch_to.alert
        texto = alert.text
        alert.accept()
        return texto
    except NoAlertPresentException:
        return None


def _mensagem_alerta_sigaa(alerta: str) -> str:
    """Converte alertas conhecidos do SIGAA em mensagens acionáveis."""
    if ALERTA_BOTAO_VOLTAR in alerta.lower():
        return (
            "O SIGAA interrompeu a coleta com o aviso de uso do botão voltar. "
            "Isso costuma acontecer quando a URL é genérica ou perdeu os parâmetros "
            "da sessão do curso. Acesse o curso pelo SIGAA, entre em Monografias e "
            "copie a URL completa da página, incluindo parâmetros como 'id=...'."
        )

    return f"O SIGAA exibiu um alerta e interrompeu a coleta: {alerta}"
