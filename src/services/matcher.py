import json
import os
import re
from typing import List, Dict, Set, Tuple

import requests
from dotenv import load_dotenv

from src.models.constants import TERM_NORMALIZER

# Загрузка переменных окружения из .env файла
load_dotenv()


class ResumeVacancyMatcher:
    """
    Класс для сопоставления резюме и вакансий с использованием 
    анализа текста и языковой модели
    """

    def __init__(self, llm_api_url=None, llm_api_key=None, llm_model=None):
        """
        Инициализация сопоставителя
        
        :param llm_api_url: URL API языковой модели
        :param llm_api_key: Ключ API для языковой модели
        :param llm_model: Название используемой модели
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

    def extract_skills(self, text: str):
        """
        Извлекает профессиональные навыки из текста и группирует их
        по нормализованным значениям
        
        :param text: Исходный текст (вакансия или резюме)
        :return: Словарь с нормализованными навыками и их оригинальными формами
        """
        # 1. Поиск технических навыков из словаря нормализации
        normalized_skills = {}

        # Ищем каждый технический термин в тексте
        for term, normalized in TERM_NORMALIZER.items():
            # Используем границы слов для точного поиска
            pattern = r'\b' + re.escape(term) + r'\b'
            if re.search(pattern, text.lower()):
                if normalized not in normalized_skills:
                    normalized_skills[normalized] = set()
                normalized_skills[normalized].add(term)

        return normalized_skills

    def preprocess_for_tfidf(self, text: str):
        """
        Предварительная обработка текста для TF-IDF анализа
        
        :param text: Исходный текст
        :return: Обработанный текст с нормализованными терминами
        """
        # Заменяем технические термины на нормализованные версии
        processed_text = text.lower()
        for term, normalized in TERM_NORMALIZER.items():
            # Используем границы слов для более точного поиска
            pattern = r'\b' + re.escape(term) + r'\b'
            processed_text = re.sub(pattern, normalized, processed_text)
        return processed_text

    def get_llm_analysis(self, vacancy_text: str, resume_text: str,
                         matched_skills: List[str], unmatched_skills: List[str]):
        """
        Запрашивает анализ от языковой модели
        
        :param vacancy_text: Текст вакансии
        :param resume_text: Текст резюме
        :param matched_skills: Список совпадающих навыков
        :param unmatched_skills: Список несовпадающих навыков
        :return: Кортеж из (текстовый анализ, оценка соответствия, плюсы, минусы, вердикт)
        """
        # Формируем промпт для LLM
        prompt = (
                "Инструкция для анализа соответствия резюме и вакансии\n\n"
                "Ты - строгий HR-специалист с многолетним опытом подбора персонала в IT сфере. Твоя задача - тщательно проанализировать "
                "соответствие резюме кандидата и требований вакансии, и дать максимально объективную и строгую оценку.\n\n"
                " Данные для анализа\n\n"
                "Вакансия:\n" + vacancy_text + "\n\n"
                                               "Резюме:\n" + resume_text + "\n\n"
                                                                           f"Совпавшие технические навыки: {matched_skills}\n"
                                                                           f"Не найденные технические навыки: {unmatched_skills}\n\n"

                                                                           " Правила оценки соответствия (score)\n\n"
                                                                           "Оцени соответствие резюме вакансии по шкале от 0 до 1, где:\n"
                                                                           "- 0.0-0.2: Полное несоответствие\n"
                                                                           "- 0.3-0.4: Слабое соответствие\n"
                                                                           "- 0.5-0.6: Среднее соответствие\n"
                                                                           "- 0.7-0.8: Хорошее соответствие\n"
                                                                           "- 0.9-1.0: Отличное соответствие\n\n"

                                                                           " КРИТИЧЕСКИ ВАЖНЫЕ ПРАВИЛА ОЦЕНКИ:\n\n"
                                                                           "1. Если название ДОЛЖНОСТИ кандидата НЕ СООТВЕТСТВУЕТ названию должности в вакансии, оценка НЕ МОЖЕТ быть выше 0.4\n"
                                                                           "2. Если текущий специализация кандидата отличается от требуемой в вакансии (например, разработчик vs тестировщик), оценка НЕ МОЖЕТ быть выше 0.3\n"
                                                                           "3. Обязательно внимательно анализируй названия позиций и их соответствие\n\n"

                                                                           " Формула расчета оценки:\n\n"
                                                                           "1. Начальная оценка = 1.0 (максимум)\n"
                                                                           "2. Если должности НЕ совпадают по направлению (например, Developer vs QA/Tester), вычти 0.6-0.7 из начальной оценки\n"
                                                                           "3. Если совпадает направление, но не совпадает специализация (Java Developer vs Python Developer), вычти 0.3-0.4\n"
                                                                           "4. Если не хватает критически важных навыков, дополнительно вычти 0.1-0.3\n"
                                                                           "5. Если опыт работы недостаточен, дополнительно вычти 0.1-0.2\n\n"

                                                                           " Критерии оценки (в порядке важности):\n\n"
                                                                           "1. **Должность и профессиональная область (вес 40%):**\n"
                                                                           "   - Должность кандидата ДОЛЖНА соответствовать должности в вакансии, иначе оценка резко снижается\n"
                                                                           "   - Примеры несоответствия, требующие сильного снижения оценки: Developer vs QA Engineer, Frontend vs Backend, Data Scientist vs DevOps\n"
                                                                           "   - Даже при высоком проценте совпадения технических навыков, несоответствие должностей - это КРИТИЧЕСКИЙ фактор\n\n"

                                                                           "2. **Опыт работы (вес 25%):**\n"
                                                                           "   - Соответствует ли опыт работы кандидата требуемому в вакансии\n"
                                                                           "   - Оцени релевантность опыта для конкретной должности\n"
                                                                           "   - Имеет ли кандидат опыт работы именно в требуемой роли\n\n"

                                                                           "3. **Технические навыки (вес 20%):**\n"
                                                                           "   - Проанализируй соотношение совпавших и несовпавших навыков\n"
                                                                           "   - Оцени критичность отсутствующих навыков для данной вакансии\n\n"

                                                                           "4. **Образование и сертификаты (вес 10%):**\n"
                                                                           "   - Соответствие образования требованиям вакансии\n"
                                                                           "   - Наличие профильных сертификатов\n\n"

                                                                           "5. **Дополнительные факторы (вес 5%):**\n"
                                                                           "   - Соответствие локации, формата работы, зарплатных ожиданий\n"
                                                                           "   - Soft skills и личные качества\n\n"

                                                                           " Примеры несоответствия должностей:\n\n"
                                                                           "- Java Developer → QA Automation Engineer: оценка не выше 0.3, даже при совпадении навыка Java\n"
                                                                           "- Frontend Developer → Backend Developer: оценка не выше 0.4\n"
                                                                           "- Data Scientist → DevOps Engineer: оценка не выше 0.2\n"
                                                                           "- Project Manager → Product Manager: оценка не выше 0.5\n\n"

                                                                           " Что требуется сделать\n\n"
                                                                           "На основе анализа данных составь объективную оценку, включающую:\n"
                                                                           "1. Точное числовое значение score от 0 до 1 с учетом всех критериев (будь СТРОГИМ в оценке!)\n"
                                                                           "2. Список конкретных положительных моментов (минимум 3, максимум 5)\n"
                                                                           "3. Список конкретных отрицательных моментов (минимум 2, максимум 5, особенно подчеркни несоответствие должностей!)\n"
                                                                           "4. Четкий итоговый вердикт о соответствии кандидата\n"
                                                                           "5. Развернутый комментарий с обоснованием оценки\n\n"

                                                                           " Формат ответа\n"
                                                                           "Ответ должен быть строго в формате JSON:\n"
                                                                           "```json\n"
                                                                           "{\n"
                                                                           "  \"score\": 0.3,\n"
                                                                           "  \"positives\": [\"Конкретный плюс 1\", \"Конкретный плюс 2\", \"Конкретный плюс 3\"],\n"
                                                                           "  \"negatives\": [\"Несоответствие должностей: в резюме Java Developer, а вакансия для QA Engineer\", \"Конкретный минус 2\"],\n"
                                                                           "  \"verdict\": \"Конкретная рекомендация\",\n"
                                                                           "  \"comment\": \"Развернутый комментарий с обоснованием\"\n"
                                                                           "}\n"
                                                                           "```\n"
                                                                           "Важно: Ответ должен содержать только JSON без дополнительных пояснений."
        )

        # Подготовка запроса к API
        headers = {
            "Authorization": f"Bearer {self.llm_api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": self.llm_model,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }

        # Отправка запроса и получение ответа
        response = requests.post(
            self.llm_api_url,
            headers=headers,
            json=data,
            timeout=60
        )
        response.raise_for_status()
        result = response.json()

        content = result['choices'][0]['message']['content']

        # Извлечение JSON из ответа
        try:
            # Ищем JSON в тексте, который может быть обернут в markdown блок кода
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Ищем JSON без обертки кода
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    raise ValueError("JSON не найден в ответе")

            analysis = json.loads(json_str)

            # Извлекаем компоненты ответа
            score = float(analysis.get("score", 0.5))  # По умолчанию 0.5, если оценка не указана
            positives = analysis.get("positives", [])
            negatives = analysis.get("negatives", [])
            verdict = analysis.get("verdict", "Нет вердикта")
            comment = analysis.get("comment", content)  # Если комментария нет, используем весь текст

            return comment, score, positives, negatives, verdict
        except Exception as e:
            print(f"Ошибка при парсинге JSON из ответа: {str(e)}")
            # В случае ошибки парсинга возвращаем исходный текст и дефолтные значения
            return content, 0.5, [], [], "Не удалось определить вердикт"

    def match(self, vacancy_text: str, resume_text: str):
        """
        Выполняет полный процесс сопоставления вакансии и резюме
        
        :param vacancy_text: Текст вакансии
        :param resume_text: Текст резюме
        :return: Кортеж из (совпадающие навыки, несовпадающие навыки, комментарий LLM, 
                            оценка соответствия, плюсы, минусы, вердикт)
        """
        # 1. Извлечение навыков
        vacancy_skills_dict = self.extract_skills(vacancy_text)
        resume_skills_dict = self.extract_skills(resume_text)

        # Получаем множества нормализованных ключей
        vacancy_norm_keys = set(vacancy_skills_dict.keys())
        resume_norm_keys = set(resume_skills_dict.keys())

        # Определяем совпадающие и несовпадающие нормализованные навыки
        matched_norm_skills = vacancy_norm_keys.intersection(resume_norm_keys)
        unmatched_norm_skills = vacancy_norm_keys - resume_norm_keys

        # Преобразуем обратно в оригинальные слова для вывода
        matched_skills = []
        for norm_skill in matched_norm_skills:
            matched_skills.extend(list(vacancy_skills_dict[norm_skill]))

        unmatched_skills = []
        for norm_skill in unmatched_norm_skills:
            unmatched_skills.extend(list(vacancy_skills_dict[norm_skill]))

        # Получение анализа от LLM
        llm_comment, score, positives, negatives, verdict = self.get_llm_analysis(
            vacancy_text, resume_text, matched_skills, unmatched_skills
        )

        return matched_skills, unmatched_skills, llm_comment, score, positives, negatives, verdict
