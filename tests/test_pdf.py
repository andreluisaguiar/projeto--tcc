from src.utils.pdf_generator import gerar_relatorio_pdf


def test_gerar_relatorio_pdf():
    pdf = gerar_relatorio_pdf(
        estatisticas={
            "resumo": {"média de publicações": 12, "orientadores ativos": 5},
            "por_engenharia": {"Engenharia Elétrica": 8},
            "por_ano": {"2024": 4},
        },
        outliers_detectados=2,
        total_tccs=20,
    )

    assert isinstance(pdf, (bytes, bytearray))
    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 1000