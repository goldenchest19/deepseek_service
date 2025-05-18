import re
import uuid
from typing import List
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup


class VacancyParser:
    """Сервис для парсинга вакансий с hh.ru"""

    def __init__(self):
        """
        Инициализация парсера вакансий
        """
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36'
        }

        # Список популярных технологий и навыков для поиска в описании
        self.common_skills = [
            "Java", "Python", "JavaScript", "TypeScript", "C++", "C#", "Go", "Ruby", "PHP", "Swift",
            "Kotlin", "Scala", "Rust", "SQL", "NoSQL", "MongoDB", "PostgreSQL", "MySQL", "Oracle",
            "Redis", "Cassandra", "Docker", "Kubernetes", "Git", "CI/CD", "Jenkins", "AWS", "Azure",
            "GCP", "Spring", "Spring Boot", "Django", "Flask", "React", "Angular", "Vue.js", "Node.js",
            "Express", "TensorFlow", "PyTorch", "Pandas", "NumPy", "Scikit-learn", "REST API", "GraphQL",
            "Kafka", "RabbitMQ", "Elasticsearch", "Agile", "Scrum", "Kanban", "Linux", "Unix", "WebFlux",
            "Microservices", "SOA", "DevOps", "SRE", "Nginx", "Apache", "JUnit", "TestNG", "Selenium",
            "Cypress", "Jest", "Mocha", "Jenkins", "TeamCity", "GitLab CI", "GitHub Actions", "Maven",
            "Gradle", "npm", "Webpack", "Babel", "ESLint", "Prettier", "Docker Compose", "Helm",
            "Terraform", "Ansible", "Puppet", "Chef", "Prometheus", "Grafana", "ELK Stack", "Splunk",
            "Datadog", "New Relic", "JIRA", "Confluence", "Bitbucket", "Trello", "Asana"
        ]

        # Список слов, которые не должны распознаваться как навыки
        self.non_skills = [
            "Сможешь", "Уже", "Умеешь", "Знаешь", "Любишь", "Читаешь", "Имеешь", "Слышал",
            "Понимаешь", "Разбираешься", "Владеешь", "Знание", "Опыт", "Навык", "Требуется",
            "Требования", "Необходимо", "Желательно", "Приветствуется", "Будет", "Плюсом",
            "Хорошо", "Отлично", "Быстро", "Качественно", "Своевременно", "Эффективно",
            "Команда", "Работа", "Проект", "Задача", "Решение", "Мы", "Вы", "Ты", "Я",
            "Компания", "Офис", "Сотрудник", "Коллега", "Руководитель", "Менеджер"
        ]

    def _clean_salary_str(self, salary_str: str):
        """
        Очищает строку с зарплатой от пробелов и других символов, конвертирует в число
        """
        # Удаляем все нецифровые символы (включая пробелы, неразрывные пробелы и т.д.)
        cleaned_str = ''.join(c for c in salary_str if c.isdigit())
        return int(cleaned_str) if cleaned_str else 0

    def _extract_currency(self, currency_text: str):
        """
        Извлекает валюту из строки, которая может содержать дополнительный текст
        """
        # Список возможных валют
        currencies = ["руб.", "USD", "EUR", "₽", "$", "€"]

        # Проверяем наличие известных валют в тексте
        for currency in currencies:
            if currency in currency_text:
                return currency

        # Если не нашли известную валюту, берем первое слово
        return currency_text.split()[0] if ' ' in currency_text else currency_text

    def _extract_skills_from_description(self, description: str):
        """
        Извлекает навыки из описания вакансии
        """
        # Найденные навыки
        found_skills = []

        # Ищем каждый навык в описании
        for skill in self.common_skills:
            # Добавляем границы слов, чтобы избежать частичных совпадений
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, description, re.IGNORECASE):
                # Для совпадения без учета регистра используем оригинальную форму навыка из списка
                if skill not in found_skills:
                    found_skills.append(skill)

        # Удаляем возможные дубликаты с разным регистром
        found_skills = self._normalize_skills(found_skills)

        return found_skills

    def _normalize_skills(self, skills: List[str]):
        """
        Нормализует список навыков, удаляя дубликаты и неподходящие слова
        """
        # Удаляем дубликаты (с учетом регистра)
        unique_skills = []
        lowercase_skills = set()

        for skill in skills:
            if skill.lower() not in lowercase_skills and skill not in self.non_skills:
                # Проверяем, является ли навык "настоящим" навыком из списка популярных
                is_common_skill = False
                for common_skill in self.common_skills:
                    if skill.lower() == common_skill.lower():
                        unique_skills.append(common_skill)  # Используем форму из списка популярных
                        is_common_skill = True
                        break

                # Если это не популярный навык, но и не из списка неподходящих слов, добавляем
                if not is_common_skill and len(skill) > 2:  # Проверяем чтобы длина была > 2 символов
                    unique_skills.append(skill)

                # Добавляем навык в множество обработанных (в нижнем регистре)
                lowercase_skills.add(skill.lower())

        # Удаляем варианты одного и того же навыка
        # Например, если есть "PostgreSQL" и "Postgresql", оставляем только "PostgreSQL"
        final_skills = []
        processed_lowercase = set()

        for skill in unique_skills:
            if skill.lower() not in processed_lowercase:
                # Проверка, есть ли навык в списке популярных с разным регистром
                found_in_common = False
                for common_skill in self.common_skills:
                    if skill.lower() == common_skill.lower():
                        final_skills.append(common_skill)
                        found_in_common = True
                        break

                if not found_in_common:
                    final_skills.append(skill)

                processed_lowercase.add(skill.lower())

        return final_skills

    def parse_vacancy(self, url: str):
        """
        Парсит вакансию по URL
        """
        # Проверка, что URL указывает на hh.ru
        parsed_url = urlparse(url)
        if 'hh.ru' not in parsed_url.netloc:
            return None, "URL должен указывать на вакансию с сайта hh.ru"

        try:
            # Получение HTML страницы
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()

            # Парсинг HTML
            soup = BeautifulSoup(response.text, 'html.parser')

            # Извлечение ID вакансии из URL
            vacancy_id_match = re.search(r'/vacancy/(\d+)', url)
            original_id = vacancy_id_match.group(1) if vacancy_id_match else None

            # Парсинг названия вакансии
            title_elem = soup.select_one('h1.bloko-header-section-1')
            title = title_elem.text.strip() if title_elem else "Неизвестная вакансия"

            # Парсинг названия компании (ищем только корректный блок)
            company_elem = soup.select_one('[data-qa="vacancy-company-name"] span, [data-qa="vacancy-company-name"] a')
            company = company_elem.text.strip() if company_elem else "Неизвестная компания"

            # Парсинг формата работы (удаленно, офис, гибрид и т.д.)
            work_format = None
            work_format_elem = soup.find(lambda tag: tag.name == 'p' and tag.text and ("удал" in tag.text.lower() or "офис" in tag.text.lower() or "гибрид" in tag.text.lower()))
            if work_format_elem:
                work_format = work_format_elem.text.strip()
            else:
                # Альтернативный способ: ищем по ключевым словам в описании
                description_elem = soup.select_one('[data-qa="vacancy-description"]')
                description_text = description_elem.text.lower() if description_elem else ""
                if "удал" in description_text:
                    work_format = "Удаленно"
                elif "офис" in description_text:
                    work_format = "В офисе"
                elif "гибрид" in description_text:
                    work_format = "Гибрид"

            # Парсинг зарплаты
            salary_elem = soup.select_one('[data-qa="vacancy-salary"] span, [data-qa="vacancy-salary"]')
            salary_text = salary_elem.text.strip() if salary_elem else ""

            salary_from = None
            salary_to = None
            currency = None

            if salary_text and salary_text != "з/п не указана":
                # Сначала ищем полный текст зарплаты и пытаемся определить валюту
                currency_match = re.search(r'(₽|\$|€|руб\.|USD|EUR)', salary_text)
                if currency_match:
                    currency = currency_match.group(1)

                # Удаляем фразы "до вычета налогов", "на руки", "за месяц" и т.д. перед парсингом
                cleaned_salary_text = re.sub(r'\s+(до вычета налогов|на руки|за месяц).*$','', salary_text)

                # Проверяем на диапазон с дефисом (например, "350 000 - 430 000 ₽")
                range_match = re.search(r'(\d+[\s\xa0]*\d*)\s*[-–—]\s*(\d+[\s\xa0]*\d*)', cleaned_salary_text)
                if range_match:
                    salary_from = self._clean_salary_str(range_match.group(1))
                    salary_to = self._clean_salary_str(range_match.group(2))
                else:
                    # Парсинг диапазона зарплаты с использованием "от до" (например, "от 100 000 до 150 000 руб.")
                    salary_match = re.search(r'от\s+(\d+[\s\xa0]*\d*)\s+до\s+(\d+[\s\xa0]*\d*)', cleaned_salary_text)
                    if salary_match:
                        salary_from = self._clean_salary_str(salary_match.group(1))
                        salary_to = self._clean_salary_str(salary_match.group(2))
                    else:
                        # Парсинг "от" зарплаты (например, "от 100 000 руб.")
                        salary_match = re.search(r'от\s+(\d+[\s\xa0]*\d*)', cleaned_salary_text)
                        if salary_match:
                            salary_from = self._clean_salary_str(salary_match.group(1))
                        else:
                            # Парсинг "до" зарплаты (например, "до 150 000 руб.")
                            salary_match = re.search(r'до\s+(\d+[\s\xa0]*\d*)', cleaned_salary_text)
                            if salary_match:
                                salary_to = self._clean_salary_str(salary_match.group(1))
                            else:
                                # Парсинг фиксированной зарплаты (например, "100 000 руб.")
                                salary_match = re.search(r'(\d+[\s\xa0]*\d*)', cleaned_salary_text)
                                if salary_match:
                                    salary_from = self._clean_salary_str(salary_match.group(1))
                                    salary_to = salary_from

                # Если валюта не найдена ранее, ищем в тексте
                if not currency:
                    for curr in ["₽", "$", "€", "руб.", "USD", "EUR"]:
                        if curr in cleaned_salary_text:
                            currency = curr
                            break

            # Парсинг опыта работы
            experience_elem = soup.select_one('[data-qa="vacancy-experience"]')
            experience = experience_elem.text.strip() if experience_elem else None

            # Парсинг описания вакансии
            description_elem = soup.select_one('[data-qa="vacancy-description"]')
            description = description_elem.text.strip() if description_elem else ""

            # Пытаемся найти навыки в блоке тегов
            skills_elems = soup.select('[data-qa="bloko-tag__text"]')
            skills = [skill.text.strip() for skill in skills_elems] if skills_elems else []

            # Если навыки не найдены через селектор тегов, извлекаем их из описания
            if not skills:
                skills = self._extract_skills_from_description(description)
            else:
                # Если навыки найдены через селектор, все равно нормализуем их
                skills = self._normalize_skills(skills)

            # Формирование результата
            vacancy_data = {
                "id": str(uuid.uuid4()),
                "title": title,
                "company": company,
                "description": description,
                "salary_from": salary_from,
                "salary_to": salary_to,
                "currency": currency,
                "experience": experience,
                "skills": skills,
                "url": url,
                "original_id": original_id,
                "work_format": work_format
            }

            return vacancy_data, None

        except requests.RequestException as e:
            return None, f"Ошибка при запросе к hh.ru: {str(e)}"
        except Exception as e:
            return None, f"Ошибка при парсинге вакансии: {str(e)}"
