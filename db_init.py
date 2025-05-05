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
            cursor.execute(f"CREATE IF NOT EXISTS SCHEMA {DB_SCHEMA}")
        else:
            console.print(f"Схема {DB_SCHEMA} уже существует")

        cursor.close()
        conn.close()
        return True
    except Exception as e:
        console.print(f"Ошибка при создании схемы: {str(e)}")
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
    
    -- Таблица с результатами сопоставления резюме и вакансий
    CREATE TABLE IF NOT EXISTS {DB_SCHEMA}.resume_vacancy_matches (
        id VARCHAR(36) PRIMARY KEY,
        resume_id VARCHAR(36) NOT NULL REFERENCES {DB_SCHEMA}.resumes(id) ON DELETE CASCADE,
        vacancy_id VARCHAR(36) NOT NULL REFERENCES {DB_SCHEMA}.vacancies(id) ON DELETE CASCADE,
        matched_skills JSONB,
        unmatched_skills JSONB,
        llm_comment TEXT,
        score FLOAT,
        positives JSONB,
        negatives JSONB,
        verdict TEXT,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(resume_id, vacancy_id)
    );
    """

    try:
        conn = psycopg2.connect(**conn_params)
        cursor = conn.cursor()
        cursor.execute(create_tables_query)
        conn.commit()
        cursor.close()
        conn.close()
        console.print("Таблицы успешно созданы или уже существуют")
        return True
    except Exception as e:
        console.print(f"Ошибка при создании таблиц: {str(e)}")
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


def main():
    """Основная функция инициализации базы данных"""
    console.rule("Инициализация схемы базы данных")

    # Создание схемы
    if not create_schema():
        console.print(
            "Ошибка при создании схемы. Проверьте параметры подключения и права доступа.")
        return False

    # Создание таблиц
    if not create_tables():
        console.print(
            "Ошибка при создании таблиц. Проверьте параметры подключения и права доступа.")
        return False


if __name__ == "__main__":
    # При запуске скрипта напрямую
    success = main()
    if not success:
        sys.exit(1)
