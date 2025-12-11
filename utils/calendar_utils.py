"""
Утилиты для работы с календарями (ICS формат)
"""
from datetime import datetime, timedelta
import uuid


def generate_ics_event(title, description, start_date, start_time='09:00', duration_hours=1):
    """
    Генерация одного события в формате ICS
    
    Args:
        title: Название события
        description: Описание
        start_date: Дата начала (YYYY-MM-DD)
        start_time: Время начала (HH:MM)
        duration_hours: Длительность в часах
    
    Returns:
        str: ICS строка события
    """
    try:
        # Парсим дату и время
        dt_start = datetime.strptime(f"{start_date} {start_time}", '%Y-%m-%d %H:%M')
        dt_end = dt_start + timedelta(hours=duration_hours)
        
        # Форматируем для ICS
        dtstart = dt_start.strftime('%Y%m%dT%H%M%S')
        dtend = dt_end.strftime('%Y%m%dT%H%M%S')
        dtstamp = datetime.now().strftime('%Y%m%dT%H%M%SZ')
        uid = str(uuid.uuid4())
        
        # Очищаем текст от специальных символов
        title = title.replace('\n', ' ').replace('\r', '')
        description = description.replace('\n', '\\n').replace('\r', '')
        
        ics = f"""BEGIN:VEVENT
UID:{uid}
DTSTAMP:{dtstamp}
DTSTART:{dtstart}
DTEND:{dtend}
SUMMARY:{title}
DESCRIPTION:{description}
STATUS:CONFIRMED
SEQUENCE:0
END:VEVENT"""
        
        return ics
        
    except Exception as e:
        print(f"❌ Ошибка генерации ICS события: {e}")
        return ""


def generate_calendar_for_tests(tests):
    """
    Генерация ICS календаря для тестов
    
    Args:
        tests: Список объектов Test
    
    Returns:
        str: Полный ICS файл
    """
    ics_content = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Classmate//Test Calendar//EN
CALSCALE:GREGORIAN
METHOD:PUBLISH
X-WR-CALNAME:Classmate - Testi
X-WR-TIMEZONE:Europe/Riga
X-WR-CALDESC:Visi testi no Classmate sistēmas
"""
    
    for test in tests:
        title = f"{test.type} - {test.subject}"
        description = test.description or f"{test.type} priekšmetā {test.subject}"
        
        event = generate_ics_event(
            title=title,
            description=description,
            start_date=test.date,
            start_time=test.time or '09:00',
            duration_hours=2  # Предполагаем 2 часа для теста
        )
        
        if event:
            ics_content += "\n" + event + "\n"
    
    ics_content += "END:VCALENDAR"
    
    return ics_content


def generate_calendar_for_homework(homework_list):
    """
    Генерация ICS календаря для домашних заданий
    
    Args:
        homework_list: Список объектов Homework
    
    Returns:
        str: Полный ICS файл
    """
    ics_content = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Classmate//Homework Calendar//EN
CALSCALE:GREGORIAN
METHOD:PUBLISH
X-WR-CALNAME:Classmate - Mājasdarbi
X-WR-TIMEZONE:Europe/Riga
X-WR-CALDESC:Visi mājasdarbi no Classmate sistēmas
"""
    
    for hw in homework_list:
        title = f"Mājasdarbs: {hw.title}"
        description = f"{hw.subject} - {hw.description or hw.title}"
        
        event = generate_ics_event(
            title=title,
            description=description,
            start_date=hw.date,
            start_time=hw.time or '23:59',
            duration_hours=1
        )
        
        if event:
            ics_content += "\n" + event + "\n"
    
    ics_content += "END:VCALENDAR"
    
    return ics_content


def generate_calendar_for_all_work(tests, homework):
    """
    Генерация объединенного календаря
    
    Args:
        tests: Список тестов
        homework: Список домашних заданий
    
    Returns:
        str: Полный ICS файл
    """
    ics_content = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Classmate//All Work Calendar//EN
