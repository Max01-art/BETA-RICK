"""
Публичные маршруты (доступные всем пользователям)
"""
from flask import Blueprint, render_template, request
from datetime import datetime
from models.subjects import load_subjects
from models.tests import load_tests
from models.homework import load_homework
from models.news import load_news
from models.terms import load_terms
from utils.auth import is_host

public_bp = Blueprint('public', __name__)


@public_bp.route('/')
def index():
    """Главная страница"""
    subjects = load_subjects()
    news_list = load_news()
    tests = load_tests()
    homework_list = load_homework()
    
    # Группируем работы по предметам
    work_by_subject = {}
    all_work = tests + homework_list
    
    for work in all_work:
        if isinstance(work, dict):
            subject = work.get('subject')
            if subject:
                if subject not in work_by_subject:
                    work_by_subject[subject] = []
                work_by_subject[subject].append(work)
    
    # Активные новости (последние 3)
    active_news = [news for news in news_list if news.get('is_active', True)]
    active_news.sort(key=lambda x: x['date'], reverse=True)
    latest_news = active_news[:3]
    
    return render_template(
        'index.html',
        terms_content=load_terms(),
        work_by_subject=work_by_subject,
        subjects=subjects,
        news=latest_news,
        is_host=is_host(),
        now=datetime.now()
    )


@public_bp.route('/all')
def all_tests():
    """Все работы (тесты + домашние задания)"""
    tests = load_tests()
    homework_list = load_homework()
    subjects = load_subjects()
    
    all_work = tests + homework_list
    
    return render_template(
        'all.html',
        terms_content=load_terms(),
        tests=all_work,
        subjects=subjects,
        is_host=is_host(),
        now=datetime.now()
    )


@public_bp.route('/homework')
def homework():
    """Страница домашних заданий"""
    homework_list = load_homework()
    
    return render_template(
        'homework.html',
        terms_content=load_terms(),
        homework=homework_list,
        is_host=is_host(),
        now=datetime.now()
    )


@public_bp.route('/subject/<subject_name>')
def subject_details(subject_name):
    """Страница предмета с деталями"""
    from models.subjects import get_subject_details
    from services.subject_service import get_subject_with_stats
    
    subjects = load_subjects()
    subject_details, subject_work = get_subject_with_stats(subject_name)
    
    return render_template(
        'subject.html',
        terms_content=load_terms(),
        subject_name=subject_name,
        subject_details=subject_details,
        tests=subject_work,
        subjects=subjects,
        is_host=is_host()
    )


@public_bp.route('/updates_log')
def updates_log():
    """Лог обновлений (публичный)"""
    from models.updates import load_updates
    
    updates_list = load_updates()
    active_updates = [u for u in updates_list if u.get('is_active', True)]
    
    return render_template(
        'updates_log.html',
        terms_content=load_terms(),
        updates=active_updates
    )