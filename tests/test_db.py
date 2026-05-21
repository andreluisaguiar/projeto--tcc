import pandas as pd

import src.utils.db as db_module


def test_sqlite_import_leitura_e_limpeza(tmp_path, monkeypatch):
    db_path = tmp_path / "raw_tccs.db"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)

    df = pd.DataFrame(
        {
            "Titulo": ["Projeto A", "Projeto A", "Projeto B"],
            "Engenharia": ["Engenharia Elétrica", "Engenharia Elétrica", "Engenharia Mecânica"],
            "Orientador": ["Ana", "Ana", "Bruno"],
            "Ano": ["2024", "2024", "2023"],
        }
    )

    inseridos, ignorados = db_module.salvar_dataframe_tccs(df)
    assert inseridos == 2
    assert ignorados == 1

    dados = db_module.obter_todos_tccs()
    assert len(dados) == 2
    assert set(dados["titulo"]) == {"Projeto A", "Projeto B"}

    removidos = db_module.limpar_banco()
    assert removidos == 2
    assert db_module.obter_todos_tccs().empty