import json
import subprocess
import sys


def test_cli_csv(tmp_path):
    file = tmp_path / "events.csv"
    file.write_text(
        "timestamp,level,source,message\n"
        "2023-05-12T08:15:00,INFO,api,Started\n"
    )
    result = subprocess.run(
        [sys.executable, '-m', 'streamstats', 'analyze', str(file), '--format', 'csv'],
        capture_output=True,
        text=True,
        check=False
    )
    assert result.returncode == 0

def test_cli_output(tmp_path):
    file = tmp_path / "events.csv"
    output = tmp_path / "result.json"
    file.write_text(
        "timestamp,level,source,message\n"
        "2024-04-15T10:00:00,INFO,server,Started\n"
        "2024-04-15T11:00:00,ERROR,database,Connection failed\n"
    )
    result = subprocess.run(
        [sys.executable, '-m', 'streamstats', 'analyze', str(file), '--format', 'csv', '--output', str(output)],
        capture_output=True,
        text=True,
        check=False
    )
    assert output.exists() == True
    data = json.loads(output.read_text(encoding="utf-8"))
    assert result.returncode == 0
    assert data["total_events"]== 2

def test_cli_output_json_skip_invalid(tmp_path):
    file = tmp_path / "events.json"
    output = tmp_path / "result.json"
    file.write_text(
        '{"timestamp":"2024-04-15T10:00:00","level":"INFO","source":"server","message":"Started"}\n'
        '{"timestamp":"2024-04-15T11:00:00","level":"HELLO","source":"database","message":"Connection failed"}\n'
        '{"timestamp":"2024-04-15T11:00:00","level":"ERROR","source":"database","message":"Connection failed"}\n',
        encoding="utf-8"
    )
    result = subprocess.run(
        [sys.executable, '-m', 'streamstats', 'analyze', str(file), '--format', 'jsonl', '--output', str(output), '--skip-invalid'],
        capture_output=True,
        text=True,
        check=False
    )
    assert result.returncode == 0
    assert output.exists()
    data = json.loads(output.read_text(encoding="utf-8"))
    assert data["total_events"] == 2
    assert data["skipped_events"] == 1


def test_cli_without_skip_invalid(tmp_path):
    file = tmp_path / "events.jsonl"
    output = tmp_path / "result.json"
    file.write_text(
        '{"timestamp":"2024-04-15T10:00:00","level":"INFO","source":"server","message":"Started"}\n'
        '{"timestamp":"2024-04-15T11:00:00","level":"HELLO","source":"database","message":"Connection failed"}\n'
        '{"timestamp":"2024-04-15T11:00:00","level":"ERROR","source":"database","message":"Connection failed"}\n',
        encoding="utf-8"
    )
    result = subprocess.run(
        [sys.executable, '-m', 'streamstats', 'analyze', str(file), '--format', 'jsonl', '--output', str(output)],
        capture_output=True,
        text=True,
        check=False
    )
    assert result.returncode == 2
    assert "level" in result.stderr  
    assert "строка 2" in result.stderr

def test_cli_without_format(tmp_path):
    file = tmp_path / "events.csv"
    file.write_text(
        "timestamp,level,source,message\n"
        "2024-04-15T10:00:00,INFO,server,Started\n"
        "2024-04-15T11:00:00,ERROR,database,Connection failed\n"
    )
    result = subprocess.run(
        [sys.executable, '-m', 'streamstats', 'analyze', str(file), '--format'],
        capture_output=True,
        text=True,
        check=False
    )
    assert result.returncode == 2
    assert 'format' in result.stderr


def test_cli_same_input_output(tmp_path):
    file = tmp_path / "events.csv"
    output = tmp_path / "events.csv"
    file.write_text(
            "timestamp,level,source,message\n"
            "2025-11-15T10:40:50,CRITICAL,server,Started\n"
            "2025-07-05T11:20:00,ERROR,database,Connection failed\n"
        )
    result = subprocess.run(
        [sys.executable, '-m', 'streamstats', 'analyze', str(file), '--format', 'csv', '--output', str(output)],
        capture_output=True,
        text=True,
        check=False
    )
    original = file.read_text(encoding="utf-8")
    assert result.returncode == 2
    assert "Нельзя сохранять отчёт поверх входного файла" in result.stderr
    assert file.read_text(encoding="utf-8") == original

def test_cli_missing_file(tmp_path):
    result = subprocess.run(
        [sys.executable, '-m', 'streamstats', 'analyze', 'missing.json', '--format', 'jsonl'],
        capture_output=True,
        text=True,
        check=False
    )
    assert result.returncode == 2
    assert "Ошибка работы с файлом" in result.stderr

def test_cli_invalid_json_line3(tmp_path):
    file = tmp_path / "events.jsonl"
    file.write_text(
        '{"timestamp":"2024-04-15T10:00:00","level":"INFO","source":"server","message":"Started"}\n'
        '{"timestamp":"2024-04-15T11:00:00","level":"INFO","source":"database","message":"Connection failed"}\n'
        '{"timestamp":"2024-04-15T11:00:00","level":"ERROR","source":"db","message":"Задача выполнена"},',
        encoding="utf-8"
    )
    result = subprocess.run(
            [sys.executable, '-m', 'streamstats', 'analyze', str(file), '--format', 'jsonl'],
            capture_output=True,
            text=True,
            check=False
    )
    assert result.returncode == 2
    assert 'неверный JSON' in result.stderr
    assert '3' in result.stderr
