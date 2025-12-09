"""
Утилиты для работы с календарями (.ics файлы)
"""
from datetime import datetime


def generate_calendar_for_work(work, work_type='test'):
    """
    Генерирует .ics файл для работы
    
    Args:
        work: Словарь с данными работы
        work_type: Тип работы ('test' или 'homework')
    
    Returns:
        str: Содержимое .ics файла
    """
    work_id = work.get('id', 0)
    subject = work.get('subject', 'Unknown')
    work_title = work.get('type', work.get('title', 'Work'))
    date = work.get('date', datetime.now().strftime('%Y-%m-%d'))
    time = work.get('time', '23:59')
    description = work.get('description', '')
    
    # Создаем уникальный ID события
    event_id = f"{work_type}_{work_id}@classmate-system"
    
    # Форматируем дату для .ics
    date_str = date.replace('-', '')  # YYYYMMDD
    time_str = time.replace(':', '')   # HHMM
    
    # Дата и время начала
    dtstart = f"{date_str}T{time_str}00"
    
    # Дата и время окончания (добавляем 1 час)
    end_hour = int(time[:2]) + 1
    if end_hour >= 24:
        end_hour = 23
    dtend = f"{date_str}T{end_hour:02d}{time_str[2:]}00"
    
    # Текущая дата для DTSTAMP
    dtstamp = datetime.now().strftime('%Y%m%dT%H%M%SZ')
    
    # Генерируем .ics контент
    ical_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Classmate System//Work Calendar//EN
CALSCALE:GREGORIAN
METHOD:PUBLISH
BEGIN:VEVENT
UID:{event_id}
DTSTAMP:{dtstamp}
DTSTART:{dtstart}
DTEND:{dtend}
SUMMARY:{subject} - {work_title}
DESCRIPTION:{description}
LOCATION:Skola
STATUS:CONFIRMED
SEQUENCE:0
BEGIN:VALARM
TRIGGER:-PT24H
ACTION:DISPLAY
DESCRIPTION:Reminder: {subject} - {work_title}
END:VALARM
END:VEVENT
END:VCALENDAR"""
    
    return ical_content


def generate_calendar_for_all_work(tests, homework):
    """
    Генерирует .ics файл для всех работ
    
    Args:
        tests: Список тестов
        homework: Список домашних заданий
    
    Returns:
        str: Содержимое .ics файла
    """
    ical_events = []
    
    # Заголовок календаря
    ical_events.append("BEGIN:VCALENDAR")
    ical_events.append("VERSION:2.0")
    ical_events.append("PRODID:-//Classmate System//All Work//EN")
    ical_events.append("CALSCALE:GREGORIAN")
    ical_events.append("METHOD:PUBLISH")
    
    dtstamp = datetime.now().strftime('%Y%m%dT%H%M%SZ')
    
    # Добавляем все тесты
    for test in tests:
        test_dict = test.to_dict() if hasattr(test, 'to_dict') else test
        event = create_ical_event(test_dict, 'test', dtstamp)
        ical_events.extend(event)
    
    # Добавляем все домашние задания
    for hw in homework:
        hw_dict = hw.to_dict() if hasattr(hw, 'to_dict') else hw
        event = create_ical_event(hw_dict, 'homework', dtstamp)
        ical_events.extend(event)
    
    # Закрываем календарь
    ical_events.append("END:VCALENDAR")
    
    return "\r\n".join(ical_events)


def create_ical_event(work, work_type, dtstamp):
    """
    Создает отдельное событие для .ics
    
    Args:
        work: Словарь с данными работы
        work_type: Тип работы
        dtstamp: Временная метка
    
    Returns:
        list: Строки события
    """
    work_id = work.get('id', 0)
    subject = work.get('subject', 'Unknown')
    work_title = work.get('type', work.get('title', 'Work'))
    date = work.get('date', datetime.now().strftime('%Y-%m-%d'))
    time = work.get('time', '23:59')
    description = work.get('description', '')
    
    event_id = f"{work_type}_{work_id}@classmate-system"
    
    date_str = date.replace('-', '')
    time_str = time.replace(':', '')
    
    dtstart = f"{date_str}T{time_str}00"
    
    end_hour = int(time[:2]) + 1
    if end_hour >= 24:
        end_hour = 23
    dtend = f"{date_str}T{end_hour:02d}{time_str[2:]}00"
    
    event_lines = [
        "BEGIN:VEVENT",
        f"UID:{event_id}",
        f"DTSTAMP:{dtstamp}",
        f"DTSTART:{dtstart}",
        f"DTEND:{dtend}",
        f"SUMMARY:{subject} - {work_title}",
        f"DESCRIPTION:{description}",
        "LOCATION:Skola",
        "STATUS:CONFIRMED",
        "BEGIN:VALARM",
        "TRIGGER:-PT24H",
        "ACTION:DISPLAY",
        f"DESCRIPTION:Reminder: {subject}",
        "END:VALARM",
        "END:VEVENT"
    ]
    
    return event_lines


def parse_ics_file(ics_content):
    """
    Парсит .ics файл и извлекает события
    
    Args:
        ics_content: Содержимое .ics файла
    
    Returns:
        list: Список событий
    """
    events = []
    current_event = {}
    in_event = False
    
    lines = ics_content.split('\n')
    
    for line in lines:
        line = line.strip()
        
        if line == 'BEGIN:VEVENT':
            in_event = True
            current_event = {}
        elif line == 'END:VEVENT':
            in_event = False
            if current_event:
                events.append(current_event)
                current_event = {}
        elif in_event and ':' in line:
            key, value = line.split(':', 1)
            
            # Обрабатываем особые случаи
            if key == 'DTSTART':
                # Извлекаем дату из формата YYYYMMDD
                if len(value) >= 8:
                    date_str = value[:8]
                    current_event['date'] = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
                    
                    # Извлекаем время если есть
                    if 'T' in value and len(value) >= 13:
                        time_str = value[9:13]
                        current_event['time'] = f"{time_str[:2]}:{time_str[2:]}"
            elif key == 'SUMMARY':
                # Разделяем subject и type
                if ' - ' in value:
                    parts = value.split(' - ', 1)
                    current_event['subject'] = parts[0]
                    current_event['type'] = parts[1]
                else:
                    current_event['subject'] = value
                    current_event['type'] = 'Event'
            elif key == 'DESCRIPTION':
                current_event['description'] = value
    
    return events