import os
import re
import ssl
from typing import List, Dict, Set, Tuple

import nltk
import requests
from dotenv import load_dotenv
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Загрузка переменных окружения из .env файла
load_dotenv()

# Исправление проблемы с SSL для загрузки данных nltk
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

# Загрузка стоп-слов с обработкой ошибок
try:
    nltk.download('stopwords', quiet=True)
    from nltk.corpus import stopwords

    STOPWORDS = set(stopwords.words('russian'))
except Exception as e:
    print(f"Ошибка при загрузке стоп-слов: {e}")
    # Предоставляем базовый набор русских стоп-слов в случае ошибки
    STOPWORDS = {"и", "в", "на", "не", "что", "он", "с", "по", "это", "она", "так", "но", "а", "его", "как", "из", "то",
                 "я", "за"}

# Словарь для нормализации технических терминов и синонимов
TERM_NORMALIZER = {
    # Языки программирования
    'python': 'python',
    'пайтон': 'python',
    # Базы данных
    'sql': 'sql',
    'postgresql': 'postgresql_sql',
    'postgres': 'postgresql_sql',
    'mysql': 'mysql_sql',
    'sqlite': 'sqlite_sql',
    # Фреймворки
    'django': 'django',
    'fastapi': 'fastapi',
    'flask': 'flask',
    # Контроль версий
    'git': 'git',
    'github': 'git',
    'gitlab': 'git',
    # Контейнеризация
    'docker': 'docker',
    'kubernetes': 'kubernetes',
    'k8s': 'kubernetes',
    # Языки
    'английский': 'english',
    'английского': 'english',
    'англ': 'english'
}


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

    def extract_skills(self, text: str) -> Dict[str, Set[str]]:
        """
        Извлекает ключевые слова (навыки) из текста и группирует их
        по нормализованным значениям
        
        :param text: Исходный текст (вакансия или резюме)
        :return: Словарь с нормализованными навыками и их оригинальными формами
        """
        # Ищем слова длиннее 3 символов, не стоп-слова
        words = re.findall(r'\b\w{4,}\b', text.lower())
        # Фильтруем стоп-слова и нормализуем термины
        raw_skills = [w for w in words if w not in STOPWORDS]
        
        # Группируем навыки по нормализованным значениям
        normalized_skills = {}
        for skill in raw_skills:
            # Если есть в словаре нормализации, используем нормализованную версию
            norm_skill = TERM_NORMALIZER.get(skill, skill)
            if norm_skill not in normalized_skills:
                normalized_skills[norm_skill] = set()
            normalized_skills[norm_skill].add(skill)
        
        return normalized_skills

    def preprocess_for_tfidf(self, text: str) -> str:
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

    def calculate_tfidf_similarity(self, text1: str, text2: str) -> float:
        """
        Вычисляет TF-IDF косинусное сходство между двумя текстами
        
        :param text1: Первый текст (вакансия)
        :param text2: Второй текст (резюме)
        :return: Значение косинусного сходства (0-1)
        """
        # Предобработка текстов
        processed_text1 = self.preprocess_for_tfidf(text1)
        processed_text2 = self.preprocess_for_tfidf(text2)
        
        # Вычисление TF-IDF и косинусного сходства
        vectorizer = TfidfVectorizer(stop_words=list(STOPWORDS))
        tfidf = vectorizer.fit_transform([processed_text1, processed_text2])
        similarity = cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0]
        
        return similarity

    def get_llm_analysis(self, vacancy_text: str, resume_text: str,
                         matched_skills: List[str], unmatched_skills: List[str],
                         tfidf_score: float) -> str:
        """
        Запрашивает анализ от языковой модели
        
        :param vacancy_text: Текст вакансии
        :param resume_text: Текст резюме
        :param matched_skills: Список совпадающих навыков
        :param unmatched_skills: Список несовпадающих навыков
        :param tfidf_score: Значение TF-IDF сходства
        :return: Текстовый анализ от языковой модели
        """
        # Формируем промпт для LLM
        prompt = (
                "Вакансия:\n" + vacancy_text +
                "\n\nРезюме:\n" + resume_text +
                f"\n\nСовпавшие навыки: {matched_skills}\nНе найденные навыки: {unmatched_skills}\nСходство TF-IDF: {tfidf_score:.2f}\n"
                "На основе этих данных оцени, насколько резюме подходит для вакансии по 10-балльной шкале."
                " Объясни свой вывод: на что ты опираешься, какие сильные и слабые стороны кандидата по сравнению с вакансией."
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
        
        return result['choices'][0]['message']['content']

    def match(self, vacancy_text: str, resume_text: str) -> Tuple[List[str], List[str], float, str]:
        """
        Выполняет полный процесс сопоставления вакансии и резюме
        
        :param vacancy_text: Текст вакансии
        :param resume_text: Текст резюме
        :return: Кортеж из (совпадающие навыки, несовпадающие навыки, 
                      tf-idf сходство, комментарий LLM)
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
        
        # 2. Вычисление TF-IDF сходства
        tfidf_score = self.calculate_tfidf_similarity(vacancy_text, resume_text)
        
        # 3. Получение анализа от LLM
        llm_comment = self.get_llm_analysis(
            vacancy_text, resume_text, matched_skills, unmatched_skills, tfidf_score
        )
        
        return matched_skills, unmatched_skills, tfidf_score, llm_comment 