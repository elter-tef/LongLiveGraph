**HALD/convert_json_to_biolink.py**

Сервисный скрипт для конвертации JSON-ов с сущностями и отношениями [датасета HALD](https://figshare.com/articles/dataset/HALD_a_human_aging_and_longevity_knowledge_graph_for_precision_gerontology_and_geroscience_analyses/22828196?utm_source=chatgpt.com) в формат Biolink Model/TSV-таблиц.

- Маппит типы сущностей и отношений на термины Biolink/LECO (через .csv-файлы соответствий).

- Генерирует nodes.tsv и edges.tsv из произвольных JSON с сущностями/отношениями, обеспечивая совместимость с PloverDB.

**prompts_and_shemes/**

- main_extractor_prompt.txt — промпт, описывающий все 
  требования к извлечению информации (категории Biolink/LECO, требования к
   confidence_score, обработка переводов, политики deduplication, поля для
   biomarker/intervention и пр.; если результат не определён, добавлять 
  clarifications на русском).

- main_extractor_shema.json — JSON-схема для валидации результата (структура graph/nodes/edges/clarifications)

- test_article.txt — пример входного текста для тестирования.

**extractor.py**

Ключевой модуль для взаимодействия с LLM по спецификации хакатона:

- Читает промпт и JSON-схему из директории /prompts_and_shemes.

- Формирует prompt и grammar для модели.

- Функция **Entity_Relationships_Recognition** вызывает LLM OpenAI API, получает и корректно распарсивает JSON-ответ в соответствии со схемой используя Structured Outputs GBNF грамматику .

- **process_kgx_json** записывает из полученного JSON-graph — в nodes.tsv и edges.tsv, добавляя специфические поля (достоверность, публикации и пр.)

**txt2KGX.py**
Главная управляющая точка для обработки текстовой статьи.

- Принимает файл с текстом (аргументы командной строки: входной файл, опционально имена выходных .tsv).

- Передаёт текст в функцию извлечения сущностей и отношений.

- Записывает результат в файлы узлов (nodes.tsv) и рёбер (edges.tsv) в формате KGX (PloverDB-совместимый
