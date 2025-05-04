#!/usr/bin/env python
"""
Запускной скрипт сервиса сопоставления резюме с вакансиями
"""
import os
import sys
from dotenv import load_dotenv
import uvicorn
from rich.console import Console

from src.main import app
from db_init import check_env_variables, create_schema, create_tables, check_connection

# Загрузка переменных окружения из .env файла
load_dotenv()

# Инициализация консоли для красивого вывода
console = Console()

def init_database():
    """Инициализация базы данных перед запуском приложения"""
    console.rule("[bold cyan]Проверка и инициализация базы данных[/bold cyan]")
    
    # Проверка переменных окружения
    check_env_variables()
    
    # Создание схемы
    if not create_schema():
        console.print("[bold red]Ошибка при создании схемы. Проверьте параметры подключения и права доступа.[/bold red]")
        return False
    
    # Создание таблиц
    if not create_tables():
        console.print("[bold red]Ошибка при создании таблиц. Проверьте параметры подключения и права доступа.[/bold red]")
        return False
    
    # Проверка подключения
    if not check_connection():
        console.print("[bold red]Ошибка при проверке подключения к базе данных![/bold red]")
        return False
    
    console.print("[bold green]База данных успешно инициализирована![/bold green]")
    return True

if __name__ == "__main__":
    # Инициализация базы данных
    if not init_database():
        console.print("[bold red]Ошибка инициализации базы данных. Приложение не будет запущено.[/bold red]")
        sys.exit(1)
    
    # Получаем настройки сервера из .env файла 
    host = os.getenv("SERVER_HOST", "0.0.0.0")
    port = int(os.getenv("SERVER_PORT", "8000"))
    
    console.rule("[bold cyan]Запуск сервиса[/bold cyan]")
    console.print(f"[green]Сервис доступен по адресу:[/green] http://{host}:{port}")
    console.print("[bold]Доступные эндпоинты:[/bold]")
    console.print("- [bold cyan]/docs[/bold cyan] - Swagger документация API")
    console.print("- [bold cyan]/[/bold cyan] - Информация о сервисе")
    console.print("- [bold cyan]/match[/bold cyan] - Сопоставление резюме и вакансии")
    console.print("- [bold cyan]/upload-resume[/bold cyan] - Загрузка и нормализация резюме в формате PDF")
    console.print("- [bold cyan]/match-stored-resume[/bold cyan] - Сопоставление загруженного резюме с вакансией")
    console.print("- [bold cyan]/resumes/{email}[/bold cyan] - Получение списка резюме пользователя")
    console.print("- [bold cyan]/normalized-resume/{resume_id}[/bold cyan] - Получение нормализованных данных резюме")
    
    # Запуск сервиса
    uvicorn.run(app, host=host, port=port) 