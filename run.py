import os
import sys

import uvicorn
from dotenv import load_dotenv
from rich.console import Console

from db_init import create_schema, create_tables, check_connection
from src.main import app

# Загрузка переменных окружения из .env файла
load_dotenv()

# Инициализация консоли для красивого вывода
console = Console()

if __name__ == "__main__":
    # Получаем настройки сервера из .env файла 
    host = os.getenv("SERVER_HOST", "0.0.0.0")
    port = int(os.getenv("SERVER_PORT", "8000"))

    # Запуск сервиса
    uvicorn.run(app, host=host, port=port)
