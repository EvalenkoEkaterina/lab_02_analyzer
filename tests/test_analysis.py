from streamstats.analysis import add_event, cr_stats, get_report
from streamstats.parsers import datetime


def test_cr_stats_independent():
    """Проверяет независимость объектов статистики."""
    stats1 = cr_stats()
    stats2 = cr_stats()
    stats1["levels"]["ERROR"] += 1
    assert stats1["levels"]["ERROR"] == 1
    assert stats2["levels"] == {}

def test_add_event_not_error():
    """Проверяет учёт события без ошибки."""
    stats = cr_stats()
    event = {
        "timestamp": datetime.fromisoformat("2024-08-12T09:30:00+00:00"),
        "level": "INFO",
        "source": "api",
        "message": "Server started"
    }
    add_event(stats, event)
    assert stats["total_events"] == 1
    assert stats["errors_sources"]["api"] == 0

def test_add_event_timestamps():
    """Проверяет определение самого раннего и позднего времени."""
    stats = cr_stats()
    event1 = {
        "timestamp": datetime.fromisoformat("2025-06-10T15:00:00+00:00"),
        "level": "ERROR",
        "source": "database",
        "message": "Connection lost"
    }
    event2 = {
        "timestamp": datetime.fromisoformat("2023-03-05T09:00:00+00:00"),
        "level": "WARNING",
        "source": "api",
        "message": "Slow response"
    }
    add_event(stats, event1)
    add_event(stats, event2)
    assert stats["first_timestamp"] == event2["timestamp"]
    assert stats["last_timestamp"] == event1["timestamp"]


def test_get_report_valid():
    """Проверяет формирование отчёта по корректному событию."""
    stats = cr_stats()
    event = {
         "timestamp": datetime.fromisoformat("2024-08-12T09:30:00+00:00"),
        "level": "INFO",
        "source": "api",
        "message": "Server started"
    }
    add_event(stats, event)
    report = get_report(stats)
    assert report["total_events"] == 1
    assert report["levels"] == {"INFO":1}
    assert report["sources"] == {"api": 1}
    assert report["top_errors"] == []
    assert report["first_timestamp"] == "2024-08-12T09:30:00+00:00"


def test_get_report_top_errors():
    """Проверяет сортировку источников по количеству ошибок."""
    stats = cr_stats()
    stats["errors_sources"]["database"] = 3
    stats["errors_sources"]["payments"] = 2
    stats["errors_sources"]["api"] = 2
    report = get_report(stats)
    assert report["top_errors"] == [
        {"source": "database", "count": 3},
        {"source": "api", "count": 2},
        {"source": "payments", "count": 2}
    ]

def test_get_report_top_five():
    """Проверяет ограничение рейтинга пятью источниками."""
    stats = cr_stats()
    stats["errors_sources"].update({
        "database": 6,
        "auth": 5,
        "payments": 4,
        "cache": 3,
        "search": 2,
        "api": 1
    })
    report = get_report(stats)
    assert len(report["top_errors"]) == 5
    assert report["top_errors"][0]["source"] == "database"
    assert report["top_errors"][-1]["source"] == "search"


from streamstats.analysis import analyze


def test_analyze_full(tmp_path):
    """Проверяет объединение двух CSV с пропуском неверной записи."""
    file1 = tmp_path / "first.csv"
    file2 = tmp_path / "second.csv"

    file1.write_text(
        "timestamp,level,source,message\n"
        "2024-03-10T10:00:00,INFO,api,Started\n"
        "2025-07-04T12:00:00,ERROR,database,Failed\n"
        "2024-06-06T12:00:00,HELLO,auth,Bad level\n"
    )
    file2.write_text(
        "timestamp,level,source,message\n"
        "2023-01-05T08:00:00,CRITICAL,payments,Payment failed\n"
        "2026-02-09T15:30:00,ERROR,database,Connection lost\n"
        "2025-02-01T12:00:00,WARNING,api,Slow response\n"
    )

    report = analyze([file1, file2], "csv", skip_invalid=True)

    assert report["total_events"] == 5
    assert report["skipped_events"] == 1
    assert report["levels"] == {
        "INFO": 1,
        "ERROR": 2,
        "CRITICAL": 1,
        "WARNING": 1
    }
    assert report["sources"] == {
        "api": 2,
        "database": 2,
        "payments": 1
    }
    assert report["top_errors"] == [
        {"source": "database", "count": 2},
        {"source": "payments", "count": 1}
    ]
    assert report["first_timestamp"] == "2023-01-05T08:00:00+00:00"
    assert report["last_timestamp"] == "2026-02-09T15:30:00+00:00"

def test_analyze_empty_csv(tmp_path):
    """Проверяет обработку пустого CSV-файла."""
    file = tmp_path / "empty.csv"
    file.write_text("", encoding="utf-8")

    report = analyze([file], "csv")

    assert report["total_events"] == 0
    assert report["skipped_events"] == 0
    assert report["levels"] == {}
    assert report["sources"] == {}
    assert report["top_errors"] == []
    assert report["first_timestamp"] is None
    assert report["last_timestamp"] is None


def test_analyze_empty_jsonl(tmp_path):
    """Проверяет обработку пустого JSONL-файла."""
    file = tmp_path / "empty.jsonl"
    file.write_text("", encoding="utf-8")

    report = analyze([file], "jsonl")

    assert report["total_events"] == 0
    assert report["skipped_events"] == 0
    assert report["levels"] == {}
    assert report["sources"] == {}
    assert report["top_errors"] == []
    assert report["first_timestamp"] is None
    assert report["last_timestamp"] is None