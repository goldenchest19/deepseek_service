from typing import List, Dict, Optional

from pydantic import BaseModel, EmailStr


class MatchRequest(BaseModel):
    """Запрос на сопоставление резюме и вакансии"""
    vacancy_text: str
    resume_text: str


class MatchResult(BaseModel):
    """Результат сопоставления резюме и вакансии"""
    matched_skills: List[str]
    unmatched_skills: List[str]
    llm_comment: str
    score: float
    positives: List[str]
    negatives: List[str]
    verdict: str


class ResumeVacancyMatchRequest(BaseModel):
    """Запрос на сопоставление загруженного резюме с вакансией"""
    resume_id: str
    vacancy_text: str


class StoredResumeVacancyMatchRequest(BaseModel):
    """Запрос на сопоставление сохраненного резюме с сохраненной вакансией"""
    resume_id: str
    vacancy_id: str


class ResumeVacancyMatchResponse(BaseModel):
    """Ответ на запрос сопоставления резюме и вакансии"""
    resume_id: str
    vacancy_id: str
    matched_skills: List[str]
    unmatched_skills: List[str]
    llm_comment: str
    score: float
    positives: List[str]
    negatives: List[str]
    verdict: str
    status: str = "success"
    message: str = "Сопоставление выполнено успешно"


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
    work_format: Optional[str] = None  # Формат работы (удаленно, офис, гибрид и т.д.)


class VacancyResponse(BaseModel):
    """Ответ на запрос парсинга вакансии"""
    vacancy_id: str
    vacancy: Vacancy
    status: str = "success"
    message: str = "Вакансия успешно загружена и сохранена"


class EducationDTO(BaseModel):
    degree: str
    direction: str
    specialty: str


class WorkExperienceDTO(BaseModel):
    end_date: str
    start_date: str
    achievements: List[str]
    company_name: str
    technologies: List[str]


class ResumeDTO(BaseModel):
    id: int
    email: str
    name: str
    phone: str
    role: str
    hardSkills: List[str]
    softSkills: List[str]
    education: List[EducationDTO]
    workExperience: List[WorkExperienceDTO]


class VacancyDTO(BaseModel):
    id: int
    title: str
    description: str
    requirements: Optional[str]
    company: str
    responsibilities: Optional[str]
    skills: List[str]
    salaryFrom: Optional[int]
    salaryTo: Optional[int]
    location: Optional[str]
    source: str
    createdAt: str
    currency: str
    experience: str
    url: str
    originalId: Optional[int]
    status: str
    formatWork: str


class ResumeVacancyFullMatchRequest(BaseModel):
    resume: ResumeDTO
    vacancy: VacancyDTO


class ResumeVacancyFullMatchResponse(BaseModel):
    """Расширенный ответ на сопоставление резюме и вакансии"""
    id: int
    resumeId: int
    vacancyId: int
    matchedSkills: List[str]
    unmatchedSkills: List[str]
    llmComment: str
    createdAt: str
    score: float
    positives: List[str]
    negatives: List[str]
    verdict: str
    clarifyingQuestions: List[str] = []
