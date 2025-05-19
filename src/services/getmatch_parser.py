import re
import uuid
import requests
from bs4 import BeautifulSoup

class GetmatchVacancyParser:
    """Сервис для парсинга вакансий с getmatch.ru"""

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36'
        }

    def parse_vacancy(self, url: str):
        if 'getmatch.ru' not in url:
            return None, "URL должен указывать на вакансию с getmatch.ru"
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            # ID вакансии
            vacancy_id_match = re.search(r'/vacancies/(\d+)', url)
            original_id = vacancy_id_match.group(1) if vacancy_id_match else None

            # Название вакансии
            title_elem = soup.find(['h1', 'h2'])
            title = title_elem.text.strip() if title_elem else "Неизвестная вакансия"

            # Название компании
            company = ""
            company_a = soup.find('a', href=re.compile(r'^/companies/'))
            if company_a:
                company = company_a.text.strip()
            if not company:
                company_elem = soup.find('div', string=re.compile(r'в\s+.+', re.IGNORECASE))
                if company_elem:
                    company = company_elem.text.replace('в ', '').strip()
            if not company:
                for tag in soup.find_all(['h2', 'h3', 'div']):
                    if tag.text and 'Иви' in tag.text:
                        company = tag.text.strip()
                        break
            if not company:
                company = "Неизвестная компания"

            # Описание вакансии
            description = ""
            desc_section = soup.find('section', class_='b-vacancy-description')
            if desc_section:
                parts = []
                for tag in desc_section.find_all(['h2', 'p', 'li'], recursive=True):
                    text = tag.get_text(separator=' ', strip=True)
                    if text:
                        if tag.name == 'h2':
                            parts.append(f"\n{text}\n")
                        elif tag.name == 'li':
                            parts.append(f"- {text}")
                        else:
                            parts.append(text)
                description = '\n'.join(parts).strip()
            else:
                # fallback: старый способ
                desc_blocks = []
                for block in soup.find_all(['div', 'section']):
                    if block.text and 'В команде' in block.text:
                        desc_blocks.append(block.text.strip())
                    if block.text and 'О компании' in block.text:
                        desc_blocks.append(block.text.strip())
                if desc_blocks:
                    description = '\n\n'.join(desc_blocks)
                else:
                    main_block = soup.find('main')
                    if main_block:
                        description = main_block.text.strip()

            # Формат работы
            work_format = None
            location_elem = soup.find(string=re.compile(r'офис|гибрид|удал', re.IGNORECASE))
            if location_elem:
                text = location_elem.lower()
                if 'удал' in text:
                    work_format = 'Удаленно'
                elif 'офис' in text and 'гибрид' in text:
                    work_format = 'Гибрид'
                elif 'офис' in text:
                    work_format = 'В офисе'
                elif 'гибрид' in text:
                    work_format = 'Гибрид'

            # Зарплата
            salary_from = None
            salary_to = None
            currency = None
            salary_h3 = None
            for h3 in soup.find_all('h3'):
                if h3.text and re.search(r'(₽|руб|usd|eur|доллар|евро)', h3.text, re.IGNORECASE):
                    salary_h3 = h3
                    break
            if salary_h3:
                salary_text = salary_h3.text.strip()
                range_match = re.search(r'(\d+[\s\xa0]*\d*)\s*[–—-]\s*(\d+[\s\xa0]*\d*)', salary_text)
                if range_match:
                    salary_from = int(range_match.group(1).replace(' ', '').replace('\xa0', ''))
                    salary_to = int(range_match.group(2).replace(' ', '').replace('\xa0', ''))
                else:
                    from_match = re.search(r'от\s*(\d+[\s\xa0]*\d*)', salary_text)
                    if from_match:
                        salary_from = int(from_match.group(1).replace(' ', '').replace('\xa0', ''))
                    to_match = re.search(r'до\s*(\d+[\s\xa0]*\d*)', salary_text)
                    if to_match:
                        salary_to = int(to_match.group(1).replace(' ', '').replace('\xa0', ''))
                if '₽' in salary_text or 'руб' in salary_text:
                    currency = 'RUB'
                elif '$' in salary_text or 'usd' in salary_text:
                    currency = 'USD'
                elif '€' in salary_text or 'eur' in salary_text:
                    currency = 'EUR'
            else:
                # fallback: старый способ
                salary_elem = soup.find(string=re.compile(r'руб|₽|usd|eur|доллар|евро', re.IGNORECASE))
                if salary_elem:
                    salary_text = salary_elem
                    range_match = re.search(r'(\d+[\s\xa0]*\d*)\s*[–-]\s*(\d+[\s\xa0]*\d*)', salary_text)
                    if range_match:
                        salary_from = int(range_match.group(1).replace(' ', '').replace('\xa0', ''))
                        salary_to = int(range_match.group(2).replace(' ', '').replace('\xa0', ''))
                    else:
                        from_match = re.search(r'от\s*(\d+[\s\xa0]*\d*)', salary_text)
                        if from_match:
                            salary_from = int(from_match.group(1).replace(' ', '').replace('\xa0', ''))
                        to_match = re.search(r'до\s*(\d+[\s\xa0]*\d*)', salary_text)
                        if to_match:
                            salary_to = int(to_match.group(1).replace(' ', '').replace('\xa0', ''))
                    if '₽' in salary_text or 'руб' in salary_text:
                        currency = 'RUB'
                    elif '$' in salary_text or 'usd' in salary_text:
                        currency = 'USD'
                    elif '€' in salary_text or 'eur' in salary_text:
                        currency = 'EUR'

            # Опыт работы
            experience = None
            exp_row = None
            for row in soup.find_all('div', class_='row'):
                term = row.find('div', class_='b-term')
                if term and 'требуемый опыт' in term.text.lower():
                    value = row.find('div', class_='b-value')
                    if value:
                        experience = value.text.strip()
                        break
            if not experience:
                exp_elem = soup.find(string=re.compile(r'опыт', re.IGNORECASE))
                if exp_elem:
                    exp_match = re.search(r'(\d+\+?)\s*лет', exp_elem)
                    if exp_match:
                        experience = exp_match.group(1) + ' лет'

            # Навыки (skills) из блока 'Технологии/инструменты'
            skills = []
            tech_block = None
            for h in soup.find_all(['h2', 'h3']):
                if h.text and 'Технологии' in h.text:
                    # ищем следующий ul, div или span
                    next_sib = h.find_next_sibling()
                    while next_sib and next_sib.name in ['br', 'hr']:
                        next_sib = next_sib.find_next_sibling()
                    if next_sib:
                        tech_block = next_sib
                        break
            if tech_block:
                for tag in tech_block.find_all(['span', 'a']):
                    skill = tag.text.strip()
                    if skill:
                        skills.append(skill)
            # fallback: ищем по ключевым словам
            if not skills:
                tech_text = ''
                for tag in soup.find_all(['div', 'section', 'span']):
                    if tag.text and 'Python' in tag.text:
                        tech_text = tag.text
                        break
                if tech_text:
                    for s in re.split(r'[•,\n]', tech_text):
                        skill = s.strip()
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
            return None, f"Ошибка при запросе к getmatch.ru: {str(e)}"
        except Exception as e:
            return None, f"Ошибка при парсинге вакансии: {str(e)}" 