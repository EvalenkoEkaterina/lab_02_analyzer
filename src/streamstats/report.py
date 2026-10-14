import json 
def result_report(report, output_path):
    """
    Сохраняет итоговый отчёт в JSON-файл.

    Args:
        report: Словарь с результатами анализа событий.
        output_path: Путь к файлу для сохранения отчёта.

    Raises:
        OSError: Если произошла ошибка при создании
                 или записи файла.
    """
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(
    report,
    f,
    ensure_ascii=False,
    indent=4
    )