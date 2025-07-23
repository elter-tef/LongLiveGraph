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

## Минимальный запуск

Чтобы быстро протестировать работу пайплайна извлечения знаний из текста для формирования графа, выполните следующие шаги:

1. **Настройте переменные окружения для доступа к LLM API**
   
   - OAI_COMPATIBLE_API_KEY
   
   - OAI_COMPATIBLE_BASE_URL
   
   - MODEL_NAME

2. **Убедитесь, что ваша LLM-платформа поддерживает GBNF-грамматику**
   
   - Текущая версия требует совместимости с llama.cpp (или эквивалентной платформой), поддерживающей строгую валидацию с помощью GBNF-grammar (см. файл `json_schema_to_grammar.py`).
   
   - Без поддержки GBNF корректная работа пайплайна невозможна.

3. **Запустите основной скрипт с примером текста:**
   В корневой директории репозитория выполните:
   
   bash
   
   `python txt2KGX.py test_article.txt --nodes-file nodes.tsv --edges-file edges.tsv`
   
   - `test_article.txt` — пример биомедицинской статьи для теста.
   
   - `--nodes-file` и `--edges-file` — наименования выходных файлов для узлов и рёбер графа.

4. **Результат**
   После выполнения команды появятся два файла:
   
   - `nodes.tsv` — перечень извлечённых сущностей (узлов).
   
   - `edges.tsv` — таблица извлечённых связей.
