import re
import uuid
from datetime import datetime
from typing import List

from fastapi import APIRouter, HTTPException, File, UploadFile, Form, BackgroundTasks
from fastapi.responses import Response

from src.models.schemas import MatchRequest, MatchResult, ResumeVacancyMatchRequest, NormalizedResume, \
    ResumeNormalizationResponse, VacancyRequest, Vacancy, VacancyResponse, StoredResumeVacancyMatchRequest, \
    ResumeVacancyMatchResponse, ResumeVacancyFullMatchResponse, ResumeVacancyFullMatchRequest
from src.services.db_service import DBService
from src.services.getmatch_parser import GetmatchVacancyParser
from src.services.habr_parser import HabrVacancyParser
from src.services.matcher import ResumeVacancyMatcher
from src.services.normalizer import ResumeNormalizer
from src.services.vacancy_parser import VacancyParser
from src.utils.pdf_extractor import PDFExtractor

# Создание роутера FastAPI
router = APIRouter()

# Инициализация сервисов
matcher = ResumeVacancyMatcher()
db_service = DBService()
resume_normalizer = ResumeNormalizer()
vacancy_parser = VacancyParser()
habr_vacancy_parser = HabrVacancyParser()
getmatch_vacancy_parser = GetmatchVacancyParser()


# Валидация email
def is_valid_email(email: str):
    """Проверяет, является ли строка валидным email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


@router.post("/match", response_model=MatchResult, tags=["Матчинг"])
def match_vacancy_resume(request: MatchRequest):
    """
    Сопоставление резюме с вакансией
    
    - **vacancy_text**: Текст вакансии
    - **resume_text**: Текст резюме кандидата
    
    Возвращает список совпадающих навыков, список отсутствующих навыков,
    комментарий от языковой модели, оценку соответствия, плюсы, минусы и вердикт.
    """
    try:
        matched_skills, unmatched_skills, llm_comment, score, positives, negatives, verdict = matcher.match(
            request.vacancy_text, request.resume_text
        )

        return MatchResult(
            matched_skills=matched_skills,
            unmatched_skills=unmatched_skills,
            llm_comment=llm_comment,
            score=score,
            positives=positives,
            negatives=negatives,
            verdict=verdict
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload-resume", response_model=ResumeNormalizationResponse, tags=["Резюме"])
async def upload_resume(
        file: UploadFile = File(...),
        email: str = Form(...),
        background_tasks: BackgroundTasks = None
):
    """
    Загрузка резюме в формате PDF с нормализацией и сохранением в базу данных
    
    - **file**: PDF-файл с резюме
    - **email**: Email пользователя
    
    Возвращает идентификатор загруженного резюме и нормализованные данные.
    """
    # Проверка формата файла
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Только PDF-файлы принимаются")

    # Проверка email
    if not is_valid_email(email):
        raise HTTPException(status_code=400, detail="Некорректный формат email")

    try:
        # Чтение содержимого файла
        pdf_content = await file.read()

        # Извлечение текста из PDF
        resume_text = PDFExtractor.extract_text_from_bytes(pdf_content)

        if not resume_text or len(resume_text.strip()) < 50:
            raise HTTPException(
                status_code=400,
                detail="Не удалось извлечь достаточно текста из PDF. Возможно, файл пустой или защищен."
            )

        # Извлечение метаданных из PDF
        metadata, errors = PDFExtractor.get_metadata(pdf_content)

        if metadata:
            # Добавляем имя файла в метаданные
            metadata["filename"] = file.filename

        # Генерируем идентификатор и сохраняем резюме в базу данных
        resume_id = str(uuid.uuid4())

        # Сохранение сырого резюме и PDF-файла в базу данных
        save_success = db_service.save_resume(resume_id, email, resume_text, metadata, pdf_content)

        if not save_success:
            raise HTTPException(
                status_code=500,
                detail="Не удалось сохранить резюме в базу данных. Попробуйте позже."
            )

        # Нормализация резюме с помощью DeepSeek
        normalized_data = resume_normalizer.normalize_resume(resume_text, email)

        if not normalized_data:
            raise HTTPException(
                status_code=500,
                detail="Не удалось нормализовать резюме. Попробуйте позже."
            )

        # Сохранение нормализованных данных в базу данных
        normalized_save_success = db_service.save_normalized_resume(resume_id, normalized_data)

        if not normalized_save_success:
            raise HTTPException(
                status_code=500,
                detail="Резюме сохранено, но не удалось сохранить нормализованные данные. Попробуйте позже."
            )

        # Создаем объект нормализованного резюме
        normalized_resume = NormalizedResume(
            name=normalized_data.get("name", ""),
            email=normalized_data.get("email", ""),
            phone=normalized_data.get("phone", ""),
            vacancy_name=normalized_data.get("vacancy_name", ""),
            languages=normalized_data.get("languages", []),
            frameworks=normalized_data.get("frameworks", []),
            education=normalized_data.get("education", []),
            work_experience=normalized_data.get("work_experience", [])
        )

        # Создаем ответ
        response = ResumeNormalizationResponse(
            resume_id=resume_id,
            normalized_data=normalized_resume
        )

        # Если есть ошибки, добавляем их в ответ
        if errors:
            response.message = f"Резюме нормализовано и сохранено, но с предупреждениями: {', '.join(errors)}"

        return response

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при обработке файла: {str(e)}")


@router.post("/match-stored-resume", response_model=MatchResult, tags=["Матчинг"])
def match_stored_resume(request: ResumeVacancyMatchRequest):
    """
    Сопоставление ранее загруженного резюме с вакансией
    
    - **resume_id**: Идентификатор резюме
    - **vacancy_text**: Текст вакансии
    
    Возвращает результат сопоставления.
    """
    # Получаем резюме из базы данных
    resume_text, record = db_service.get_resume(request.resume_id)

    if not resume_text:
        raise HTTPException(status_code=404, detail=f"Резюме с ID {request.resume_id} не найдено")

    try:
        # Выполняем сопоставление
        matched_skills, unmatched_skills, llm_comment, score, positives, negatives, verdict = matcher.match(
            request.vacancy_text, resume_text
        )

        return MatchResult(
            matched_skills=matched_skills,
            unmatched_skills=unmatched_skills,
            llm_comment=llm_comment,
            score=score,
            positives=positives,
            negatives=negatives,
            verdict=verdict
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/resumes/{email}", tags=["Резюме"])
def get_user_resumes(email: str):
    """
    Получение списка резюме пользователя по email

    - **email**: Email пользователя

    Возвращает список резюме пользователя.
    """
    if not is_valid_email(email):
        raise HTTPException(status_code=400, detail="Некорректный формат email")

    # Получаем резюме из базы данных
    resumes = db_service.get_resumes_by_email(email)

    return {"email": email, "resumes": resumes}


@router.get("/normalized-resume/{resume_id}", response_model=NormalizedResume, tags=["Резюме"])
def get_normalized_resume(resume_id: str):
    """
    Получение нормализованных данных резюме

    - **resume_id**: Идентификатор резюме

    Возвращает нормализованные данные резюме.
    """
    # Получаем нормализованные данные из базы данных
    normalized_data = db_service.get_normalized_resume(resume_id)

    if not normalized_data:
        raise HTTPException(status_code=404, detail=f"Нормализованные данные для резюме с ID {resume_id} не найдены")

    # Создаем объект нормализованного резюме
    normalized_resume = NormalizedResume(
        name=normalized_data.get("name", ""),
        email=normalized_data.get("email", ""),
        phone=normalized_data.get("phone", ""),
        vacancy_name=normalized_data.get("vacancy_name", ""),
        languages=normalized_data.get("languages", []),
        frameworks=normalized_data.get("frameworks", []),
        education=normalized_data.get("education", []),
        work_experience=normalized_data.get("work_experience", [])
    )

    return normalized_resume


@router.get("/resume-pdf/{resume_id}", tags=["Резюме"])
def get_resume_pdf(resume_id: str):
    """
    Получение PDF-файла резюме по идентификатору

    - **resume_id**: Идентификатор резюме

    Возвращает файл резюме в формате PDF.
    """
    # Получаем PDF-файл из базы данных
    pdf_content = db_service.get_resume_pdf(resume_id)

    if not pdf_content:
        raise HTTPException(status_code=404, detail=f"PDF-файл для резюме с ID {resume_id} не найден")

    # Получаем метаданные резюме для определения имени файла
    _, record = db_service.get_resume(resume_id)

    # Определяем имя файла
    filename = "resume.pdf"
    if record and record.get("metadata") and record["metadata"].get("filename"):
        filename = record["metadata"]["filename"]

    # Возвращаем PDF-файл
    return Response(
        content=pdf_content,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )


@router.post("/parse-vacancy", response_model=VacancyResponse, tags=["Вакансии"])
def parse_vacancy(request: VacancyRequest):
    """
    Парсинг вакансии с hh.ru
    
    - **url**: URL вакансии на hh.ru
    
    Возвращает данные о вакансии.
    """
    # Парсим вакансию
    vacancy_data, error = vacancy_parser.parse_vacancy(request.url)

    if error:
        raise HTTPException(status_code=400, detail=error)

    if not vacancy_data:
        raise HTTPException(status_code=500, detail="Не удалось распарсить вакансию")

    # Создаем объект вакансии
    vacancy = Vacancy(
        id=vacancy_data.get("id"),
        title=vacancy_data.get("title"),
        company=vacancy_data.get("company"),
        description=vacancy_data.get("description"),
        salary_from=vacancy_data.get("salary_from"),
        salary_to=vacancy_data.get("salary_to"),
        currency=vacancy_data.get("currency"),
        experience=vacancy_data.get("experience"),
        skills=vacancy_data.get("skills", []),
        url=vacancy_data.get("url"),
        created_at=vacancy_data.get("created_at"),
        work_format=vacancy_data.get("work_format")
    )

    # Создаем ответ
    response = VacancyResponse(
        vacancy_id=vacancy_data.get("id"),
        vacancy=vacancy,
        status="success",
        message="Вакансия успешно загружена"
    )

    return response


@router.get("/vacancies", response_model=List[Vacancy], tags=["Вакансии"])
def get_all_vacancies():
    """
    Получение списка всех вакансий

    Возвращает список всех вакансий.
    """
    # Получаем вакансии из базы данных
    vacancies_data = db_service.get_all_vacancies()

    # Преобразуем в список объектов Vacancy
    vacancies = []
    for vacancy_data in vacancies_data:
        vacancy = Vacancy(
            id=vacancy_data.get("id"),
            title=vacancy_data.get("title"),
            company=vacancy_data.get("company"),
            description=vacancy_data.get("description"),
            salary_from=vacancy_data.get("salary_from"),
            salary_to=vacancy_data.get("salary_to"),
            currency=vacancy_data.get("currency"),
            experience=vacancy_data.get("experience"),
            skills=vacancy_data.get("skills", []),
            url=vacancy_data.get("url"),
            created_at=vacancy_data.get("created_at"),
            work_format=vacancy_data.get("work_format")
        )
        vacancies.append(vacancy)

    return vacancies


@router.get("/vacancy/{vacancy_id}", response_model=Vacancy, tags=["Вакансии"])
def get_vacancy(vacancy_id: str):
    """
    Получение вакансии по идентификатору

    - **vacancy_id**: Идентификатор вакансии

    Возвращает данные о вакансии.
    """
    # Получаем вакансию из базы данных
    vacancy_data = db_service.get_vacancy(vacancy_id)

    if not vacancy_data:
        raise HTTPException(status_code=404, detail=f"Вакансия с ID {vacancy_id} не найдена")

    # Создаем объект вакансии
    vacancy = Vacancy(
        id=vacancy_data.get("id"),
        title=vacancy_data.get("title"),
        company=vacancy_data.get("company"),
        description=vacancy_data.get("description"),
        salary_from=vacancy_data.get("salary_from"),
        salary_to=vacancy_data.get("salary_to"),
        currency=vacancy_data.get("currency"),
        experience=vacancy_data.get("experience"),
        skills=vacancy_data.get("skills", []),
        url=vacancy_data.get("url"),
        created_at=vacancy_data.get("created_at"),
        work_format=vacancy_data.get("work_format")
    )

    return vacancy


@router.post("/match-stored", response_model=ResumeVacancyMatchResponse, tags=["Матчинг"])
def match_stored_resume_with_vacancy(request: StoredResumeVacancyMatchRequest):
    """
    Сопоставление сохраненного резюме с сохраненной вакансией
    
    - **resume_id**: Идентификатор резюме
    - **vacancy_id**: Идентификатор вакансии
    
    Возвращает результат сопоставления и сохраняет его в базе данных.
    """
    # Получаем резюме из базы данных
    resume_text, resume_record = db_service.get_resume(request.resume_id)
    if not resume_text:
        raise HTTPException(status_code=404, detail=f"Резюме с ID {request.resume_id} не найдено")

    # Получаем вакансию из базы данных
    vacancy_data = db_service.get_vacancy(request.vacancy_id)
    if not vacancy_data:
        raise HTTPException(status_code=404, detail=f"Вакансия с ID {request.vacancy_id} не найдена")

    vacancy_text = vacancy_data.get("description", "")

    try:
        # Проверяем, есть ли уже результаты сопоставления в базе данных
        existing_match = db_service.get_resume_vacancy_match(request.resume_id, request.vacancy_id)
        if existing_match:
            # Возвращаем существующие результаты
            return ResumeVacancyMatchResponse(
                resume_id=request.resume_id,
                vacancy_id=request.vacancy_id,
                matched_skills=existing_match.get("matched_skills", []),
                unmatched_skills=existing_match.get("unmatched_skills", []),
                llm_comment=existing_match.get("llm_comment", ""),
                score=existing_match.get("score", 0.5),
                positives=existing_match.get("positives", []),
                negatives=existing_match.get("negatives", []),
                verdict=existing_match.get("verdict", ""),
                message="Результаты сопоставления получены из базы данных"
            )

        # Выполняем сопоставление
        matched_skills, unmatched_skills, llm_comment, score, positives, negatives, verdict = matcher.match(
            vacancy_text, resume_text
        )

        # Генерируем ID для сопоставления
        match_id = str(uuid.uuid4())

        # Сохраняем результаты в базе данных
        try:
            save_success = db_service.save_resume_vacancy_match(
                match_id=match_id,
                resume_id=request.resume_id,
                vacancy_id=request.vacancy_id,
                matched_skills=matched_skills,
                unmatched_skills=unmatched_skills,
                llm_comment=llm_comment,
                score=score,
                positives=positives,
                negatives=negatives,
                verdict=verdict
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка при сохранении результатов: {str(e)}"
            )

        if not save_success:
            raise HTTPException(
                status_code=500,
                detail="Не удалось сохранить результаты сопоставления в базу данных. Попробуйте позже."
            )

        # Возвращаем результаты
        return ResumeVacancyMatchResponse(
            resume_id=request.resume_id,
            vacancy_id=request.vacancy_id,
            matched_skills=matched_skills,
            unmatched_skills=unmatched_skills,
            llm_comment=llm_comment,
            score=score,
            positives=positives,
            negatives=negatives,
            verdict=verdict
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при сопоставлении: {str(e)}")


@router.get("/resume/{resume_id}/matches", response_model=List[ResumeVacancyMatchResponse], tags=["Матчинг"])
def get_resume_matches(resume_id: str):
    """
    Получение всех сопоставлений для конкретного резюме

    - **resume_id**: Идентификатор резюме

    Возвращает список всех сопоставлений резюме с вакансиями.
    """
    # Проверяем существование резюме
    resume_text, resume_record = db_service.get_resume(resume_id)
    if not resume_text:
        raise HTTPException(status_code=404, detail=f"Резюме с ID {resume_id} не найдено")

    try:
        # Получаем все сопоставления для резюме
        matches = db_service.get_resume_matches(resume_id)

        # Преобразуем результаты в формат ответа
        response_matches = []
        for match in matches:
            response_match = ResumeVacancyMatchResponse(
                resume_id=match.get("resume_id"),
                vacancy_id=match.get("vacancy_id"),
                matched_skills=match.get("matched_skills", []),
                unmatched_skills=match.get("unmatched_skills", []),
                llm_comment=match.get("llm_comment", ""),
                score=match.get("score", 0.5),
                positives=match.get("positives", []),
                negatives=match.get("negatives", []),
                verdict=match.get("verdict", "")
            )
            response_matches.append(response_match)

        return response_matches
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении сопоставлений: {str(e)}")


@router.get("/vacancy/{vacancy_id}/matches", response_model=List[ResumeVacancyMatchResponse], tags=["Матчинг"])
def get_vacancy_matches(vacancy_id: str):
    """
    Получение всех сопоставлений для конкретной вакансии

    - **vacancy_id**: Идентификатор вакансии

    Возвращает список всех сопоставлений вакансии с резюме.
    """
    # Проверяем существование вакансии
    vacancy_data = db_service.get_vacancy(vacancy_id)
    if not vacancy_data:
        raise HTTPException(status_code=404, detail=f"Вакансия с ID {vacancy_id} не найдена")

    try:
        # Получаем все сопоставления для вакансии
        matches = db_service.get_vacancy_matches(vacancy_id)

        # Преобразуем результаты в формат ответа
        response_matches = []
        for match in matches:
            response_match = ResumeVacancyMatchResponse(
                resume_id=match.get("resume_id"),
                vacancy_id=match.get("vacancy_id"),
                matched_skills=match.get("matched_skills", []),
                unmatched_skills=match.get("unmatched_skills", []),
                llm_comment=match.get("llm_comment", ""),
                score=match.get("score", 0.5),
                positives=match.get("positives", []),
                negatives=match.get("negatives", []),
                verdict=match.get("verdict", "")
            )
            response_matches.append(response_match)

        return response_matches
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении сопоставлений: {str(e)}")


@router.post("/parse-habr-vacancy", response_model=VacancyResponse, tags=["Вакансии"])
def parse_habr_vacancy(request: VacancyRequest):
    """
    Парсинг вакансии с career.habr.com
    
    - **url**: URL вакансии на career.habr.com
    
    Возвращает данные о вакансии в формате VacancyResponse.
    """
    vacancy_data, error = habr_vacancy_parser.parse_vacancy(request.url)

    if error:
        raise HTTPException(status_code=400, detail=error)

    if not vacancy_data:
        raise HTTPException(status_code=500, detail="Не удалось распарсить вакансию")

    vacancy = Vacancy(
        id=vacancy_data.get("id"),
        title=vacancy_data.get("title"),
        company=vacancy_data.get("company"),
        description=vacancy_data.get("description"),
        salary_from=vacancy_data.get("salary_from"),
        salary_to=vacancy_data.get("salary_to"),
        currency=vacancy_data.get("currency"),
        experience=vacancy_data.get("experience"),
        skills=vacancy_data.get("skills", []),
        url=vacancy_data.get("url"),
        created_at=vacancy_data.get("created_at"),
        work_format=vacancy_data.get("work_format")
    )

    response = VacancyResponse(
        vacancy_id=vacancy_data.get("id"),
        vacancy=vacancy,
        status="success",
        message="Вакансия успешно загружена"
    )

    return response


@router.post("/parse-getmatch-vacancy", response_model=VacancyResponse, tags=["Вакансии"])
def parse_getmatch_vacancy(request: VacancyRequest):
    """
    Парсинг вакансии с getmatch.ru
    
    - **url**: URL вакансии на getmatch.ru
    
    Возвращает данные о вакансии в формате VacancyResponse.
    """
    vacancy_data, error = getmatch_vacancy_parser.parse_vacancy(request.url)

    if error:
        raise HTTPException(status_code=400, detail=error)

    if not vacancy_data:
        raise HTTPException(status_code=500, detail="Не удалось распарсить вакансию")

    vacancy = Vacancy(
        id=vacancy_data.get("id"),
        title=vacancy_data.get("title"),
        company=vacancy_data.get("company"),
        description=vacancy_data.get("description"),
        salary_from=vacancy_data.get("salary_from"),
        salary_to=vacancy_data.get("salary_to"),
        currency=vacancy_data.get("currency"),
        experience=vacancy_data.get("experience"),
        skills=vacancy_data.get("skills", []),
        url=vacancy_data.get("url"),
        created_at=vacancy_data.get("created_at"),
        work_format=vacancy_data.get("work_format")
    )

    response = VacancyResponse(
        vacancy_id=vacancy_data.get("id"),
        vacancy=vacancy,
        status="success",
        message="Вакансия успешно загружена"
    )

    return response


@router.post("/match-full", response_model=ResumeVacancyFullMatchResponse, tags=["Матчинг"])
def match_full(request: ResumeVacancyFullMatchRequest):
    """
    Сопоставление резюме и вакансии (расширенный формат)

    - **resume**: объект с данными резюме
    - **vacancy**: объект с данными вакансии

    Возвращает расширенный результат сопоставления.
    """
    try:
        resume = request.resume
        vacancy = request.vacancy
        resume_id = resume.id
        vacancy_id = vacancy.id

        # Формируем словари только с нужными полями
        resume_dict = {
            "hardSkills": resume.hardSkills,
            "softSkills": resume.softSkills,
            "education": [e.dict() for e in resume.education],
            "workExperience": [w.dict() for w in resume.workExperience],
            "role": resume.role
        }
        vacancy_dict = {
            "title": vacancy.title,
            "description": vacancy.description,
            "requirements": vacancy.requirements,
            "company": vacancy.company,
            "responsibilities": vacancy.responsibilities,
            "skills": vacancy.skills,
            "salaryFrom": vacancy.salaryFrom,
            "salaryTo": vacancy.salaryTo,
            "experience": vacancy.experience,
            "formatWork": vacancy.formatWork
        }

        score, positives, negatives, verdict, comment, matched_skills, unmatched_skills, clarifying_questions = matcher.get_llm_analysis(
            resume_dict=resume_dict, vacancy_dict=vacancy_dict
        )

        created_at = datetime.utcnow().isoformat()

        return ResumeVacancyFullMatchResponse(
            id=1,
            resumeId=resume_id,
            vacancyId=vacancy_id,
            matchedSkills=matched_skills,
            unmatchedSkills=unmatched_skills,
            llmComment=comment,
            createdAt=created_at,
            score=score,
            positives=positives,
            negatives=negatives,
            verdict=verdict,
            clarifyingQuestions=clarifying_questions
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
