"""Geração de relatórios PDF em formato acadêmico."""

from __future__ import annotations

from pathlib import Path

from fpdf import FPDF


def _localizar_fonte_unicode() -> str | None:
    candidatos = [
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed.ttf"),
        Path("/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"),
    ]
    for candidato in candidatos:
        if candidato.exists():
            return str(candidato)
    return None


class RelatorioPDF(FPDF):
    def header(self) -> None:
        self.set_font(self.font_family_name, "B", 14)
        self.set_text_color(25, 25, 25)
        self.cell(0, 8, "Relatório Consolidado do Projeto TCC", ln=True, align="C")
        self.set_font(self.font_family_name, "", 9)
        self.set_text_color(90, 90, 90)
        self.cell(0, 6, "Resumo executivo, estatísticas e consolidação dos dados", ln=True, align="C")
        self.ln(2)

    def footer(self) -> None:
        self.set_y(-15)
        self.set_font(self.font_family_name, "I", 8)
        self.set_text_color(110, 110, 110)
        self.cell(0, 8, f"Página {self.page_no()}", align="C")


def _escrever_linha(pdf: RelatorioPDF, rotulo: str, valor: str) -> None:
    pdf.set_font(pdf.font_family_name, "B", 10)
    pdf.cell(45, 8, f"{rotulo}:", border=0)
    pdf.set_font(pdf.font_family_name, "", 10)
    pdf.cell(0, 8, valor, ln=True)


def _preparar_pdf() -> RelatorioPDF:
    pdf = RelatorioPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    fonte_unicode = _localizar_fonte_unicode()
    if fonte_unicode:
        pdf.add_font("DejaVu", "", fonte_unicode)
        pdf.add_font("DejaVu", "B", fonte_unicode)
        pdf.add_font("DejaVu", "I", fonte_unicode)
        pdf.add_font("DejaVu", "BI", fonte_unicode)
        pdf.font_family_name = "DejaVu"
    else:
        pdf.font_family_name = "Helvetica"
    pdf.set_font(pdf.font_family_name, "", 10)
    pdf.add_page()
    return pdf


def gerar_relatorio_pdf(
    estatisticas: dict,
    outliers_detectados: int,
    total_tccs: int,
) -> bytes:
    """Gera um PDF binário com o resumo consolidado do projeto."""
    pdf = _preparar_pdf()

    resumo = estatisticas.get("resumo", {}) if isinstance(estatisticas, dict) else {}
    distribuicao_engenharia = estatisticas.get("por_engenharia", {}) if isinstance(estatisticas, dict) else {}
    distribuicao_ano = estatisticas.get("por_ano", {}) if isinstance(estatisticas, dict) else {}
    top_orientadores = estatisticas.get("top_orientadores", {}) if isinstance(estatisticas, dict) else {}

    pdf.set_font(pdf.font_family_name, "B", 12)
    pdf.cell(0, 8, "1. Visão Geral", ln=True)
    pdf.set_font(pdf.font_family_name, "", 10)
    pdf.ln(1)
    _escrever_linha(pdf, "Total de TCCs", str(total_tccs))
    _escrever_linha(pdf, "Outliers detectados", str(outliers_detectados))

    for chave, valor in resumo.items():
        _escrever_linha(pdf, str(chave).replace("_", " ").title(), str(valor))

    def escrever_secao_tabela(titulo: str, dados: dict) -> None:
        if not dados:
            return
        pdf.ln(2)
        pdf.set_font(pdf.font_family_name, "B", 12)
        pdf.cell(0, 8, titulo, ln=True)
        pdf.set_font(pdf.font_family_name, "", 10)
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(120, 8, "Categoria", border=1, fill=True)
        pdf.cell(0, 8, "Quantidade", border=1, fill=True, ln=True)
        for categoria, quantidade in list(dados.items())[:15]:
            pdf.cell(120, 8, str(categoria), border=1)
            pdf.cell(0, 8, str(quantidade), border=1, ln=True)

    escrever_secao_tabela("2. Distribuição por Engenharia", distribuicao_engenharia)
    escrever_secao_tabela("3. Distribuição por Ano", distribuicao_ano)
    escrever_secao_tabela("4. Top Orientadores", top_orientadores)

    conteudo = pdf.output(dest="S")
    if isinstance(conteudo, str):
        return conteudo.encode("latin-1")
    return bytes(conteudo)