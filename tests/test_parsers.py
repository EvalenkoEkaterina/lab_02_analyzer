import pytest

from streamstats.errors import InvalidEventError, InvalidTimestampError
from streamstats.parsers import detect_separator, make_event, parse_csv, parse_jsonl


#положительный тест для make_event level
def test_make_event_valid_level():
    raw = {"timestamp": "2026-09-06T13:13:00",
        "level": "DEBUG",
        "source": "db",
        "message": "Started"}
    event = make_event(raw, 1, "events.csv")
    assert event["level"] == "DEBUG"

#отрицательный тест для make_event 
def test_make_event_invalid_level():
    raw = {"timestamp": "2026-10-06T11:08:00",
        "level": "ERRROR",
        "source": "api",
        "message": "Started"
    }
    with pytest.raises(InvalidEventError):
        make_event(raw, 1, "events.jsonl")

#положительный тест для make_event timestamp
def test_make_event_valid_timestamp():
    raw = {
        "timestamp": "2024-01-06T11:01:00",
        "level": "INFO",
        "source": "auth",
        "message": "Started"
    }
    event = make_event(raw, 1, "events.csv")
    assert event["timestamp"].isoformat() == "2024-01-06T11:01:00+00:00"

#отрицательные тесты для timestamp make_event
def test_invalid_timestamp():
    raw = { "timestamp": "2016-99-56",
        "level": "ERROR",
        "source": "worker",
        "message": "Задача выполнена"}
    with pytest.raises(InvalidTimestampError):
        make_event(raw, 1, "events.csv")

def test_empty_timestamp():
    raw = {"timestamp": "",
        "level": "WARNING",
        "source": "payment",
        "message": "Request received"

    }
    with pytest.raises(InvalidTimestampError):
        make_event(raw, 1, "events.csv")

def test_missing_timestamp():
    raw = {
        "level": "DEBUG",
        "source": "db",
        "message": "Started"
    }
    with pytest.raises(InvalidTimestampError):
        make_event(raw, 1, "events.jsonl")

#положительный тест для make_event source
def test_valid_source():
    raw = {
        "timestamp": "2021-12-06T07:15:00",
        "level": "CRITICAL",
        "source": "api",
        "message": "Задача выполнена"
    }
    event = make_event(raw, 1, "events.jsonl")
    assert event["source"] == "api"

#отрицательные тесты для make_event source
def test_empty_source():
    raw = {
        "timestamp": "2014-04-05T04:01:00",
        "level": "WARNING",
        "source": "",
        "message": "Cache miss"
    }
    with pytest.raises(InvalidEventError):
        make_event(raw, 1, "events.csv")

def test_spaces_source():
    raw = {
        "timestamp": "2001-05-01T01:09:15",
        "level": "INFO",
        "source": "   ",
        "message": "User logged in"
    }

    with pytest.raises(InvalidEventError):
        make_event(raw, 1, "events.jsonl")      

#положительные тесты для message
def test_valid_message():
    raw = {
        "timestamp": "2023-11-09T04:08:27",
        "level": "ERROR",
        "source": "db",
        "message": "Database connected"
    }
    event = make_event(raw, 1, "events.csv")
    assert event["message"] == "Database connected"

def test_empty_message():
    raw = {
        "timestamp": "2012-08-07T08:02:22",
        "level": "INFO",
        "source": "server",
        "message": ""
    }
    event = make_event(raw, 1, "events.jsonl")
    assert event["message"] == ""

#отрицательные тсеты для message 
def test_invalid_message():
    raw = {
        "timestamp": "2011-09-02T05:07:12",
        "level": "DEBUG",
        "source": "db",
        "message": 124
    }
    with pytest.raises(InvalidEventError):
        make_event(raw, 1, "events.jsonl")

def test_missing_message():
    raw = {
        "timestamp": "2022-05-09T10:17:00",
        "level": "INFO",
        "source": "cache"
    }
    with pytest.raises(InvalidEventError):
        make_event(raw, 1, "events.csv")

