import os
import requests
import json
import time
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel

# Загрузка переменных окружения из .env файла
load_dotenv()

console = Console()

# Тестовые данные
test_data = {
    "vacancy_text": """
    Требуется Python-разработчик с опытом работы от 3 лет.
    Обязательные навыки: Python, FastAPI, SQL, Git.
    Желательно: опыт работы с Docker, знание английского языка.
    Мы предлагаем: удаленную работу, конкурентную зарплату, гибкий график.
    """,
    "resume_text": """
    Опыт работы Python-разработчиком 5 лет.
    Основные навыки: Python, Django, FastAPI, PostgreSQL, Git, Docker.
    Работал в команде над проектами для финтех и e-commerce.
    Английский язык - Upper Intermediate.
    Ищу удаленную работу с гибким графиком.
    """
}

# Дополнительный тестовый пример с низким соответствием
test_data_low_match = {
    "vacancy_text": """
    Требуется Senior Java-разработчик с опытом работы от 5 лет.
    Обязательные навыки: Java, Spring Boot, Hibernate, MySQL, Docker, Kubernetes.
    Желательно: опыт работы с микросервисами, знание английского языка.
    Мы предлагаем: работу в офисе, конкурентную зарплату, соц. пакет.
    """,
    "resume_text": """
    Опыт работы Python-разработчиком 3 года.
    Основные навыки: Python, Django, Flask, PostgreSQL, Git.
    Имею опыт работы с Docker, но на уровне базовых знаний.
    Английский язык - Pre-Intermediate.
    Ищу удаленную работу с гибким графиком.
    """
}

# URL API из .env файла
SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
SERVER_PORT = os.getenv("SERVER_PORT", "8000")
API_URL = f"http://{SERVER_HOST}:{SERVER_PORT}"

def test_match(data, test_name="Стандартный"):
    """Тестирование сопоставления резюме и вакансии"""
    console.rule(f"[bold cyan]Тест {test_name}")
    
    # Краткое описание теста
    console.print(Panel.fit(
        f"Вакансия: {data['vacancy_text'].strip()[:100]}...\n"
        f"Резюме: {data['resume_text'].strip()[:100]}...",
        title="Входные данные"
    ))
    
    # Отправляем запрос к API
    console.print("[yellow]Отправка запроса к API...[/yellow]")
    
    try:
        start_time = time.time()
        response = requests.post(f"{API_URL}/match", json=data)
        response.raise_for_status()
        result = response.json()
        end_time = time.time()
        
        # Форматированный вывод результатов
        console.print("[green]Результат сопоставления:[/green]")
        console.print(f"[bold]Время выполнения:[/bold] {end_time - start_time:.2f} сек.")
        console.print(f"[bold]Совпавшие навыки:[/bold] {', '.join(result['matched_skills'])}")
        console.print(f"[bold]Несовпавшие навыки:[/bold] {', '.join(result['unmatched_skills'])}")
        console.print(f"[bold]TF-IDF сходство:[/bold] {result['tfidf_score']:.2f}")
        
        console.print(Panel.fit(
            result['llm_comment'],
            title="Комментарий LLM",
            border_style="green"
        ))
        
        return True
    except Exception as e:
        console.print(f"[bold red]Ошибка:[/bold red] {e}")
        return False

def main():
    """Основная функция для запуска тестов"""
    console.print("[bold]Тестирование API сопоставления резюме и вакансий[/bold]")
    
    # Информация о конфигурации
    console.print(Panel.fit(
        f"URL API: {API_URL}\n"
        f"Модель: {os.getenv('LLM_MODEL', 'Не указана')}",
        title="Конфигурация",
        border_style="blue"
    ))
    
    # Проверка доступности API
    try:
        health_check = requests.get(f"{API_URL}/")
        health_check.raise_for_status()
        console.print("[green]API доступен! Информация о сервисе:[/green]")
        console.print(health_check.json())
    except Exception as e:
        console.print(f"[bold red]Ошибка подключения к API: {e}[/bold red]")
        console.print(f"[yellow]Убедитесь, что сервис запущен на {API_URL}[/yellow]")
        return
    
    # Запуск тестов
    result1 = test_match(test_data, "высокое соответствие")
    result2 = test_match(test_data_low_match, "низкое соответствие")
    
    # Итог
    if result1 and result2:
        console.print("[bold green]Все тесты выполнены успешно![/bold green]")
    else:
        console.print("[bold red]Некоторые тесты завершились с ошибками![/bold red]")

if __name__ == "__main__":
    main() 