"""
Subject Service - Управление предметами
"""

from models.subjects import get_all_subjects, get_subject_by_name
from models.tests import load_tests
from models.homework import load_homework
from datetime import datetime


def get_subjects_with_work_count():
    """
    Получает все предметы с количеством работ
    
    Returns:
        list: Список предметов с work_count
    """
    try:
        subjects = get_all_subjects()
        tests = load_tests()
        homework = load_homework()
        all_work = tests + homework
        
        # Подсчитываем работы для каждого предмета
        for subject in subjects:
            subject['work_count'] = sum(
                1 for work in all_work 
                if work.get('subject') == subject['name']
            )
        
        return subjects
        
    except Exception as e:
        print(f"Error getting subjects with work count: {e}")
        return []


def get_subject_statistics(subject_name):
    """
    Статистика по предмету
    
    Args:
        subject_name (str): Название предмета
        
    Returns:
        dict: Статистика
    """
    try:
        tests = load_tests()
        homework = load_homework()
        all_work = tests + homework
        
        # Фильтруем работы по предмету
        subject_work = [w for w in all_work if w.get('subject') == subject_name]
        
        today = datetime.now().date()
        
        stats = {
            'total': len(subject_work),
            'tests': sum(1 for w in subject_work if w.get('source') == 'test'),
            'homework': sum(1 for w in subject_work if w.get('source') == 'homework'),
            'today': 0,
            'tomorrow': 0,
            'week': 0,
            'overdue': 0
        }
        
        for work in subject_work:
            try:
                work_date = datetime.strptime(work['date'], '%Y-%m-%d').date()
                days_left = (work_date - today).days
                
                if days_left == 0:
                    stats['today'] += 1
                elif days_left == 1:
                    stats['tomorrow'] += 1
                elif 2 <= days_left <= 7:
                    stats['week'] += 1
                elif days_left < 0:
                    stats['overdue'] += 1
            except:
                continue
        
        return stats
        
    except Exception as e:
        print(f"Error getting subject statistics: {e}")
        return {
            'total': 0,
            'tests': 0,
            'homework': 0,
            'today': 0,
            'tomorrow': 0,
            'week': 0,
            'overdue': 0
        }


def get_work_by_subject():
    """
    Группирует все работы по предметам
    
    Returns:
        dict: {subject_name: [works]}
    """
    try:
        tests = load_tests()
        homework = load_homework()
        all_work = tests + homework
        
        work_by_subject = {}
        
        for work in all_work:
            subject = work.get('subject', 'Другое')
            if subject not in work_by_subject:
                work_by_subject[subject] = []
            work_by_subject[subject].append(work)
        
        # Сортируем работы в каждом предмете по дате
        for subject in work_by_subject:
            work_by_subject[subject].sort(
                key=lambda x: x.get('date', '9999-12-31')
            )
        
        return work_by_subject
        
    except Exception as e:
        print(f"Error grouping work by subject: {e}")
        return {}


def get_subject_colors():
    """
    Словарь цветов предметов
    
    Returns:
        dict: {subject_name: color}
    """
    try:
        subjects = get_all_subjects()
        return {
            s['name']: s.get('color', '#667eea') 
            for s in subjects
        }
    except:
        return {}