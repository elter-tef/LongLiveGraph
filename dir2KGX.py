import json

import argparse
from extractor import Entity_Relationships_Recognition, process_kgx_json



def main():
    """
    Главная функция для парсинга аргументов и запуска обработки.
    """
    parser = argparse.ArgumentParser(
        description="Извлекает сущности и отношения из текстовой статьи и дозаписывает их в TSV-файлы формата KGX."
    )
    # Позиционный аргумент для входного файла
    parser.add_argument(
        'input_file',
        type=str,
        help='Путь к входному текстовому файлу (статье).'
    )
    # Опциональные аргументы для выходных файлов
    parser.add_argument(
        '--nodes-file', 
        type=str, 
        default='nodes.tsv',
        help='Имя выходного файла для узлов (по умолчанию: nodes.tsv)'
    )
    parser.add_argument(
        '--edges-file', 
        type=str, 
        default='edges.tsv',
        help='Имя выходного файла для ребер (по умолчанию: edges.tsv)'
    )
    args = parser.parse_args()

    # Чтение текста статьи из файла, указанного в аргументах
    try:
        with open(args.input_file, 'r', encoding='utf-8') as file:
            article_text = file.read() 
    except FileNotFoundError:
        print(f"Ошибка: Входной файл не найден по пути '{args.input_file}'")
        return # Прекращаем выполнение, если файл не найден

    # Основной блок обработки
    try:
        # 1. Извлечение данных из текста
        kgx_data = Entity_Relationships_Recognition(article_text=article_text)
        
        # 2. Обработка и сохранение данных в TSV
        process_kgx_json(kgx_data, args.nodes_file, args.edges_file)

    except json.JSONDecodeError:
        print("Ошибка: Неверный формат JSON получен от модуля распознавания.")
    except Exception as e:
        print(f"Произошла непредвиденная ошибка: {e}")


if __name__ == '__main__':
    main()
