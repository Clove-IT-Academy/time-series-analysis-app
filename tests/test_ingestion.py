import io

import pytest
from openpyxl import Workbook

from forecasting_app.contracts import InputError
from forecasting_app.ingestion import list_sheets, read_upload


def workbook_bytes(formula=False):
    wb = Workbook()
    wb.active.title = "First"
    wb.active.append(["Date", "Sales"])
    wb.active.append(["2024-01-01", "=1+1" if formula else 12])
    wb.create_sheet("Other").append(["Other"])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def test_csv_and_header_identity():
    result = read_upload(b"Date,Sales\n2024-01-01,10\n", "data.csv")
    assert list(result.table) == ["Date", "Sales"]
    assert len(result.fingerprint) == 64


@pytest.mark.parametrize(
    "payload,name",
    [
        (b"a,a\n1,2", "a.csv"),
        (b"a,b\n1", "a.csv"),
        (b"", "a.csv"),
        (b"a\n1", "a.xls"),
        (b"junk", "a.xlsx"),
        (b"\xff", "a.csv"),
        (b"a,\n1,2", "a.csv"),
        (b"a,b\n", "a.csv"),
    ],
)
def test_invalid_input(payload, name):
    with pytest.raises(InputError):
        read_upload(payload, name)


def test_sheets_and_formulas():
    data = workbook_bytes()
    assert list_sheets(data, "book.xlsx") == ["First", "Other"]
    with pytest.raises(InputError, match="worksheet"):
        read_upload(data, "book.xlsx")
    assert read_upload(data, "book.xlsx", "First").table.iloc[0, 1] == 12
    with pytest.raises(InputError, match="Formula"):
        read_upload(workbook_bytes(True), "book.xlsx", "First")


def test_limits(monkeypatch):
    import forecasting_app.ingestion as ingestion

    monkeypatch.setattr(ingestion, "MAX_ROWS", 1)
    with pytest.raises(InputError):
        read_upload(b"a\n1\n2", "a.csv")
    monkeypatch.setattr(ingestion, "MAX_BYTES", 2)
    with pytest.raises(InputError):
        read_upload(b"a\n1", "a.csv")