CALSCALE:GREGORIAN
METHOD:PUBLISH
X-WR-CALNAME:Classmate - Visi darbi
X-WR-TIMEZONE:Europe/Riga
X-WR-CALDESC:Visi testi un mājasdarbi no Classmate sistēmas
"""
    
    # Добавляем тесты
    for test in tests:
        title = f"📝 {test.type} - {test.subject}"
        description = test.description or f"{test.type} priekšmetā {test.subject}"
        
        event = generate_ics_event(
            title=title,
            description=description,
            start_date=test.date,
            start_time=test.time or '09:00',
            duration_hours=2
        )
        
        if event:
            ics_content += "\n" + event + "\n"
    
    # Добавляем домашние задания
    for hw in homework:
        title = f"📖 {hw.title}"
        description = f"{hw.subject} - {hw.description or hw.title}"
        
        event = generate_ics_event(
            title=title,
            description=description,
            start_date=hw.date,
            start_time=hw.time or '23:59',
            duration_hours=1
        )
        
        if event:
            ics_content += "\n" + event + "\n"
    
    ics_content += "END:VCALENDAR"
    
    return ics_content


def parse_ics_file(ics_content):
    """
    Парсинг ICS файла в список событий
    
    Args:
        ics_content: Содержимое ICS файла
    
    Returns:
        list: Список словарей с событиями
    """
    events = []
    
    try:
        # Простой парсинг (для более сложных случаев лучше использовать библиотеку icalendar)
        lines = ics_content.split('\n')
        current_event = {}
        in_event = False
        
        for line in lines:
            line = line.strip()
            
            if line == 'BEGIN:VEVENT':
                in_event = True
                current_event = {}
            
            elif line == 'END:VEVENT':
                if current_event:
                    events.append(current_event)
                in_event = False
            
            elif in_event and ':' in line:
                key, value = line.split(':', 1)
                
                if key == 'SUMMARY':
                    current_event['summary'] = value
                
                elif key == 'DESCRIPTION':
                    current_event['description'] = value.replace('\\n', '\n')
                
                elif key == 'DTSTART':
                    # Парсим дату (формат: 20240115T090000)
                    try:
                        if 'T' in value:
                            dt = datetime.strptime(value.split('Z')[0], '%Y%m%dT%H%M%S')
                            current_event['date'] = dt.strftime('%Y-%m-%d')
                            current_event['time'] = dt.strftime('%H:%M')
                        else:
                            dt = datetime.strptime(value, '%Y%m%d')
                            current_event['date'] = dt.strftime('%Y-%m-%d')
                            current_event['time'] = '00:00'
                    except:
                        pass
                
                elif key == 'LOCATION':
                    current_event['location'] = value
        
        # Пытаемся извлечь предмет из summary
        for event in events:
            summary = event.get('summary', '')
            
            # Пытаемся найти паттерн "Type - Subject"
            if ' - ' in summary:
                parts = summary.split(' - ', 1)
                event['type'] = parts[0].strip()
                event['subject'] = parts[1].strip()
            else:
                event['subject'] = summary
        
        return events
        
    except Exception as e:
        print(f"❌ Ошибка парсинга ICS: {e}")
        return []


def create_reminder_event(work_item, work_type, days_before=1):
    """
    Создание напоминания о работе
    
    Args:
        work_item: Тест или домашнее задание
        work_type: 'test' или 'homework'
        days_before: За сколько дней напомнить
    
    Returns:
        str: ICS событие-напоминание
    """
    try:
        # Парсим оригинальную дату
        dt_work = datetime.strptime(work_item.date, '%Y-%m-%d')
        
        # Вычисляем дату напоминания
        dt_reminder = dt_work - timedelta(days=days_before)
        
        if work_type == 'test':
            title = f"⏰ Atgādinājums: {work_item.type} - {work_item.subject}"
            description = f"Pēc {days_before} dienām būs {work_item.type} priekšmetā {work_item.subject}"
        else:
            title = f"⏰ Atgādinājums: {work_item.title}"
            description = f"Pēc {days_before} dienām jāiesniedz {work_item.title}"
        
        return generate_ics_event(
            title=title,
            description=description,
            start_date=dt_reminder.strftime('%Y-%m-%d'),
            start_time='08:00',
            duration_hours=0.5
        )
        
    except Exception as e:
        print(f"❌ Ошибка создания напоминания: {e}")
        return ""


def generate_weekly_calendar(start_date=None):
    """
    Генерация календаря на неделю
    
    Args:
        start_date: Дата начала недели (YYYY-MM-DD), по умолчанию - сегодня
    
    Returns:
        dict: Словарь {дата: [события]}
    """
    from models.test import Test
    from models.homework import Homework
    
    if not start_date:
        start_date = datetime.now()
    else:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
    
    end_date = start_date + timedelta(days=7)
    
    # Получаем все работы
    all_tests = Test.get_all()
    all_homework = Homework.get_all()
    
    # Группируем по датам
    weekly_calendar = {}
    
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        weekly_calendar[date_str] = {
            'tests': [],
            'homework': []
        }
        
        # Фильтруем работы на эту дату
        for test in all_tests:
            if test.date == date_str:
                weekly_calendar[date_str]['tests'].append(test)
        
        for hw in all_homework:
            if hw.date == date_str:
                weekly_calendar[date_str]['homework'].append(hw)
        
        current_date += timedelta(days=1)
    
    return weekly_calendar