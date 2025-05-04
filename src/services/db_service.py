import os
import json
from typing import Optional, Dict, Any, Tuple, List
import psycopg2
from psycopg2.extras import Json, RealDictCursor
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Константы для подключения к базе данных
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5433")
DB_NAME = os.getenv("DB_NAME", "postgres")
DB_SCHEMA = os.getenv("DB_SCHEMA", "resume_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")


class DBService:
    """Сервис для работы с базой данных PostgreSQL"""
    
    def __init__(self):
        """Инициализация подключения к базе данных"""
        self.conn_params = {
            "host": DB_HOST,
            "database": DB_NAME,
            "user": DB_USER,
            "password": DB_PASSWORD,
            "port": DB_PORT
        }
        
        # Проверка наличия параметров подключения
        self._check_db_params()
    
    def _check_db_params(self):
        """Проверка параметров подключения к базе данных"""
        if not DB_HOST:
            print("ВНИМАНИЕ: Не указан DB_HOST, используется значение по умолчанию: localhost")
        
        if not DB_NAME:
            print("ВНИМАНИЕ: Не указан DB_NAME, используется значение по умолчанию: postgres")
        
        if not DB_SCHEMA:
            print("ВНИМАНИЕ: Не указан DB_SCHEMA, используется значение по умолчанию: resume_db")
        
        if not DB_USER:
            print("ВНИМАНИЕ: Не указан DB_USER, используется значение по умолчанию: postgres")
        
        if not DB_PASSWORD:
            print("ВНИМАНИЕ: DB_PASSWORD не указан")
    
    def _get_connection(self):
        """Получение соединения с базой данных"""
        conn = psycopg2.connect(**self.conn_params)
        # Устанавливаем схему по умолчанию
        cursor = conn.cursor()
        cursor.execute(f"SET search_path TO {DB_SCHEMA}")
        cursor.close()
        return conn
    
    def save_resume(self, resume_id: str, email: str, raw_text: str, metadata: Optional[Dict] = None, pdf_content: Optional[bytes] = None) -> bool:
        """
        Сохраняет сырое резюме в базу данных
        
        Args:
            resume_id: Идентификатор резюме
            email: Email пользователя
            raw_text: Исходный текст резюме
            metadata: Метаданные резюме
            pdf_content: Содержимое PDF-файла в бинарном формате
            
        Returns:
            True, если резюме успешно сохранено
        """
        query = f"""
        INSERT INTO {DB_SCHEMA}.resumes (id, email, raw_text, metadata, pdf_content)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (id) DO UPDATE
        SET email = EXCLUDED.email,
            raw_text = EXCLUDED.raw_text,
            metadata = EXCLUDED.metadata,
            pdf_content = EXCLUDED.pdf_content,
            created_at = CURRENT_TIMESTAMP
        """
        
        try:
            print(f"Сохранение резюме с ID {resume_id} для {email}")
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(query, (resume_id, email, raw_text, Json(metadata or {}), pdf_content))
            conn.commit()
            cursor.close()
            conn.close()
            print(f"Резюме с ID {resume_id} успешно сохранено")
            return True
        except Exception as e:
            print(f"Ошибка при сохранении резюме: {str(e)}")
            return False
    
    def save_normalized_resume(self, resume_id: str, normalized_data: Dict[str, Any]) -> bool:
        """
        Сохраняет нормализованные данные резюме в базу данных
        
        Args:
            resume_id: Идентификатор резюме
            normalized_data: Нормализованные данные резюме
            
        Returns:
            True, если данные успешно сохранены
        """
        query = f"""
        INSERT INTO {DB_SCHEMA}.normalized_resumes (
            id, name, email, phone, vacancy_name, languages, frameworks, education, work_experience
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO UPDATE
        SET name = EXCLUDED.name,
            email = EXCLUDED.email,
            phone = EXCLUDED.phone,
            vacancy_name = EXCLUDED.vacancy_name,
            languages = EXCLUDED.languages,
            frameworks = EXCLUDED.frameworks,
            education = EXCLUDED.education,
            work_experience = EXCLUDED.work_experience,
            created_at = CURRENT_TIMESTAMP
        """
        
        try:
            print(f"Сохранение нормализованных данных для резюме с ID {resume_id}")
            
            # Проверяем, существует ли резюме в базе данных
            check_query = f"""
            SELECT 1 FROM {DB_SCHEMA}.resumes WHERE id = %s
            """
            
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute(check_query, (resume_id,))
            if not cursor.fetchone():
                print(f"Ошибка: Резюме с ID {resume_id} не найдено в базе данных")
                cursor.close()
                conn.close()
                return False
                
            cursor.execute(query, (
                resume_id,
                normalized_data.get("name", ""),
                normalized_data.get("email", ""),
                normalized_data.get("phone", ""),
                normalized_data.get("vacancy_name", ""),
                Json(normalized_data.get("languages", [])),
                Json(normalized_data.get("frameworks", [])),
                Json(normalized_data.get("education", [])),
                Json(normalized_data.get("work_experience", []))
            ))
            conn.commit()
            cursor.close()
            conn.close()
            print(f"Нормализованные данные для резюме с ID {resume_id} успешно сохранены")
            return True
        except Exception as e:
            print(f"Ошибка при сохранении нормализованных данных: {str(e)}")
            return False
    
    def get_normalized_resume(self, resume_id: str) -> Optional[Dict[str, Any]]:
        """
        Получает нормализованные данные резюме
        
        Args:
            resume_id: Идентификатор резюме
            
        Returns:
            Нормализованные данные резюме или None, если резюме не найдено
        """
        query = f"""
        SELECT * FROM {DB_SCHEMA}.normalized_resumes
        WHERE id = %s
        """
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(query, (resume_id,))
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            return dict(result) if result else None
        except Exception as e:
            print(f"Ошибка при получении нормализованных данных: {str(e)}")
            return None
            
    def get_resume(self, resume_id: str) -> Optional[Tuple[str, Dict]]:
        """
        Получает резюме по идентификатору из базы данных
        
        Args:
            resume_id: Идентификатор резюме
            
        Returns:
            Кортеж (текст резюме, метаданные) или None, если резюме не найдено
        """
        query = f"""
        SELECT id, email, raw_text, metadata, created_at FROM {DB_SCHEMA}.resumes
        WHERE id = %s
        """
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(query, (resume_id,))
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if not result:
                return None, None
                
            record = dict(result)
            return record.get("raw_text", ""), record
        except Exception as e:
            print(f"Ошибка при получении резюме: {str(e)}")
            return None, None
            
    def get_resume_pdf(self, resume_id: str) -> Optional[bytes]:
        """
        Получает PDF-файл резюме по идентификатору
        
        Args:
            resume_id: Идентификатор резюме
            
        Returns:
            Содержимое PDF-файла в бинарном формате или None, если файл не найден
        """
        query = f"""
        SELECT pdf_content FROM {DB_SCHEMA}.resumes
        WHERE id = %s
        """
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(query, (resume_id,))
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            return result[0] if result and result[0] else None
        except Exception as e:
            print(f"Ошибка при получении PDF-файла резюме: {str(e)}")
            return None
            
    def get_resumes_by_email(self, email: str) -> List[Dict]:
        """
        Получает все резюме пользователя по email из базы данных
        
        Args:
            email: Email пользователя
            
        Returns:
            Список резюме пользователя
        """
        query = f"""
        SELECT id, email, metadata, created_at FROM {DB_SCHEMA}.resumes
        WHERE email = %s
        ORDER BY created_at DESC
        """
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(query, (email,))
            results = cursor.fetchall()
            cursor.close()
            conn.close()
            
            return [dict(r) for r in results] if results else []
        except Exception as e:
            print(f"Ошибка при получении резюме пользователя: {str(e)}")
            return []
            
    def save_vacancy(self, vacancy_id: str, title: str, company: str, description: str, 
                     url: str, original_id: Optional[str] = None, 
                     salary_from: Optional[int] = None, salary_to: Optional[int] = None,
                     currency: Optional[str] = None, experience: Optional[str] = None,
                     skills: Optional[List[str]] = None) -> bool:
        """
        Сохраняет вакансию в базу данных
        
        Args:
            vacancy_id: Идентификатор вакансии
            title: Название вакансии
            company: Название компании
            description: Описание вакансии
            url: URL вакансии
            original_id: Оригинальный ID вакансии на hh.ru
            salary_from: Минимальная зарплата
            salary_to: Максимальная зарплата
            currency: Валюта зарплаты
            experience: Опыт работы
            skills: Список требуемых навыков
            
        Returns:
            True, если вакансия успешно сохранена
        """
        query = f"""
        INSERT INTO {DB_SCHEMA}.vacancies (
            id, title, company, description, url, original_id, 
            salary_from, salary_to, currency, experience, skills
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO UPDATE
        SET title = EXCLUDED.title,
            company = EXCLUDED.company,
            description = EXCLUDED.description,
            url = EXCLUDED.url,
            original_id = EXCLUDED.original_id,
            salary_from = EXCLUDED.salary_from,
            salary_to = EXCLUDED.salary_to,
            currency = EXCLUDED.currency,
            experience = EXCLUDED.experience,
            skills = EXCLUDED.skills,
            created_at = CURRENT_TIMESTAMP
        """
        
        try:
            print(f"Сохранение вакансии с ID {vacancy_id} - {title}")
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(query, (
                vacancy_id,
                title,
                company,
                description,
                url,
                original_id,
                salary_from,
                salary_to,
                currency,
                experience,
                Json(skills or [])
            ))
            conn.commit()
            cursor.close()
            conn.close()
            print(f"Вакансия с ID {vacancy_id} успешно сохранена")
            return True
        except Exception as e:
            print(f"Ошибка при сохранении вакансии: {str(e)}")
            return False
    
    def get_vacancy(self, vacancy_id: str) -> Optional[Dict[str, Any]]:
        """
        Получает вакансию по идентификатору
        
        Args:
            vacancy_id: Идентификатор вакансии
            
        Returns:
            Данные о вакансии или None, если вакансия не найдена
        """
        query = f"""
        SELECT * FROM {DB_SCHEMA}.vacancies
        WHERE id = %s
        """
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(query, (vacancy_id,))
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            return dict(result) if result else None
        except Exception as e:
            print(f"Ошибка при получении вакансии: {str(e)}")
            return None
    
    def get_all_vacancies(self) -> List[Dict[str, Any]]:
        """
        Получает все вакансии из базы данных
        
        Returns:
            Список вакансий
        """
        query = f"""
        SELECT * FROM {DB_SCHEMA}.vacancies
        ORDER BY created_at DESC
        """
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(query)
            results = cursor.fetchall()
            cursor.close()
            conn.close()
            
            return [dict(r) for r in results] if results else []
        except Exception as e:
            print(f"Ошибка при получении всех вакансий: {str(e)}")
            return [] 