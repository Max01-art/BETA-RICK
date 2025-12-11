"""
RTU расписания скрапер
Загрузка расписания с сайта nodarbibas.rtu.lv
"""
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re


class RTUScraper:
    """Класс для парсинга расписания RTU"""
    
    def __init__(self, base_url='https://nodarbibas.rtu.lv'):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def get_schedule(self, program_id, course_id, semester_id=28):
        """
        Получить расписание для программы и курса
        
        Args:
            program_id: ID программы обучения
            course_id: Номер курса (1-4)
            semester_id: ID семестра
        
        Returns:
            list: Список занятий
        """
        try:
            url = f"{self.base_url}/lv/schedule/{semester_id}/{program_id}/{course_id}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            lessons = self._parse_schedule(soup)
            
            return lessons
            
        except Exception as e:
            print(f"❌ Ошибка получения расписания RTU: {e}")
            return []
    
    def _parse_schedule(self, soup):
        """
        Парсинг HTML страницы с расписанием
        
        Args:
            soup: BeautifulSoup объект
        
        Returns:
            list: Список занятий
        """
        lessons = []
        
        try:
            # Ищем таблицу с расписанием
            schedule_table = soup.find('table', class_='schedule-table')
            
            if not schedule_table:
                print("⚠️ Таблица расписания не найдена")
                return []
            
            # Парсим строки
            rows = schedule_table.find_all('tr')
            
            current_date = None
            
            for row in rows:
                # Проверяем дату
                date_cell = row.find('td', class_='date-cell')
                if date_cell:
                    current_date = self._parse_date(date_cell.get_text(strip=True))
                
                # Парсим занятие
                lesson_cells = row.find_all('td', class_='lesson-cell')
                
                for cell in lesson_cells:
                    lesson = self._parse_lesson_cell(cell, current_date)
                    if lesson:
                        lessons.append(lesson)
            
            return lessons
            
        except Exception as e:
            print(f"❌ Ошибка парсинга расписания: {e}")
            return []
    
    def _parse_lesson_cell(self, cell, date):
        """
        Парсинг ячейки с занятием
        
        Args:
            cell: BeautifulSoup элемент ячейки
            date: Дата занятия
        
        Returns:
            dict: Данные о занятии
        """
        try:
            # Время
            time_elem = cell.find(class_='lesson-time')
            time = time_elem.get_text(strip=True) if time_elem else ''
            
            # Название предмета
            subject_elem = cell.find(class_='lesson-subject')
            subject = subject_elem.get_text(strip=True) if subject_elem else ''
            
            # Тип занятия (лекция, практика и т.д.)
            type_elem = cell.find(class_='lesson-type')
            lesson_type = type_elem.get_text(strip=True) if type_elem else ''
            
            # Преподаватель
            teacher_elem = cell.find(class_='lesson-teacher')
            teacher = teacher_elem.get_text(strip=True) if teacher_elem else ''
            
            # Аудитория
            room_elem = cell.find(class_='lesson-room')
            room = room_elem.get_text(strip=True) if room_elem else ''
            
            if subject:
                return {
                    'date': date,
                    'time': time,
                    'subject': subject,
                    'type': lesson_type,
                    'teacher': teacher,
                    'room': room
                }
            
            return None
            
        except Exception as e:
            print(f"❌ Ошибка парсинга ячейки: {e}")
            return None
    
    def _parse_date(self, date_str):
        """
        Парсинг строки с датой
        
        Args:
            date_str: Строка с датой
        
        Returns:
            str: Дата в формате YYYY-MM-DD
        """
        try:
            # Примеры форматов: "Pirmdiena, 15.01.2024", "15.01.2024"
            
            # Убираем день недели
            date_str = re.sub(r'[A-Za-zāčēģīķļņšūžĀČĒĢĪĶĻŅŠŪŽ]+,\s*', '', date_str)
            
            # Парсим дату
            date = datetime.strptime(date_str.strip(), '%d.%m.%Y')
            return date.strftime('%Y-%m-%d')
            
        except Exception as e:
            print(f"❌ Ошибка парсинга даты '{date_str}': {e}")
            return datetime.now().strftime('%Y-%m-%d')
    
    def get_exams(self, program_id, course_id, semester_id=28):
        """
        Получить расписание экзаменов
        
        Args:
            program_id: ID программы обучения
            course_id: Номер курса
            semester_id: ID семестра
        
        Returns:
            list: Список экзаменов
        """
        try:
            url = f"{self.base_url}/lv/exams/{semester_id}/{program_id}/{course_id}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            exams = self._parse_exams(soup)
            
            return exams
            
        except Exception as e:
            print(f"❌ Ошибка получения экзаменов RTU: {e}")
            return []
    
    def _parse_exams(self, soup):
        """
        Парсинг страницы с экзаменами
        
        Args:
            soup: BeautifulSoup объект
        
        Returns:
            list: Список экзаменов
        """
        exams = []
        
        try:
            exam_rows = soup.find_all('tr', class_='exam-row')
            
            for row in exam_rows:
                # Дата
                date_cell = row.find('td', class_='exam-date')
                date_str = date_cell.get_text(strip=True) if date_cell else ''
                
                # Время
                time_cell = row.find('td', class_='exam-time')
                time_str = time_cell.get_text(strip=True) if time_cell else ''
                
                # Предмет
                subject_cell = row.find('td', class_='exam-subject')
                subject = subject_cell.get_text(strip=True) if subject_cell else ''
                
                # Тип (экзамен, зачет)
                type_cell = row.find('td', class_='exam-type')
                exam_type = type_cell.get_text(strip=True) if type_cell else 'Eksāmens'
                
                # Аудитория
                room_cell = row.find('td', class_='exam-room')
                room = room_cell.get_text(strip=True) if room_cell else ''
                
                if subject and date_str:
                    exams.append({
                        'date': self._parse_date(date_str),
                        'time': time_str or '09:00',
                        'subject': subject,
                        'type': exam_type,
                        'room': room
                    })
            
            return exams
            
        except Exception as e:
            print(f"❌ Ошибка парсинга экзаменов: {e}")
            return []
    
    def import_to_database(self, lessons, import_type='schedule'):
        """
        Импорт данных в базу данных
        
        Args:
            lessons: Список занятий/экзаменов
            import_type: Тип импорта ('schedule' или 'exams')
        
        Returns:
            dict: Статистика импорта
        """
        from models.test import Test
        from models.subject import Subject
        
        imported = 0
        errors = 0
        
        for lesson in lessons:
            try:
                # Создаем/обновляем предмет
                subject = Subject.get_by_name(lesson['subject'])
                if not subject:
                    subject = Subject(name=lesson['subject'])
                    subject.save()
                
                # Создаем тест/занятие
                if import_type == 'exams':
                    test = Test(
                        subject=lesson['subject'],
                        type=lesson.get('type', 'Eksāmens'),
                        date=lesson['date'],
                        time=lesson.get('time', '09:00'),
                        description=f"Auditorija: {lesson.get('room', '')}"
                    )
                    test.save()
                    imported += 1
                
            except Exception as e:
                print(f"❌ Ошибка импорта: {e}")
                errors += 1
        
        return {
            'imported': imported,
            'errors': errors,
            'total': len(lessons)
        }


def scrape_rtu_schedule(program_id=1393, course_id=1, semester_id=28):
    """
    Вспомогательная функция для быстрого скрапинга
    
    Args:
        program_id: ID программы
        course_id: Курс
        semester_id: ID семестра
    
    Returns:
        list: Список занятий
    """
    scraper = RTUScraper()
    return scraper.get_schedule(program_id, course_id, semester_id)


def scrape_rtu_exams(program_id=1393, course_id=1, semester_id=28):
    """
    Вспомогательная функция для получения экзаменов
    
    Args:
        program_id: ID программы
        course_id: Курс
        semester_id: ID семестра
    
    Returns:
        list: Список экзаменов
    """
    scraper = RTUScraper()
    return scraper.get_exams(program_id, course_id, semester_id)