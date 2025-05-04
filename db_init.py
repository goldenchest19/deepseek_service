#!/usr/bin/env python
"""
Скрипт для инициализации схемы в базе данных PostgreSQL
"""
import os
import sys

import psycopg2
from dotenv import load_dotenv
from rich.console import Console

# Загружаем переменные окружения
load_dotenv()

# Параметры подключения из .env
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5433")
DB_NAME = os.getenv("DB_NAME", "postgres")
DB_SCHEMA = os.getenv("DB_SCHEMA", "resume_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

# Инициализация консоли для красивого вывода
console = Console()


def check_env_variables():
    """Проверка наличия переменных окружения"""
    console.print("[bold]Проверка переменных окружения для подключения к БД:[/bold]")

    if not DB_HOST:
        console.print("[red]DB_HOST не указан, используется значение по умолчанию: localhost[/red]")
    else:
        console.print(f"[green]DB_HOST = {DB_HOST}[/green]")

    if not DB_PORT:
        console.print("[red]DB_PORT не указан, используется значение по умолчанию: 5433[/red]")
    else:
        console.print(f"[green]DB_PORT = {DB_PORT}[/green]")

    if not DB_NAME:
        console.print("[red]DB_NAME не указан, используется значение по умолчанию: postgres[/red]")
    else:
        console.print(f"[green]DB_NAME = {DB_NAME}[/green]")
        
    if not DB_SCHEMA:
        console.print("[red]DB_SCHEMA не указан, используется значение по умолчанию: resume_db[/red]")
    else:
        console.print(f"[green]DB_SCHEMA = {DB_SCHEMA}[/green]")

    if not DB_USER:
        console.print("[red]DB_USER не указан, используется значение по умолчанию: postgres[/red]")
    else:
        console.print(f"[green]DB_USER = {DB_USER}[/green]")

    if not DB_PASSWORD:
        console.print("[yellow]ВНИМАНИЕ: DB_PASSWORD не указан или пустой[/yellow]")
    else:
        console.print("[green]DB_PASSWORD = ********[/green]")


def create_schema():
    """Создание схемы, если она не существует"""
    # Параметры подключения к postgres
    conn_params = {
        "host": DB_HOST,
        "database": DB_NAME,
        "user": DB_USER,
        "password": DB_PASSWORD,
        "port": DB_PORT
    }

    try:
        # Подключаемся к postgres для создания схемы
        conn = psycopg2.connect(**conn_params)
        conn.autocommit = True
        cursor = conn.cursor()

        # Проверяем существование схемы
        cursor.execute(f"SELECT schema_name FROM information_schema.schemata WHERE schema_name = '{DB_SCHEMA}'")
        exists = cursor.fetchone()

        if not exists:
            console.print(f"[yellow]Схема {DB_SCHEMA} не существует. Создаем...[/yellow]")
            cursor.execute(f"CREATE SCHEMA {DB_SCHEMA}")
            console.print(f"[green]Схема {DB_SCHEMA} успешно создана[/green]")
        else:
            console.print(f"[green]Схема {DB_SCHEMA} уже существует[/green]")

        cursor.close()
        conn.close()
        return True
    except Exception as e:
        console.print(f"[bold red]Ошибка при создании схемы: {str(e)}[/bold red]")
        return False


def create_tables():
    """Создание таблиц в базе данных"""
    # Параметры подключения к базе данных
    conn_params = {
        "host": DB_HOST,
        "database": DB_NAME,
        "user": DB_USER,
        "password": DB_PASSWORD,
        "port": DB_PORT
    }

    create_tables_query = f"""
    -- Таблица со всеми резюме
    CREATE TABLE IF NOT EXISTS {DB_SCHEMA}.resumes (
        id VARCHAR(36) PRIMARY KEY,
        email VARCHAR(255) NOT NULL,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        raw_text TEXT NOT NULL,
        metadata JSONB,
        pdf_content BYTEA
    );
    
    -- Таблица с нормализованными данными резюме
    CREATE TABLE IF NOT EXISTS {DB_SCHEMA}.normalized_resumes (
        id VARCHAR(36) PRIMARY KEY REFERENCES {DB_SCHEMA}.resumes(id) ON DELETE CASCADE,
        name VARCHAR(255),
        email VARCHAR(255) NOT NULL,
        phone VARCHAR(100),
        vacancy_name VARCHAR(255),
        languages JSONB,
        frameworks JSONB,
        education JSONB,
        work_experience JSONB,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    
    -- Таблица с вакансиями
    CREATE TABLE IF NOT EXISTS {DB_SCHEMA}.vacancies (
        id VARCHAR(36) PRIMARY KEY,
        title VARCHAR(255) NOT NULL,
        company VARCHAR(255) NOT NULL,
        description TEXT NOT NULL,
        salary_from INTEGER,
        salary_to INTEGER,
        currency VARCHAR(10),
        experience VARCHAR(100),
        skills JSONB,
        url VARCHAR(1000) NOT NULL,
        original_id VARCHAR(100),
        source VARCHAR(50) DEFAULT 'hh.ru',
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    """

    try:
        conn = psycopg2.connect(**conn_params)
        cursor = conn.cursor()
        cursor.execute(create_tables_query)
        conn.commit()
        cursor.close()
        conn.close()
        console.print("[green]Таблицы успешно созданы или уже существуют[/green]")
        return True
    except Exception as e:
        console.print(f"[bold red]Ошибка при создании таблиц: {str(e)}[/bold red]")
        return False


def check_connection():
    """Проверка подключения к базе данных"""
    conn_params = {
        "host": DB_HOST,
        "database": DB_NAME,
        "user": DB_USER,
        "password": DB_PASSWORD,
        "port": DB_PORT
    }

    try:
        conn = psycopg2.connect(**conn_params)
        cursor = conn.cursor()
        
        # Проверка доступа к схеме
        cursor.execute(f"SET search_path TO {DB_SCHEMA}")
        cursor.execute("SELECT current_schema()")
        schema = cursor.fetchone()[0]
        
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        console.print(f"[green]Подключение к базе данных успешно:[/green] {version}")
        console.print(f"[green]Текущая схема:[/green] {schema}")
        return True
    except Exception as e:
        console.print(f"[bold red]Ошибка подключения к базе данных: {str(e)}[/bold red]")
        return False


def recreate_tables():
    """Удаление и пересоздание таблиц в базе данных"""
    # Параметры подключения к базе данных
    conn_params = {
        "host": DB_HOST,
        "database": DB_NAME,
        "user": DB_USER,
        "password": DB_PASSWORD,
        "port": DB_PORT
    }

    drop_tables_query = f"""
    DROP TABLE IF EXISTS {DB_SCHEMA}.normalized_resumes;
    DROP TABLE IF EXISTS {DB_SCHEMA}.resumes;
    """

    try:
        conn = psycopg2.connect(**conn_params)
        cursor = conn.cursor()
        cursor.execute(drop_tables_query)
        conn.commit()
        cursor.close()
        conn.close()
        console.print("[green]Таблицы успешно удалены[/green]")
        return True
    except Exception as e:
        console.print(f"[bold red]Ошибка при удалении таблиц: {str(e)}[/bold red]")
        return False


def main():
    """Основная функция инициализации базы данных"""
    console.rule("[bold]Инициализация схемы базы данных[/bold]")

    # Проверка переменных окружения
    check_env_variables()

    # Создание схемы
    if not create_schema():
        console.print(
            "[bold red]Ошибка при создании схемы. Проверьте параметры подключения и права доступа.[/bold red]")
        return False

    # Удаление и пересоздание таблиц
    if not recreate_tables():
        console.print(
            "[bold red]Ошибка при удалении таблиц. Проверьте параметры подключения и права доступа.[/bold red]")
        return False

    # Создание таблиц
    if not create_tables():
        console.print(
            "[bold red]Ошибка при создании таблиц. Проверьте параметры подключения и права доступа.[/bold red]")
        return False

    # Проверка подключения
    if check_connection():
        console.print("[bold green]Схема базы данных успешно инициализирована![/bold green]")
        return True
    else:
        console.print("[bold red]Ошибка при проверке подключения к базе данных![/bold red]")
        return False


if __name__ == "__main__":
    # При запуске скрипта напрямую
    success = main()
    if not success:
        sys.exit(1)
