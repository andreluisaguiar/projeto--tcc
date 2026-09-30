from src.scraping.sigaa_scraper import _mensagem_alerta_sigaa


def test_mensagem_alerta_botao_voltar_orienta_url_completa():
    mensagem = _mensagem_alerta_sigaa(
        "Você utilizou o botão voltar do navegador, o que não é recomendado."
    )

    assert "URL completa" in mensagem
    assert "id=..." in mensagem


def test_mensagem_alerta_generico_preserva_texto():
    mensagem = _mensagem_alerta_sigaa("Informe ao menos um critério de busca.")

    assert "Informe ao menos um critério de busca." in mensagem
