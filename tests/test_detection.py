import pandas as pd

from forecasting_app.detection import detect_columns, requires_confirmation


def test_rank_and_ambiguity():
    table = pd.DataFrame(
        {
            "Invoice Date": ["2024-01-01", "2024-02-01"],
            "Sales": [12, 14],
            "Purchases": [5, 8],
            "ID": [1234, 5678],
        }
    )
    candidates = detect_columns(table)
    assert candidates["date"][0].column_name == "Invoice Date"
    assert candidates["sales"][0].column_name == "Sales"
    assert candidates["purchases"][0].column_name == "Purchases"
    assert not requires_confirmation(candidates["sales"])
    assert next(c for c in candidates["date"] if c.column_name == "ID").confidence == 0
    ambiguous = detect_columns(pd.DataFrame({"Amount": [3, 5], "Value": [4, 6]}))
    assert requires_confirmation(ambiguous["sales"])
    assert ambiguous["sales"][0].evidence
