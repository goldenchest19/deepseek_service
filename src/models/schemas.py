from typing import List, Dict, Optional, Any
from pydantic import BaseModel, EmailStr
from datetime import date


class MatchRequest(BaseModel):
    """Запрос на сопоставление резюме и вакансии"""
    vacancy_text: str
    resume_text: str


class MatchResult(BaseModel):
    """Результат сопоставления резюме и вакансии"""
    matched_skills: List[str]
    unmatched_skills: List[str]
    tfidf_score: float
    llm_comment: str


class ResumeUploadResponse(BaseModel):
    """Ответ на загрузку резюме"""
    resume_id: str
    email: EmailStr
    extracted_text_length: int
    metadata: Dict = {}
    status: str = "success"
    message: str = "Резюме успешно загружено"


class ResumeVacancyMatchRequest(BaseModel):
    """Запрос на сопоставление загруженного резюме с вакансией"""
    resume_id: str
    vacancy_text: str


class Education(BaseModel):
    """Модель образования"""
    degree: str
    direction: str
    specialty: str


class WorkExperience(BaseModel):
    """Модель опыта работы"""
    start_date: str
    end_date: Optional[str] = None
    company_name: str
    achievements: List[str] = []
    technologies: List[str] = []


class NormalizedResume(BaseModel):
    """Модель нормализованного резюме"""
    name: str
    email: str
    phone: Optional[str] = None
    vacancy_name: Optional[str] = None
    languages: List[str] = []
    frameworks: List[str] = []
    education: List[Education] = []
    work_experience: List[WorkExperience] = []


class ResumeNormalizationResponse(BaseModel):
    """Ответ на нормализацию резюме"""
    resume_id: str
    normalized_data: NormalizedResume
    status: str = "success"
    message: str = "Резюме успешно нормализовано и сохранено"


class VacancyRequest(BaseModel):
    """Запрос на парсинг вакансии с hh.ru"""
    url: str


class Vacancy(BaseModel):
    """Модель вакансии"""
    id: str
    title: str
    company: str
    description: str
    salary_from: Optional[int] = None
    salary_to: Optional[int] = None
    currency: Optional[str] = None
    experience: Optional[str] = None
    skills: List[str] = []
    url: str
    created_at: Optional[str] = None


class VacancyResponse(BaseModel):
    """Ответ на запрос парсинга вакансии"""
    vacancy_id: str
    vacancy: Vacancy
    status: str = "success"
    message: str = "Вакансия успешно загружена и сохранена" 