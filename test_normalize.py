import json
import os

import requests
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

# Загрузка переменных окружения из .env файла
load_dotenv()

console = Console()

# URL API из .env файла
SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
SERVER_PORT = os.getenv("SERVER_PORT", "8000")
API_URL = f"http://{SERVER_HOST}:{SERVER_PORT}"

# Пример резюме для тестирования
SAMPLE_RESUME_PATH = "tests/sample_resume.pdf"


def test_normalize_resume():
    """Тестирование загрузки и нормализации резюме"""
    console.rule("[bold cyan]Тест нормализации резюме")

    if not os.path.exists(SAMPLE_RESUME_PATH):
        console.print(f"[bold red]Ошибка:[/bold red] Файл {SAMPLE_RESUME_PATH} не найден")
        console.print(f"[yellow]Разместите тестовое резюме в формате PDF по пути {SAMPLE_RESUME_PATH}[/yellow]")
        return False

    # Проверка доступности API
    try:
        health_check = requests.get(f"{API_URL}/")
        health_check.raise_for_status()
        console.print("[green]API доступен! Информация о сервисе:[/green]")
        console.print(health_check.json())
    except Exception as e:
        console.print(f"[bold red]Ошибка подключения к API: {e}[/bold red]")
        console.print(f"[yellow]Убедитесь, что сервис запущен на {API_URL}[/yellow]")
        return False

    # Отправка резюме на сервер
    try:
        console.print("[yellow]Отправка резюме на сервер...[/yellow]")

        # Открываем файл резюме
        with open(SAMPLE_RESUME_PATH, 'rb') as resume_file:
            # Формируем данные запроса
            files = {'file': (os.path.basename(SAMPLE_RESUME_PATH), resume_file, 'application/pdf')}
            data = {'email': 'test@example.com'}

            # Отправляем запрос
            response = requests.post(f"{API_URL}/api/upload-resume", files=files, data=data)
            response.raise_for_status()
            result = response.json()

            # Выводим результат
            console.print("[green]Результат нормализации резюме:[/green]")

            # Получаем ID резюме и нормализованные данные
            resume_id = result.get('resume_id')
            normalized_data = result.get('normalized_data')

            # Выводим ID резюме
            console.print(f"[bold]ID резюме:[/bold] {resume_id}")

            # Выводим базовую информацию
            console.print(f"[bold]ФИО:[/bold] {normalized_data.get('name', '')}")
            console.print(f"[bold]Email:[/bold] {normalized_data.get('email', '')}")
            console.print(f"[bold]Телефон:[/bold] {normalized_data.get('phone', '')}")
            console.print(f"[bold]Должность:[/bold] {normalized_data.get('vacancy_name', '')}")
            console.print(f"[bold]Языки программирования:[/bold] {normalized_data.get('languages', '')}")
            console.print(f"[bold]Фреймворки:[/bold] {normalized_data.get('frameworks', '')}")

            # Выводим образование
            console.print("\n[bold]Образование:[/bold]")
            for edu in normalized_data.get('education', []):
                console.print(f"  - {edu.get('degree', '')} | {edu.get('direction', '')} | {edu.get('specialty', '')}")

            # Выводим опыт работы
            console.print("\n[bold]Опыт работы:[/bold]")
            for exp in normalized_data.get('work_experience', []):
                console.print(
                    f"  - {exp.get('company_name', '')}: {exp.get('start_date', '')} - {exp.get('end_date', '')}")

                console.print("    [bold]Достижения:[/bold]")
                for achievement in exp.get('achievements', []):
                    console.print(f"      - {achievement}")

                console.print("    [bold]Технологии:[/bold]")
                for tech in exp.get('technologies', []):
                    console.print(f"      - {tech}")

            # Выводим JSON для наглядности
            console.print("\n[bold]Данные в формате JSON:[/bold]")
            json_str = json.dumps(normalized_data, ensure_ascii=False, indent=2)
            syntax = Syntax(json_str, "json", theme="monokai", line_numbers=True)
            console.print(syntax)

            console.print(Panel.fit(
                "Резюме успешно нормализовано и сохранено в базе данных.",
                title="Статус",
                border_style="green"
            ))

            return True
    except Exception as e:
        console.print(f"[bold red]Ошибка при нормализации резюме: {e}[/bold red]")
        if hasattr(e, 'response') and e.response:
            try:
                error_data = e.response.json()
                console.print(f"[red]Детали ошибки: {error_data.get('detail', 'Неизвестная ошибка')}[/red]")
            except:
                console.print(f"[red]Код ответа: {e.response.status_code}[/red]")
        return False


if __name__ == "__main__":
    test_normalize_resume()