#отрицательные тесты дл передачи словаря в make_event
def test_make_event_invalid_raw_list():
    raw = ["2025-10-12", "INFO", "db", "Задача выполнена"]
    with pytest.raises(InvalidEventError):
        make_event(raw, 1, "events.jsonl")

def test_make_event_invalid_raw_number():
    raw = 215
    with pytest.raises(InvalidEventError):
        make_event(raw, 2, "events.csv")

def test_make_event_invalid_raw_none():
    raw = None
    with pytest.raises(InvalidEventError):
        make_event(raw, 3, "events.csv")


#положительный тест для detect_separator
def test_detect_separator_semicolon():
    header = "timestamp;level;source;message"
    assert detect_separator(header) == ";"

#отрицательный тест для detect_separator
def test_detect_separator_invalid():
    header = "timestamp|level|source|message"
    assert detect_separator(header) == ","

def test_parse_csv_valid(tmp_path):
    file = tmp_path / "events.csv"
    file.write_text(
        "timestamp,level,source,message\n"
        "2023-10-07T10:09:15,INFO,api,Started\n"
    )
    event = next(parse_csv(file))
    assert event["level"] == "INFO"

#положительныq тест parse_csv
def test_parse_csv_invalid(tmp_path):
    file = tmp_path / "events.csv"
    file.write_text(
        "timestamp,level,source\n"
        "2022-12-07T00:06:55,ERROR,db\n"
    )
    with pytest.raises(InvalidEventError):
        list(parse_csv(file))

#отрицательные тесты parse_csv
def test_parse_csv_invalid_level(tmp_path):
    file = tmp_path / "events.csv"
    file.write_text(
        "timestamp,level,source,message\n"
        "2023-10-07T10:09:15,INFO,api,Started\n"
        "2023-10-07T10:10:15,BYE,db,Error\n"
    )
    with pytest.raises(InvalidEventError):
        list(parse_csv(file))

def test_parse_csv_skip_invalid(tmp_path):
    file = tmp_path / "events.csv"
    file.write_text(
        "timestamp,level,source,message\n"
        "2013-12-07T10:09:34,INFO,api,Started\n"
        "2025-10-01T10:10:27,HELLO,db,Error\n"
        "2017-11-08T10:11:15,WARNING,api,Slow\n"
    )
    events = list(parse_csv(file, skip_invalid=True))
    assert len(events) == 3
    assert events[0]["level"] == "INFO"
    assert events[1] is None
    assert events[2]["level"] == "WARNING"


def test_parse_jsonl_valid(tmp_path):
    file = tmp_path / "events.jsonl"
    file.write_text(
        '{"timestamp":"2014-07-07T12:09:19","level":"WARNING","source":"payment","message":"Запуск"}\n'
    )
    event = next(parse_jsonl(file))
    assert event["level"] == "WARNING"
    assert event["source"] == "payment"

def test_parse_jsonl_invalid(tmp_path):
    file = tmp_path / "events.jsonl"
    file.write_text(
        '{"timestamp":"2018-02-09T14:07:19","level":"CRITICAL","source":"api","message":"Started",}\n'
    )
    with pytest.raises(InvalidEventError):
        next(parse_jsonl(file))

def test_parse_jsonl_skip_invalid(tmp_path):
    file = tmp_path / "events.jsonl"
    file.write_text(
        '{"timestamp":"2023-05-12T08:15:00","level":"INFO","source":"api","message":"Started"}\n'
        '{"timestamp":"2024-11-20T14:30:00","level":"ERROR","source":"payments","message":"Failed",}\n'
        '{"timestamp":"2025-06-07T20:45:00","level":"CRITICAL","source":"database","message":"Connection lost"}\n'
    )
    events = list(parse_jsonl(file, skip_invalid=True))
    assert events[1] is None
    assert events[2]["level"] == "CRITICAL"
    assert events[2]["source"] == "database"