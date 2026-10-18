import csv
import json
import logging
from datetime import datetime, timezone

from .errors import InvalidEventError, InvalidTimestampError

logger = logging.getLogger(__name__)


def detect_separator(header_line):
    """
    Определяет разделитель CSV-файла по строке заголовка.

    Args:
        header_line: Первая строка файла с названиями колонок.

    Returns:
        str: Найденный разделитель (";", "\t" или ",").
             Если ";" и "\t" отсутствуют, возвращает ",".
    """
    for separator in (";", "\t"):
        if separator in header_line:
            return separator
    return "," 

def parse_csv(path, skip_invalid=False):
    """
    Читает CSV-файл построчно и преобразует строки в события.

    Args:
        path: Путь к CSV-файлу.
        skip_invalid: Если True, пропускает некорректные записи.
                      Если False, вызывает исключение при ошибке.

    Yields:
        dict: Проверенное событие с полями timestamp, level,
              source и message.
        None: Если запись некорректна и skip_invalid=True.

    Raises:
        InvalidEventError: Если отсутствуют обязательные колонки
                           или запись некорректна при skip_invalid=False.
    """
    with open(path, encoding="utf-8-sig", newline="") as f:
        separator = detect_separator(f.readline())
        f.seek(0)
        reader = csv.reader(f, delimiter=separator)
        column_names = next(reader, None)
        if column_names is None:
            return #завершает генератор для пустого файла — событий будет ноль.
        required_fields = {"timestamp", "level", "source", "message"}
        if not required_fields.issubset(column_names):#проверяет, что все обязательные поля есть в заголовке. Дополнительные колонки допускаются.
            raise InvalidEventError(
                f"{path}, строка {reader.line_num}: "
                "в заголовке отсутствуют обязательные поля"
            )
        for values in reader:
            try:
                if len(values) != len(column_names):
                    raise InvalidEventError(
                        f"{path}, строка {reader.line_num}: пустая строка или неверное количество колонок"
                    )
                raw = dict(zip(column_names, values))
                yield make_event(raw, reader.line_num, path)
            except InvalidEventError as error:
                if skip_invalid:
                    logger.warning(str(error))
                    yield None
                else:
                    raise


def parse_jsonl(path, skip_invalid=False):
    """
    Читает JSONL-файл построчно и преобразует строки в события.

    Args:
        path: Путь к JSONL-файлу.
        skip_invalid: Если True, пропускает некорректные записи.
                      Если False, вызывает исключение при ошибке.

    Yields:
        dict: Проверенное событие с полями timestamp, level,
              source и message.
        None: Если запись некорректна и skip_invalid=True.

    Raises:
        InvalidEventError: Если строка пустая, содержит неверный JSON
                           или некорректные данные при skip_invalid=False.
    """
    with open(path, encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            try:
                if not line.strip():
                    raise InvalidEventError(
                        f"{path}, строка {line_number}: пустая строка"
                    )

                try:
                    raw = json.loads(line)
                except json.JSONDecodeError as e:
                    raise InvalidEventError(
                        f"{path}, строка {line_number}: неверный JSON"
                    ) from e

                yield make_event(raw, line_number, path)

            except InvalidEventError as error:
                if skip_invalid:
                    logger.warning(str(error))
                    yield None
                else:
                    raise
LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}

def make_event(raw, line_number, path):
    """
    Проверяет данные события и преобразует их в нужный формат.

    Args:
        raw: Словарь с исходными данными события.
        line_number: Номер строки в файле.
        path: Путь к файлу.

    Returns:
        dict: Проверенное событие с полями timestamp, level,
              source и message. Поле timestamp преобразуется
              в объект datetime.

    Raises:
        InvalidEventError: Если запись не является словарём,
                           уровень события неверный или поля
                           source и message некорректны.
        InvalidTimestampError: Если поле timestamp отсутствует,
                               пустое или содержит неверную дату.
    """
    where = f"{path}, строка {line_number}"
    if not isinstance(raw, dict):
        raise InvalidEventError(f"{where}: запись не является объектом")
    
    timestamp_raw = raw.get("timestamp")
    if not isinstance(timestamp_raw, str) or not timestamp_raw.strip():
        raise InvalidTimestampError(f"{where}: поле timestamp пустое или отсутствует")
    try:
        timestamp = datetime.fromisoformat(timestamp_raw)
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
    except ValueError as e:
        raise InvalidTimestampError(f"{where}: поле timestamp, неверная дата {timestamp_raw!r}") from e

    level = raw.get("level")
    if not isinstance(level, str) or level not in LEVELS :
        raise InvalidEventError(f"{where}: поле level неверное: {level!r}")

    source = raw.get("source")
    if not isinstance(source, str) or not source.strip():
        raise InvalidEventError(f"{where}: поле source отсутсвует или пустое")

    message = raw.get("message")
    if not isinstance(message, str):
        raise InvalidEventError(f"{where}: поле message отсутсвует")

    return {"timestamp": timestamp, "level": level, "source": source, "message": message}
    
