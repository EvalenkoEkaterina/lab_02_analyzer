import json
import sys
from pathlib import Path

from .analysis import analyze
from .errors import CLIConfigError, StreamStatsError
from .report import result_report


def run():
    """
    Обрабатывает аргументы командной строки и запускает анализ файлов.

    Считывает аргументы, проверяет их корректность, запускает анализ
    CSV или JSONL и выводит отчёт в терминал или сохраняет в файл.

    Поддерживаемые параметры:
        --help: Вывод справки о программе.
        --format: Формат входных файлов ("csv" или "jsonl").
        --output: Путь для сохранения JSON-отчёта.
        --skip-invalid: Пропуск некорректных записей.

    Raises:
        CLIConfigError: Если команда или параметры указаны неверно,
                        отсутствуют входные файлы или путь отчёта
                        совпадает с путём входного файла.
        UnsupportedFormatError: Если указан неподдерживаемый формат.
        InvalidEventError: Если обнаружена некорректная запись
                           при skip_invalid=False.
        InvalidTimestampError: Если дата события некорректна
                               при skip_invalid=False.
        OSError: Если произошла ошибка при работе с файлами.
    """
    args = sys.argv[1:]

    if args == ["--help"] or args == ["analyze", "--help"]:
        print(
    "streamstats — анализатор событий из CSV и JSONL.\n"
    "\n"
    "Пример запуска:\n"
    "  python -m streamstats analyze data/events_valid.csv --format csv\n"
    "\n"
    "После analyze укажи один или несколько файлов через пробел.\n"
    "\n"
    "Параметры:\n"
    "  --format csv или --format jsonl — обязательный формат входных файлов.\n"
    "  --output report.json — сохранить отчёт в указанный файл.\n"
    "  --skip-invalid — пропускать неверные записи и выводить предупреждения.\n"
    "\n"
    "Без --output отчёт выводится в терминал.\n"
    "Без --skip-invalid программа останавливается на первой неверной записи."
    )
        return

    if not args:
        raise CLIConfigError("Укажи команду analyze")
    if args[0] != "analyze":
        raise CLIConfigError(f"Неизвестная команда: {args[0]}")

    args = args[1:]
    paths = []
    file_format = None
    skip_invalid = False
    output_path = None

    while args:
        
        arg = args.pop(0)

        if arg == "--format":
            if not args or args[0].startswith("-"):
                raise CLIConfigError("После --format нужно указать формат")
            file_format = args.pop(0)
        elif arg == "--skip-invalid":
            skip_invalid = True
        elif arg == "--output":
            if not args or args[0].startswith("-"):
                raise CLIConfigError("После --output нужно указать путь")
            output_path = args.pop(0)
        elif arg.startswith("-"):
            raise CLIConfigError(f"Неизвестный параметр: {arg}")
        else:
            paths.append(arg)

    if not paths:
        raise CLIConfigError("Укажи хотя бы один файл")
    if file_format is None:
        raise CLIConfigError("Укажи --format csv или jsonl")

    
    report = analyze(paths, file_format, skip_invalid)
    if output_path is not None:
        report_path = Path(output_path).resolve()
        for path in paths:
            input_path = Path(path).resolve() # resolve() получает полный путь, чтобы сравнить, ведут ли пути к одному файлу.
            if report_path == input_path:
                raise CLIConfigError(
                    "Нельзя сохранять отчёт поверх входного файла"
                )

    if output_path is not None:
        result_report(report, output_path)
    else:
        print(json.dumps(report, ensure_ascii=False, indent=4))

def main():
    """
    Запускает программу и обрабатывает возникающие ошибки.

    Вызывает функцию run() и перехватывает исключения,
    выводя сообщения об ошибках в stderr.

    Raises:
        SystemExit: Завершает программу с кодом 2 при возникновении
                    StreamStatsError или OSError.
    """
    try:
        run()
    except StreamStatsError as error:
        print(str(error), file=sys.stderr)
        sys.exit(2)
    except OSError as error:
        print(f"Ошибка работы с файлом: {error}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()