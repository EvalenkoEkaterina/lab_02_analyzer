from collections import Counter

from .errors import UnsupportedFormatError
from .parsers import parse_csv, parse_jsonl


def cr_stats():
    return {
        "total_events": 0,
        "levels": Counter(),
        "sources": Counter(),
        "errors_sources": Counter(),
        "first_timestamp": None,
        "last_timestamp": None,
        "skipped_events":0,
    }

def add_event(stats, event):
    """
    Добавляет событие в общую статистику.
    Args:
        stats: Словарь с накопленной статистикой событий.
        event: Словарь с данными проверенного события
    Обновляет:
        total_events: Общее количество обработанных событий.
        levels: Количество событий каждого уровня.
        sources: Количество событий по источникам.
        errors_sources: Количество ошибок ERROR и CRITICAL
                        по источникам.
        first_timestamp: Время самого раннего события.
        last_timestamp: Время самого позднего события.
    """
    stats["total_events"] += 1

    stats["levels"][event["level"]] += 1
    stats["sources"][event["source"]] += 1

    if event["level"] in ("ERROR", "CRITICAL"):
        stats["errors_sources"][event["source"]] += 1

    timestamp = event["timestamp"]

    if stats["first_timestamp"] is None:
        stats["first_timestamp"] = timestamp
        stats["last_timestamp"] = timestamp

    stats["first_timestamp"] = min(stats["first_timestamp"], timestamp)
    stats["last_timestamp"] = max(stats["last_timestamp"], timestamp)

def get_report(stats):
    """
    Формирует итоговый отчёт на основе собранной статистики.
    Args:
        stats: Словарь с накопленной статистикой событий.
    Returns:
        dict: Отчёт, содержащий:
            skipped_events: Количество пропущенных записей.
            total_events: Общее количество обработанных событий.
            levels: Количество событий по уровням.
            sources: Количество событий по источникам.
            top_errors: Топ-5 источников с наибольшим количеством
                        ошибок ERROR и CRITICAL.
            first_timestamp: Время самого раннего события.
            last_timestamp: Время самого позднего события.

    """
    top_errors = list(stats["errors_sources"].items())
    top_errors.sort(key=lambda x: x[0])
    top_errors.sort(key=lambda x: x[1], reverse=True)
    top_errors = top_errors[:5]

    return {
        "skipped_events": stats["skipped_events"],
        "total_events": stats["total_events"],
        "levels": dict(stats["levels"]),
        "sources": dict(stats["sources"]),
        "top_errors": [
            {"source": source, "count": count}
            for source, count in top_errors
        ],
        "first_timestamp": (
            stats["first_timestamp"].isoformat()
            if stats["first_timestamp"] is not None
            else None
        ),
        "last_timestamp": (
            stats["last_timestamp"].isoformat()
            if stats["last_timestamp"] is not None
            else None
        ),
    }

def analyze(paths, file_format, skip_invalid=False):
    """
    Анализирует файлы CSV или JSONL и собирает статистику событий.
    Args:
        paths: Список путей к файлам для анализа.
        file_format: Формат входных файлов ("csv" или "jsonl").
        skip_invalid: Если True, пропускает некорректные записи.
                      Если False, вызывает исключение при ошибке.
    Returns:
        dict: Итоговый отчёт с количеством событий, распределением
              по уровням и источникам, топ-5 источников ошибок,
              временным диапазоном и числом пропущенных записей.
    Raises:
        UnsupportedFormatError: Если указан неподдерживаемый формат файла.
        InvalidEventError: Если обнаружена некорректная запись
                           при skip_invalid=False.
        InvalidTimestampError: Если дата события некорректна
                               при skip_invalid=False.
    """
    if file_format == "csv":
        parser = parse_csv
    elif file_format == "jsonl":
        parser = parse_jsonl
    else:
        raise UnsupportedFormatError(f"Неподдерживаемый формат: {file_format}")

    stats = cr_stats()

    for path in paths:
        for event in parser(path, skip_invalid=skip_invalid):
            if event is None:
                stats["skipped_events"] += 1
            else:
                add_event(stats, event)
    return get_report(stats)

