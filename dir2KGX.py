import json
import csv
import argparse
from extractor import Entity_Relationships_Recognition

def process_kgx_json(json_data, nodes_filepath, edges_filepath):
    """
    Обрабатывает JSON-данные, извлекает узлы и ребра и записывает их в TSV-файлы.

    :param json_data: Словарь, содержащий данные графа.
    :param nodes_filepath: Путь к выходному файлу для узлов (nodes.tsv).
    :param edges_filepath: Путь к выходному файлу для ребер (edges.tsv).
    """
    graph = json_data.get('graph', {})
    nodes = graph.get('nodes', [])
    edges = graph.get('edges', [])

    # Определение заголовков для nodes.tsv в соответствии с требованиями
    node_headers = [
        'id', 'name', 'category', 'confidence_score', 'research_direction',
        'impact_score', 'source_type', 'maturity_level',
        'evidence_publication', 'explanation'
    ]

    # Обработка и запись узлов в nodes.tsv
    with open(nodes_filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=node_headers, delimiter='\t')
        writer.writeheader()
        for node in nodes:
            # Извлечение данных из 'additional_fields'
            additional_fields = node.get('additional_fields', {})
            
            # Преобразование списка публикаций в строку, разделенную '|'
            evidence_pub = additional_fields.get('evidence_publication')
            if isinstance(evidence_pub, list):
                evidence_pub_str = '|'.join(evidence_pub)
            else:
                evidence_pub_str = ''

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
    
    print(f"Данные успешно записаны в {nodes_filepath}")

    # Определение заголовков для edges.tsv
    edge_headers = [
        'subject', 'object', 'predicate', 'confidence_score', 
        'provided_by', 'evidence_publication'
    ]
    
    # Обработка и запись ребер в edges.tsv
    with open(edges_filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=edge_headers, delimiter='\t')
        writer.writeheader()
        for edge in edges:
            # Преобразование списка публикаций в строку, разделенную '|'
            evidence_pub = edge.get('evidence_publication')
            if isinstance(evidence_pub, list):
                evidence_pub_str = '|'.join(evidence_pub)
            else:
                evidence_pub_str = ''

            row = {
                'subject': edge.get('subject'),
                'object': edge.get('object'),
                'predicate': edge.get('predicate'),
                'confidence_score': edge.get('confidence_score'),
                'provided_by': edge.get('provided_by'),
                'evidence_publication': evidence_pub_str
            }
            writer.writerow(row)
            
    print(f"Данные успешно записаны в {edges_filepath}")

try:
    with open('prompts_and_shemes/test_article.txt', 'r', encoding='utf-8') as file:
        article = file.read() 
except FileNotFoundError:
    print("Ошибка: Файл не найден! ")

def main():
    """
    Главная функция для парсинга аргументов и запуска обработки.
    """
    parser = argparse.ArgumentParser(
        description="Преобразует JSON-граф в TSV-файлы формата KGX."
    )
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

    try:
        process_kgx_json(Entity_Relationships_Recognition(article_text=article), args.nodes_file, args.edges_file)

    except json.JSONDecodeError:
        print("Ошибка: Неверный формат JSON1.")
    except Exception as e:
        print(f"Произошла непредвиденная ошибка: {e}")

if __name__ == '__main__':
    main()