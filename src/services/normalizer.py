import os
import json
from typing import Dict, Any, Optional
import requests
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()


class ResumeNormalizer:
    """Сервис для нормализации резюме с помощью DeepSeek LLM"""
    
    def __init__(self, llm_api_url=None, llm_api_key=None, llm_model=None):
        """
        Инициализация нормализатора резюме
        
        Args:
            llm_api_url: URL API языковой модели
            llm_api_key: Ключ API для языковой модели
            llm_model: Название используемой модели
        """
        # Получаем значения из .env файла или используем переданные параметры
        self.llm_api_url = llm_api_url or os.getenv("LLM_API_URL")
        self.llm_api_key = llm_api_key or os.getenv("LLM_API_KEY")
        self.llm_model = llm_model or os.getenv("LLM_MODEL", "deepseek-ai/DeepSeek-V3")
        
        # Проверка наличия обязательных параметров
        if not self.llm_api_url:
            raise ValueError(
                "URL API языковой модели не указан. Укажите LLM_API_URL в .env файле или передайте параметр.")
        
        if not self.llm_api_key:
            raise ValueError(
                "Ключ API языковой модели не указан. Укажите LLM_API_KEY в .env файле или передайте параметр.")
    
    def normalize_resume(self, resume_text: str, email: str) -> Optional[Dict[str, Any]]:
        """
        Нормализует текст резюме с помощью DeepSeek LLM
        
        Args:
            resume_text: Текст резюме для нормализации
            email: Email пользователя (нужен для заполнения схемы)
            
        Returns:
            Нормализованные данные в формате JSON или None, если произошла ошибка
        """
        # Формируем промпт для LLM
        prompt = f"""
Проанализируй следующее резюме и извлеки из него структурированные данные в формате JSON согласно следующей схеме:

```json
{{
"name": "ФИО пользователя или просто ФИ",
"email": "{email}",
"phone": "номер телефона",
"vacancy_name": "Название желаемой должности, например Java Developer, Python Developer, DevOps Engineer и т.д.",
"languages": ["Язык1", "Язык2", "Язык3"],
"frameworks": ["Фреймворк1", "Фреймворк2", "Фреймворк3"],
"education": [
    {{
        "degree": "степень образования бакалавриат/магистратура/аспирантура",
        "direction": "направление образования",
        "specialty": "специальность образования"
    }}
],
"work_experience": [
    {{
        "start_date": "дата начало работы",
        "end_date": "дата окончания работы",
        "company_name": "Название компании",
        "achievements": [
            "Достижение1",
            "Достижение2",
            "Достижение3"
        ],
        "technologies": [
            "technology1",
            "technology2",
            "technology3",
            "technology4",
            "technology5"
        ]
    }}
]
}}
```

Важно: 
1. Данные должны быть структурированы точно по этой схеме.
2. Для полей с неизвестными значениями укажи пустые строки или массивы.
3. Возвращай только JSON без лишнего текста и комментариев.
4. Email возьми из параметра, но если в резюме указан другой email, используй его.
5. Для поля "vacancy_name" определи на основании навыков и опыта кандидата, какую должность он скорее всего ищет.
6. Если в резюме явно указана желаемая должность, используй ее для поля "vacancy_name".

Вот резюме для анализа:

{resume_text}
        """
        
        # Подготовка запроса к API
        headers = {
            "Authorization": f"Bearer {self.llm_api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": self.llm_model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1  # Низкая температура для более детерминированных результатов
        }
        
        try:
            # Отправка запроса и получение ответа
            response = requests.post(
                self.llm_api_url,
                headers=headers,
                json=data,
                timeout=60
            )
            response.raise_for_status()
            result = response.json()
            
            # Извлекаем ответ модели
            llm_response = result['choices'][0]['message']['content']
            
            # Попытка извлечь JSON из ответа
            # Сначала проверяем, есть ли в ответе блок кода
            if "```json" in llm_response:
                json_str = llm_response.split("```json")[1].split("```")[0].strip()
            elif "```" in llm_response:
                json_str = llm_response.split("```")[1].split("```")[0].strip()
            else:
                json_str = llm_response.strip()
            
            # Парсим JSON
            normalized_data = json.loads(json_str)
            
            # Проверяем, что обязательные поля присутствуют
            required_fields = ["name", "email", "vacancy_name"]
            for field in required_fields:
                if field not in normalized_data:
                    normalized_data[field] = ""
            
            # Проверяем списковые поля
            list_fields = ["languages", "frameworks"]
            for field in list_fields:
                if field not in normalized_data:
                    normalized_data[field] = []
                elif not isinstance(normalized_data[field], list):
                    # Если поле не является списком, преобразуем его в список с одним элементом
                    normalized_data[field] = [normalized_data[field]]
            
            # Проверяем структуру вложенных полей
            if "education" not in normalized_data:
                normalized_data["education"] = []
            
            if "work_experience" not in normalized_data:
                normalized_data["work_experience"] = []
            
            return normalized_data
            
        except Exception as e:
            print(f"Ошибка при нормализации резюме: {str(e)}")
            return None 