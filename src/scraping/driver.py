"""Criação e gerenciamento do WebDriver Chrome/Chromium."""

import os
import shutil
import tempfile

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import WebDriverException

from src.config import CHROME_BINARY_PATH, CHROMEDRIVER_PATH, CHROME_CANDIDATES
from src.utils.logging_config import logger


def _localizar_navegador() -> str | None:
    """Busca um navegador Chrome/Chromium instalado no sistema.

    Returns:
        Caminho absoluto do executável encontrado, ou None.
    """
    for nome in CHROME_CANDIDATES:
        caminho = shutil.which(nome)
        if caminho:
            logger.info("Navegador encontrado: %s", caminho)
            return caminho
    return None


def criar_driver() -> webdriver.Chrome:
    """Cria e retorna uma instância do Chrome WebDriver em modo headless.

    Tenta localizar o ChromeDriver e o navegador automaticamente via variáveis
    de ambiente ou busca no PATH do sistema.

    Returns:
        Instância configurada do Chrome WebDriver.

    Raises:
        FileNotFoundError: Se o caminho configurado não for um arquivo válido.
        RuntimeError: Se não for possível iniciar o navegador.
    """
    driver_path = CHROMEDRIVER_PATH or os.getenv("CHROMEDRIVER_PATH") or shutil.which("chromedriver")
    browser_path = CHROME_BINARY_PATH or os.getenv("CHROME_BINARY_PATH") or _localizar_navegador()

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
        driver = webdriver.Chrome(service=service, options=options)
        logger.info("WebDriver iniciado com sucesso")
        return driver
    except WebDriverException as exc:
        raise RuntimeError(
            "Não foi possível iniciar o Chrome/ChromeDriver. "
            "Instale o Google Chrome ou Chromium e um ChromeDriver compatível, "
            "ou defina as variáveis CHROME_BINARY_PATH e CHROMEDRIVER_PATH. "
            f"Caminho do navegador: {browser_path or 'não encontrado'}; "
            f"caminho do driver: {driver_path or 'não encontrado'}."
        ) from exc
