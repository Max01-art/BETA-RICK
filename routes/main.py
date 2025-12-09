"""
Главные маршруты приложения
"""
from flask import Blueprint, render_template, session, request
from datetime import datetime

from models.subject import Subject
from models.test import Test
from models.homework import Homework
from models.news import News
from utils.helpers import calculate_days_left, get_work_by_subject

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Главная страница"""
    # Загружаем данные
    subjects = Subject.get_all()
    news_list = News.get_active(limit=3)
    
    # Группируем работы по предметам
    work_by_subject = get_work_by_subject()
    
    return render_template(
        'pages/index.html',
        subjects=subjects,
        work_by_subject=work_by_subject,
        news=news_list,
        now=datetime.now()
    )


@main_bp.route('/updates_log')
def updates_log():
    """Страница с обновлениями"""
    from models.update import Update
    
    updates = Update.get_active()
    
    return render_template(
        'pages/updates.html',
        updates=updates
    )


@main_bp.route('/terms')
def terms():
    """Условия использования"""
    from models.terms import Terms
    
    terms_content = Terms.get_latest()
    
    return render_template(
        'pages/terms.html',
        terms_content=terms_content
    )


@main_bp.route('/debug')
def debug():
    """Debug информация (только для разработки)"""
    if not request.args.get('secret') == 'debug123':
        return "Access Denied", 403
    
    import os
    from core.database import get_db_connection
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Получаем статистику
    stats = {
        'subjects_count': Subject.count(),
        'tests_count': Test.count(),
        'homework_count': Homework.count(),
        'news_count': News.count(),
        'database_type': 'PostgreSQL' if os.environ.get('DATABASE_URL') else 'SQLite',
        'environment': os.environ.get('FLASK_ENV', 'development'),
        'app_version': '2.1.0'
    }
    
    conn.close()
    
    return render_template(
        'pages/debug.html',
        stats=stats
    )


@main_bp.route('/search')
def search():
    """Поиск по работам"""
    query = request.args.get('q', '').strip()
    
    if not query:
        return render_template('pages/search.html', results=[], query='')
    
    # Поиск в тестах и домашних заданиях
    tests = Test.search(query)
    homework = Homework.search(query)
    subjects = Subject.search(query)
    
    results = {
        'tests': tests,
        'homework': homework,
        'subjects': subjects,
        'total': len(tests) + len(homework) + len(subjects)
    }
    
    return render_template(
        'pages/search.html',
        results=results,
        query=query
    )


@main_bp.route('/calendar/all')
def download_all_calendar():
    """Скачать календарь всех работ"""
    from utils.calendar_utils import generate_calendar_for_all_work
    
    tests = Test.get_upcoming()
    homework = Homework.get_upcoming()
    
    ical_content = generate_calendar_for_all_work(tests, homework)
    
    from flask import make_response
    
    response = make_response(ical_content)
    response.headers['Content-Type'] = 'text/calendar'
    response.headers['Content-Disposition'] = 'attachment; filename=all_tests.ics'
    
    return response


@main_bp.route('/export/json')
def export_json():
    """Экспорт всех данных в JSON"""
    from flask import jsonify
    
    data = {
        'subjects': [s.to_dict() for s in Subject.get_all()],
        'tests': [t.to_dict() for t in Test.get_all()],
        'homework': [h.to_dict() for h in Homework.get_all()],
        'news': [n.to_dict() for n in News.get_all()],
        'exported_at': datetime.now().isoformat()
    }
    
    return jsonify(data)


@main_bp.route('/stats')
def stats():
    """Статистика приложения"""
    from collections import defaultdict
    
    # Собираем статистику
    subjects = Subject.get_all()
    tests = Test.get_all()
    homework = Homework.get_all()
    
    # Работы по предметам
    work_by_subject = defaultdict(lambda: {'tests': 0, 'homework': 0})
    
    for test in tests:
        work_by_subject[test.subject]['tests'] += 1
    
    for hw in homework:
        work_by_subject[hw.subject]['homework'] += 1
    
    # Работы по месяцам
    work_by_month = defaultdict(int)
    
    for work in tests + homework:
        try:
            date = datetime.strptime(work.date, '%Y-%m-%d')
            month_key = date.strftime('%Y-%m')
            work_by_month[month_key] += 1
        except:
            pass
    
    stats_data = {
        'total_subjects': len(subjects),
        'total_tests': len(tests),
        'total_homework': len(homework),
        'work_by_subject': dict(work_by_subject),
        'work_by_month': dict(work_by_month),
        'upcoming_count': len([t for t in tests + homework if calculate_days_left(t.date) >= 0])
    }
    
    return render_template(
        'pages/stats.html',
        stats=stats_data
    )


# Context processor для всех шаблонов
@main_bp.app_context_processor
def inject_common_data():
    """Добавляет общие данные во все шаблоны"""
    return {
        'app_name': 'Classmate',
        'app_version': '2.1.0',
        'current_year': datetime.now().year,
        'is_host': session.get('is_host', False)
    }