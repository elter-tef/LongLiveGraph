import json
import csv
import uuid
import pandas as pd
from typing import Dict, Set, List, Tuple

def load_mapping_files() -> Tuple[Dict[str, str], Dict[str, str]]:
    """
    Загружает файлы маппинга для преобразования типов сущностей и отношений
    в термины Biolink Model
    """
    # Загрузка маппинга типов сущностей
    entity_mapping = {}
    with open('to_biolink_entity.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            dataset_type = row['Entity in dataset'].strip()
            biolink_type = row['to Biolink Model'].strip()
            entity_mapping[dataset_type] = biolink_type
    
    print(f"DEBUG: Загруженные типы сущностей: {list(entity_mapping.keys())}")
    
    # Загрузка маппинга отношений
    relationship_mapping = {}
    with open('to_biolink_relationship.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            dataset_relationships = row['relationship in dataset'].strip()
            biolink_predicate = row['To biolink:predicate'].strip()
            # Разделяем множественные отношения через запятую
            for rel in dataset_relationships.split(','):
                rel = rel.strip()
                relationship_mapping[rel] = biolink_predicate
    
    print(f"DEBUG: Несколько примеров отношений: {list(relationship_mapping.keys())[:10]}")
    return entity_mapping, relationship_mapping

def load_entities(filepath: str) -> Dict[str, str]:
    """
    Загружает сущности из Entity_Info.json
    Возвращает словарь: {entity_name: entity_type}
    """
    entities = {}
    print(f"DEBUG: Загружаем сущности из {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"DEBUG: Тип данных в JSON: {type(data)}")
    print(f"DEBUG: Ключи верхнего уровня: {list(data.keys()) if isinstance(data, dict) else 'Не словарь'}")
    
    # Более гибкая обработка структуры JSON
    def extract_entities(obj, depth=0):
        if depth > 3:  # Защита от бесконечной рекурсии
            return
        
        if isinstance(obj, dict):
            # Если это сущность с ключами entity и type
            if 'entity' in obj and 'type' in obj:
                entity_name = obj['entity']
                entity_type = obj['type']
                entities[entity_name] = entity_type
                if len(entities) <= 5:  # Показываем первые 5 для отладки
                    print(f"DEBUG: Найдена сущность: {entity_name} -> {entity_type}")
            else:
                # Рекурсивно обрабатываем все значения
                for value in obj.values():
                    extract_entities(value, depth + 1)
        elif isinstance(obj, list):
            # Обрабатываем каждый элемент списка
            for item in obj:
                extract_entities(item, depth + 1)
    
    extract_entities(data)
    print(f"DEBUG: Итого найдено сущностей: {len(entities)}")
    return entities

def load_relations(filepath: str) -> List[Dict[str, str]]:
    """
    Загружает отношения из Relation_Info.json
    Возвращает список словарей с ключами: source_entity, target_entity, relationship
    """
    relations = []
    print(f"DEBUG: Загружаем отношения из {filepath}")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"DEBUG: Тип данных отношений: {type(data)}")
        
        if isinstance(data, dict):
            print(f"DEBUG: Ключи верхнего уровня отношений: {list(data.keys())}")
        elif isinstance(data, list):
            print(f"DEBUG: Список содержит {len(data)} элементов")
            if len(data) > 0:
                print(f"DEBUG: Тип первого элемента: {type(data[0])}")
                if isinstance(data[0], dict):
                    print(f"DEBUG: Ключи первого элемента: {list(data[0].keys())}")
        
        # Более гибкая обработка структуры JSON для отношений
        def extract_relations(obj, depth=0):
            if depth > 3:  # Защита от бесконечной рекурсии
                return
            
            if isinstance(obj, dict):
                # Проверяем различные возможные ключи для отношений
                possible_source_keys = ['source entity', 'source_entity', 'source', 'from', 'subject']
                possible_target_keys = ['target entity', 'target_entity', 'target', 'to', 'object']
                possible_rel_keys = ['relationship', 'relation', 'predicate', 'type']
                
                source = None
                target = None
                relationship = None
                
                for key in possible_source_keys:
                    if key in obj:
                        source = obj[key]
                        break
                
                for key in possible_target_keys:
                    if key in obj:
                        target = obj[key]
                        break
                
                for key in possible_rel_keys:
                    if key in obj:
                        relationship = obj[key]
                        break
                
                if source and target and relationship:
                    rel_dict = {
                        'source_entity': str(source).strip(),
                        'target_entity': str(target).strip(),
                        'relationship': str(relationship).strip()
                    }
                    relations.append(rel_dict)
                    if len(relations) <= 5:  # Показываем первые 5 для отладки
                        print(f"DEBUG: Найдено отношение: {rel_dict}")
                else:
                    # Рекурсивно обрабатываем вложенные объекты
                    for value in obj.values():
                        extract_relations(value, depth + 1)
            elif isinstance(obj, list):
                # Обрабатываем каждый элемент списка
                for item in obj:
                    extract_relations(item, depth + 1)
        
        extract_relations(data)
        
    except Exception as e:
        print(f"DEBUG: Ошибка при загрузке отношений: {e}")
    
    print(f"DEBUG: Итого найдено отношений: {len(relations)}")
    return relations

def generate_nodes_tsv(entities: Dict[str, str], entity_mapping: Dict[str, str]) -> Dict[str, str]:
    """
    Генерирует файл nodes.tsv в формате, совместимом с PloverDB
    Возвращает словарь {entity_name: node_id}
    """
    nodes_data = []
    entity_id_mapping = {}
    mapped_count = 0
    unmapped_types = set()
    
    for entity_name, entity_type in entities.items():
        # Проверяем, есть ли маппинг для этого типа сущности
        if entity_type in entity_mapping:
            # Генерируем уникальный ID в формате CURIE
            node_id = f"MYGRAPH:{str(uuid.uuid4())}"
            biolink_category = entity_mapping[entity_type]
            
            nodes_data.append({
                'id': node_id,
                'name': entity_name,
                'all_categories': biolink_category  # Изменено с 'category' на 'all_categories'
            })
            
            entity_id_mapping[entity_name] = node_id
            mapped_count += 1
        else:
            unmapped_types.add(entity_type)
    
    print(f"DEBUG: Замаплено сущностей: {mapped_count}")
    print(f"DEBUG: Незамапленные типы: {unmapped_types}")
    
    # Сохраняем в TSV файл
    df_nodes = pd.DataFrame(nodes_data)
    df_nodes.to_csv('nodes.tsv', sep='\t', index=False)
    
    return entity_id_mapping

def generate_edges_tsv(relations: List[Dict[str, str]], 
                      entity_id_mapping: Dict[str, str],
                      relationship_mapping: Dict[str, str]):
    """
    Генерирует файл edges.tsv в формате, совместимом с PloverDB
    """
    edges_data = []
    missing_entities = set()
    unmapped_relationships = set()
    found_relationships = set()
    
    for relation in relations:
        source_entity = relation['source_entity']
        target_entity = relation['target_entity']
        relationship = relation['relationship']
        
        found_relationships.add(relationship)
        
        # Проверяем наличие сущностей
        source_found = source_entity in entity_id_mapping
        target_found = target_entity in entity_id_mapping
        rel_found = relationship in relationship_mapping
        
        if not source_found:
            missing_entities.add(f"source: {source_entity}")
        if not target_found:
            missing_entities.add(f"target: {target_entity}")
        if not rel_found:
            unmapped_relationships.add(relationship)
        
        # Проверяem, что обе сущности есть в нашем маппинге узлов
        # и что отношение есть в маппинге отношений
        if source_found and target_found and rel_found:
            edges_data.append({
                'id': str(uuid.uuid4()),  # Добавлен уникальный идентификатор ребра
                'subject': entity_id_mapping[source_entity],
                'object': entity_id_mapping[target_entity],
                'predicate': relationship_mapping[relationship],
                'primary_knowledge_source': 'infores:mygraph'  # Добавлен источник знаний
            })
    
    print(f"DEBUG: Найдено уникальных отношений в данных: {len(found_relationships)}")
    print(f"DEBUG: Примеры найденных отношений: {list(found_relationships)[:10]}")
    print(f"DEBUG: Незамапленные отношения: {unmapped_relationships}")
    print(f"DEBUG: Примеры отсутствующих сущностей: {list(missing_entities)[:10]}")
    print(f"DEBUG: Валидных рёбер создано: {len(edges_data)}")
    
    # Сохраняем в TSV файл
    df_edges = pd.DataFrame(edges_data)
    df_edges.to_csv('edges.tsv', sep='\t', index=False)

def main():
    """
    Основная функция программы
    """
    print("Загружаем файлы маппинга...")
    entity_mapping, relationship_mapping = load_mapping_files()
    print(f"Загружено {len(entity_mapping)} типов сущностей")
    print(f"Загружено {len(relationship_mapping)} типов отношений")
    
    print("Загружаем сущности из Entity_Info.json...")
    entities = load_entities('Entity_Info.json')
    print(f"Загружено {len(entities)} сущностей")
    
    print("Загружаем отношения из Relation_Info.json...")
    relations = load_relations('Relation_Info.json')
    print(f"Загружено {len(relations)} отношений")
    
    print("Генерируем nodes.tsv...")
    entity_id_mapping = generate_nodes_tsv(entities, entity_mapping)
    print(f"Сгенерировано {len(entity_id_mapping)} узлов")
    
    print("Генерируем edges.tsv...")
    generate_edges_tsv(relations, entity_id_mapping, relationship_mapping)
    
    print("Готово! Файлы nodes.tsv и edges.tsv созданы в формате, совместимом с PloverDB.")

if __name__ == "__main__":
    main()

