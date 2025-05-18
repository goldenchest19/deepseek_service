import re
import uuid
import requests
from bs4 import BeautifulSoup

class HabrVacancyParser:
    """Сервис для парсинга вакансий с career.habr.com"""

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36'
        }

    def parse_vacancy(self, url: str):
        if 'career.habr.com' not in url:
            return None, "URL должен указывать на вакансию с career.habr.com"
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            # ID вакансии
            vacancy_id_match = re.search(r'/vacancies/(\d+)', url)
            original_id = vacancy_id_match.group(1) if vacancy_id_match else None

            # Название вакансии
            title_elem = soup.find('h1')
            title = title_elem.text.strip() if title_elem else "Неизвестная вакансия"

            # Название компании
            company_elem = soup.find('div', class_='company_name')
            if not company_elem:
                company_elem = soup.find('div', class_='company-header__name')
            company = company_elem.text.strip() if company_elem else "Неизвестная компания"

            # Описание вакансии
            description_elem = soup.find('div', class_='vacancy-description__text')
            if not description_elem:
                description_elem = soup.find('div', class_='vacancy-description')
            description = description_elem.text.strip() if description_elem else ""

            # Формат работы
            work_format = None
            location_elem = soup.find('div', class_='vacancy-header__location')
            if location_elem:
                location_text = location_elem.text.lower()
                if 'удал' in location_text:
                    work_format = 'Удаленно'
                elif 'офис' in location_text:
                    work_format = 'В офисе'
                elif 'гибрид' in location_text:
                    work_format = 'Гибрид'
                else:
                    work_format = location_elem.text.strip()
            # Альтернатива: ищем по ключевым словам в описании
            if not work_format and description:
                desc_lower = description.lower()
                if 'удал' in desc_lower:
                    work_format = 'Удаленно'
                elif 'офис' in desc_lower:
                    work_format = 'В офисе'
                elif 'гибрид' in desc_lower:
                    work_format = 'Гибрид'

            # Зарплата
            salary_from = None
            salary_to = None
            currency = None
            salary_elem = soup.find('div', class_='basic-salary')
            if salary_elem:
                salary_text = salary_elem.text.strip()
                # Пример: "от 400 000 ₽"
                only_from_match = re.search(r'от\s*(\d+[\s\xa0]*\d*)', salary_text)
                range_match = re.search(r'от\s*(\d+[\s\xa0]*\d*)\s*до\s*(\d+[\s\xa0]*\d*)', salary_text)
                if range_match:
                    salary_from = int(range_match.group(1).replace(' ', '').replace('\xa0', ''))
                    salary_to = int(range_match.group(2).replace(' ', '').replace('\xa0', ''))
                elif only_from_match:
                    salary_from = int(only_from_match.group(1).replace(' ', '').replace('\xa0', ''))
                    salary_to = None
                # Валюта
                if '₽' in salary_text or 'руб' in salary_text:
                    currency = 'RUB'
                elif '$' in salary_text:
                    currency = 'USD'
                elif '€' in salary_text:
                    currency = 'EUR'

            # Опыт работы
            experience = None
            exp_elem = soup.find('div', class_='vacancy-description__skills')
            if exp_elem:
                exp_text = exp_elem.text.lower()
                exp_match = re.search(r'(\d+\+?)\s*год', exp_text)
                if exp_match:
                    experience = exp_match.group(1) + ' лет'

            # Навыки (только из блока требований)
            skills = []
            # Новый способ: ищем блок <h2 class="content-section__title">Требования</h2> и следующий span.inline-list
            req_title = soup.find('h2', class_='content-section__title', string=lambda t: t and 'требования' in t.lower())
            if req_title:
                parent_section = req_title.find_parent('div', class_='content-section')
                if parent_section:
                    inline_list = parent_section.find('span', class_='inline-list')
                    if inline_list:
                        for a in inline_list.find_all('a', class_='link-comp'):
                            skill = a.text.strip()
                            if skill:
                                skills.append(skill)
            # Если не нашли, fallback: старый способ
            if not skills:
                # Ищем блок с требованиями (например, заголовок или div с текстом 'Требования')
                req_block = None
                for h in soup.find_all(['h2', 'h3', 'strong']):
                    if h.text.strip().lower().startswith('требования'):
                        next_sib = h.find_next_sibling()
                        if next_sib and next_sib.name in ['ul', 'ol']:
                            req_block = next_sib
                            break
                        if next_sib and next_sib.name == 'div':
                            req_block = next_sib
                            break
                if req_block and req_block.name in ['ul', 'ol']:
                    for li in req_block.find_all('li'):
                        skill = li.text.strip()
                        if skill:
                            skills.append(skill)
                elif req_block and req_block.name == 'div':
                    for p in req_block.find_all(['p', 'li']):
                        skill = p.text.strip()
                        if skill:
                            skills.append(skill)
            # Если не нашли, fallback: ищем по ключевым словам в описании
            if not skills and description:
                req_match = re.search(r'Требования[\s:]*([\s\S]+?)(?:\n\n|\n\s*\*|\n\s*—|\n\s*•|\n\s*\-|\n\s*\d+\.|\n\s*\w+\s*\:|\n\s*Ожидания|\n\s*Обязанности|$)', description, re.IGNORECASE)
                if req_match:
                    for line in req_match.group(1).split('\n'):
                        skill = line.strip('•*-—•').strip()
                        if skill:
                            skills.append(skill)

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
            return None, f"Ошибка при запросе к career.habr.com: {str(e)}"
        except Exception as e:
            return None, f"Ошибка при парсинге вакансии: {str(e)}" 