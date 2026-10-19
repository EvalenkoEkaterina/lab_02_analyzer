import json

from streamstats.report import result_report


def test_result_report(tmp_path):
    """Проверяет сохранение JSON-отчёта в файл."""
    file = tmp_path / "report.json"
    report = {"total_events": 5}
    result_report(report, file)
    with open(file, encoding="utf-8") as f:
        saved = json.load(f)
    assert saved == report

def test_result_report2(tmp_path):
    """Проверяет сохранение кириллицы в JSON-отчёте."""
    file = tmp_path / "report.json"
    report = {
        "total_events": 2,
        "sources": {"сервис": 2}
    }
    result_report(report, file)
    saved = json.loads(file.read_text(encoding="utf-8"))
    assert saved == report