import json
import csv
import argparse
import os  # Импортирован для проверки существования и размера файла
from extractor import Entity_Relationships_Recognition


def process_kgx_json(json_data, nodes_filepath, edges_filepath):
    """
    Обрабатывает JSON-данные, извлекает узлы и ребра и дозаписывает их в TSV-файлы.

    :param json_data: Словарь, содержащий данные графа.
    :param nodes_filepath: Путь к выходному файлу для узлов (nodes.tsv).
    :param edges_filepath: Путь к выходному файлу для ребер (edges.tsv).
    """
    graph = json_data.get('graph', {})
    nodes = graph.get('nodes', [])
    edges = graph.get('edges', [])

    # --- Обработка и дозапись узлов в nodes.tsv ---

    node_headers = [
        'id', 'name', 'category', 'confidence_score', 'research_direction',
        'impact_score', 'source_type', 'maturity_level',
        'evidence_publication', 'explanation'
    ]

    # Проверяем, нужно ли записывать заголовок.
    # Записываем, только если файл не существует или пуст.
    write_node_header = not os.path.exists(nodes_filepath) or os.path.getsize(nodes_filepath) == 0

    with open(nodes_filepath, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=node_headers, delimiter='\t')
        if write_node_header:
            writer.writeheader()
        
        for node in nodes:
            additional_fields = node.get('additional_fields', {})
            evidence_pub = additional_fields.get('evidence_publication')
            # Преобразование списка публикаций в строку, разделенную '|'
            evidence_pub_str = '|'.join(evidence_pub) if isinstance(evidence_pub, list) else ''

            row = {
                'id': node.get('id'),
                'name': node.get('name'),
                'category': node.get('category'),
                'confidence_score': node.get('confidence_score'),
                'research_direction': additional_fields.get('research_direction'),
                'impact_score': additional_fields.get('impact_score'),
                'source_type': additional_fields.get('source_type'),
                'maturity_level': additional_fields.get('maturity_level'),
                'evidence_publication': evidence_pub_str,
                'explanation': additional_fields.get('explanation')
            }
            writer.writerow(row)
    
    print(f"Данные узлов успешно дозаписаны в {nodes_filepath}")

    # --- Обработка и дозапись ребер в edges.tsv ---

    edge_headers = [
        'subject', 'object', 'predicate', 'confidence_score', 
        'provided_by', 'evidence_publication'
    ]

    # Аналогичная проверка для файла ребер
    write_edge_header = not os.path.exists(edges_filepath) or os.path.getsize(edges_filepath) == 0
    
    with open(edges_filepath, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=edge_headers, delimiter='\t')
        if write_edge_header:
            writer.writeheader()

        for edge in edges:
            evidence_pub = edge.get('evidence_publication')
            # Преобразование списка публикаций в строку
            evidence_pub_str = '|'.join(evidence_pub) if isinstance(evidence_pub, list) else ''

            row = {
                'subject': edge.get('subject'),
                'object': edge.get('object'),
                'predicate': edge.get('predicate'),
                'confidence_score': edge.get('confidence_score'),
                'provided_by': edge.get('provided_by'),
                'evidence_publication': evidence_pub_str
            }
            writer.writerow(row)
            
    print(f"Данные ребер успешно дозаписаны в {edges_filepath}")


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
