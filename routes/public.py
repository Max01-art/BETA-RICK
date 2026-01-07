"""
Публичные маршруты (доступные всем пользователям)
"""
from flask import Blueprint, render_template, request, session
from datetime import datetime
from models.subjects import load_subjects
from models.tests import load_tests
from models.homework import load_homework
from models.news import load_news
from models.terms import load_terms
from utils.auth import is_host

public_bp = Blueprint('public', __name__)


def get_common_stats():
    """Получить общую статистику для всех страниц"""
    tests = load_tests()
    homework_list = load_homework()
    today = datetime.now().date()
    
    # Подсчёт работ на сегодня
    today_work = [w for w in tests + homework_list 
                  if w.get('date') == today.strftime('%Y-%m-%d')]
    
    return {
        'today': len(today_work),
        'total': len(tests) + len(homework_list)
    }


@public_bp.route('/')
def index():
    """Главная страница"""
    subjects = load_subjects()
    news_list = load_news()
    tests = load_tests()
    homework_list = load_homework()
    
    # Группировка работ по предметам
    work_by_subject = {}
    all_work = tests + homework_list
    
    for work in all_work:
        if isinstance(work, dict):
            subject = work.get('subject')
            if subject:
                if subject not in work_by_subject:
                    work_by_subject[subject] = []
                work_by_subject[subject].append(work)
    
    # Последние 3 активные новости
    active_news = [news for news in news_list if news.get('is_active', True)]
    active_news.sort(key=lambda x: x['date'], reverse=True)
    latest_news = active_news[:3]
    
    return render_template(
        'pages/public/index.html',
        terms_content=load_terms(),
        work_by_subject=work_by_subject,
        subjects=subjects,
        news=latest_news,
        is_host=is_host(),
        stats=get_common_stats(),
        now=datetime.now()
    )


@public_bp.route('/all')
def all_tests():
    """Все работы (тесты + домашние задания)"""
    tests = load_tests()
    homework_list = load_homework()
    subjects = load_subjects()
    all_work = tests + homework_list
    
    # Сортировка по дате
    all_work.sort(key=lambda x: x.get('date', ''), reverse=False)
    
    return render_template(
        'pages/public/all.html',
        terms_content=load_terms(),
        tests=all_work,
        subjects=subjects,
        is_host=is_host(),
        stats=get_common_stats(),
        now=datetime.now()
    )


@public_bp.route('/homework')
def homework():
    """Страница домашних заданий"""
    homework_list = load_homework()
    subjects = load_subjects()
    
    # Сортировка по дате
    homework_list.sort(key=lambda x: x.get('date', ''), reverse=False)
    
    return render_template(
        'pages/public/homework.html',
        terms_content=load_terms(),
        homework=homework_list,
        subjects=subjects,
        is_host=is_host(),
        stats=get_common_stats(),
        now=datetime.now()
    )


@public_bp.route('/subject/<subject_name>')
def subject_details(subject_name):
    """Детальная страница предмета"""
    from services.subject_service import get_subject_with_stats
    
    subjects = load_subjects()
    subject_details, subject_work = get_subject_with_stats(subject_name)
    
    if not subject_details:
        return render_template(
            'pages/auth/error.html',
            error=f"Priekšmets '{subject_name}' nav atrasts"
        ), 404
    
    return render_template(
        'pages/public/subject.html',
        terms_content=load_terms(),
        subject_name=subject_name,
        subject_details=subject_details,
        tests=subject_work,
        subjects=subjects,
        is_host=is_host(),
        stats=get_common_stats(),
        now=datetime.now()
    )


@public_bp.route('/news')
def news():
    """Страница новостей"""
    news_list = load_news()
    
    # Фильтрация активных новостей
    active_news = [n for n in news_list if n.get('is_active', True)]
    active_news.sort(key=lambda x: x['date'], reverse=True)
    
    return render_template(
        'pages/public/news.html',
        terms_content=load_terms(),
        news=active_news,
        is_host=is_host(),
        stats=get_common_stats(),
        now=datetime.now()
    )


@public_bp.route('/news/<int:news_id>')
def news_detail(news_id):
    """Детальная страница новости"""
    from models.news import get_news_by_id
    
    news_item = get_news_by_id(news_id)
    
    if not news_item:
        return render_template(
            'pages/auth/error.html',
            error="Ziņa nav atrasta"
        ), 404
    
    return render_template(
        'pages/public/news_detail.html',
        terms_content=load_terms(),
        news=news_item,
        is_host=is_host(),
        stats=get_common_stats(),
        now=datetime.now()
    )


@public_bp.route('/calendar')
def calendar():
    """Календарь событий"""
    tests = load_tests()
    homework_list = load_homework()
    subjects = load_subjects()
    all_work = tests + homework_list
    
    # Сортировка по дате
    all_work.sort(key=lambda x: x.get('date', ''))
    
    return render_template(
        'pages/public/calendar.html',
        terms_content=load_terms(),
        work=all_work,
        subjects=subjects,
        is_host=is_host(),
        stats=get_common_stats(),
        now=datetime.now()
    )


@public_bp.route('/search')
def search():
    """Поиск по работам"""
    query = request.args.get('q', '').strip()
    results = []
    
    if query:
        tests = load_tests()
        homework_list = load_homework()
        subjects = load_subjects()
        all_work = tests + homework_list
        
        # Поиск по предмету, названию, описанию
        query_lower = query.lower()
        results = [
            w for w in all_work if 
            query_lower in str(w.get('subject', '')).lower() or
            query_lower in str(w.get('title', '')).lower() or
            query_lower in str(w.get('type', '')).lower() or
            query_lower in str(w.get('description', '')).lower()
        ]
        
        # Сортировка по дате
        results.sort(key=lambda x: x.get('date', ''), reverse=False)
    
    return render_template(
        'pages/public/search.html',
        terms_content=load_terms(),
        query=query,
        results=results,
        is_host=is_host(),
        stats=get_common_stats(),
        now=datetime.now()
    )


@public_bp.route('/settings')
def settings():
    """Настройки пользователя"""
    return render_template(
        'pages/public/settings.html',
        terms_content=load_terms(),
        is_host=is_host(),
        stats=get_common_stats(),
        now=datetime.now()
    )


@public_bp.route('/timer')
def timer():
    """Pomodoro таймер"""
    return render_template(
        'pages/public/timer.html',
        terms_content=load_terms(),
        is_host=is_host(),
        stats=get_common_stats(),
        now=datetime.now()
    )


@public_bp.route('/updates')
def updates_log():
    """Журнал обновлений системы"""
    from models.updates import load_updates
    
    updates_list = load_updates()
    
    # Фильтрация активных обновлений
    active_updates = [u for u in updates_list if u.get('is_active', True)]
    active_updates.sort(key=lambda x: x['date'], reverse=True)
    
    return render_template(
        'pages/public/news.html',  # Используем тот же шаблон что и для новостей
        terms_content=load_terms(),
        news=active_updates,  # Передаём как news для совместимости с шаблоном
        is_host=is_host(),
        stats=get_common_stats(),
        now=datetime.now()
    )