from extractor import Entity_Relationships_Recognition

try:
    with open('prompts_and_shemes/test_article.txt', 'r', encoding='utf-8') as file:
        article = file.read() 
except FileNotFoundError:
    print("Ошибка: Файл не найден! ")

res = Entity_Relationships_Recognition(article_text=article)
print(res)