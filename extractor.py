import os
import json
import csv
import uuid
from openai import OpenAI
from config import OAI_COMPATIBLE_API_KEY, OAI_COMPATIBLE_BASE_URL, MODEL_NAME
import json_schema_to_grammar

def convert_schema_to_grammar(json_schema: dict) -> str:
    """
    Конвертирует JSON-схему в формат грамматики GBNF для llama.cpp.
    Добавляет обработку тегов <thinking>...</thinking>.
    """
    converter = json_schema_to_grammar.SchemaConverter(
        prop_order={},
        allow_fetch=False,
        dotall=False,
        raw_pattern=False
    )
    
    converter.visit(json_schema, 'json-schema')
    json_grammar = converter.format_grammar()
    
    # Add <thinking> before JSON
    base_rules = """
root ::= "<thinking>" [^<]+ "</thinking>" [\\n]* json-schema
"""
    return base_rules + json_grammar

try:
    with open('prompts_and_shemes/main_extractor_prompt.txt', 'r', encoding='utf-8') as file:
        main_extractor_prompt = file.read()
except FileNotFoundError:
    print("Ошибка: Файл не найден! ")

try:
    with open('prompts_and_shemes/main_extractor_shema.json', 'r', encoding='utf-8') as f:
        main_extractor_schema = json.load(f)
except FileNotFoundError:
    print(f"Ошибка: файл схемы не найден ")

client = OpenAI(
    base_url=OAI_COMPATIBLE_BASE_URL,
    api_key=OAI_COMPATIBLE_API_KEY
)

# Создание грамматики на основе схемы
grammar = convert_schema_to_grammar(main_extractor_schema)

def Entity_Relationships_Recognition(article_text):
    try:
        chat_completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": main_extractor_prompt,
                },
                {
                    "role": "user",
                    "content": article_text,
                },
            ],
            temperature=0.5,
            extra_body={
                "grammar": grammar
            }
        )
        
        response_content = chat_completion.choices[0].message.content
        
        # Извлекаем JSON из ответа, игнорируя часть с <thinking>
        closing_tag = "</thinking>"
        try:
            think_end_pos = response_content.rfind(closing_tag)
            if think_end_pos != -1:
                search_start_pos = think_end_pos + len(closing_tag)
                json_start_index = response_content.find('{', search_start_pos)
                if json_start_index != -1:
                    json_string = response_content[json_start_index:]
                    parsed_json = json.loads(json_string)
                    return parsed_json
                else:
                    print("\nНе удалось найти JSON после тега </thinking>.")
            else:
                print("\nПредупреждение: тег </thinking> не найден. Попытка найти JSON с начала ответа.")
                json_start_index = response_content.find('{')
                if json_start_index != -1:
                    json_string = response_content[json_start_index:]
                    parsed_json = json.loads(json_string)
                    print("\nИзвлеченный и распарсенный JSON (запасной метод):")
                    print(json.dumps(parsed_json, indent=2, ensure_ascii=False))
                    return parsed_json
                else:
                    print("\nНе удалось найти JSON в ответе.")
        except json.JSONDecodeError as e:
            print(f"\nОшибка декодирования JSON: {e}")
            print("Проверьте, что модель вернула корректный JSON.")
        except Exception as e:
            print(f"\nПроизошла непредвиденная ошибка при обработке ответа: {e}")
            
    except Exception as e:
        print(f"\nПроизошла ошибка при выполнении запроса: {e}")

def process_kgx_json(json_data, nodes_filepath, edges_filepath):
    """
    Обрабатывает JSON-данные, извлекает узлы и ребра и дозаписывает их в TSV-файлы
    в формате, совместимом с PloverDB и Biolink-моделью.
    
    :param json_data: Словарь, содержащий данные графа.
    :param nodes_filepath: Путь к выходному файлу для узлов (nodes.tsv).
    :param edges_filepath: Путь к выходному файлу для ребер (edges.tsv).
    """
    graph = json_data.get('graph', {})
    nodes = graph.get('nodes', [])
    edges = graph.get('edges', [])

    # --- Обработка и дозапись узлов в nodes.tsv (совместимо с PloverDB) ---
    node_headers = [
        'id', 'name', 'all_categories', 'confidence_score', 'research_direction',
        'impact_score', 'source_type', 'maturity_level',
        'evidence_publication', 'explanation'
    ]

    # Проверяем, нужно ли записывать заголовок
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
                'all_categories': node.get('category'),  # Переименовано для совместимости с PloverDB
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

    # --- Обработка и дозапись ребер в edges.tsv (совместимо с PloverDB) ---
    edge_headers = [
        'id', 'subject', 'object', 'predicate', 'confidence_score',
        'provided_by', 'evidence_publication', 'primary_knowledge_source'
    ]

    # Проверяем, нужно ли записывать заголовок
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
                'id': str(uuid.uuid4()),  # Уникальный идентификатор ребра
                'subject': edge.get('subject'),
                'object': edge.get('object'),
                'predicate': edge.get('predicate'),
                'confidence_score': edge.get('confidence_score'),
                'provided_by': edge.get('provided_by'),
                'evidence_publication': evidence_pub_str,
                'primary_knowledge_source': 'infores:mygraph'  # Источник знаний для PloverDB
            }
            writer.writerow(row)

    print(f"Данные ребер успешно дозаписаны в {edges_filepath}")
