from flask import Blueprint, render_template, request
from datetime import datetime
from models.subjects import load_subjects
from models.tests import load_tests
from models.homework import load_homework
from models.news import load_news
from models.terms import load_terms
from utils.auth import is_host

public_bp = Blueprint('public', __name__)

# --- Helper function to avoid repeating stats in every route ---
def get_common_stats():
    return {
        'today': 10,  # Replace with actual logic later
        'total': 100
    }

@public_bp.route('/')
def index():
    subjects = load_subjects()
    news_list = load_news()
    tests = load_tests()
    homework_list = load_homework()
    
    work_by_subject = {}
    all_work = tests + homework_list
    
    for work in all_work:
        if isinstance(work, dict):
            subject = work.get('subject')
            if subject:
                if subject not in work_by_subject:
                    work_by_subject[subject] = []
                work_by_subject[subject].append(work)
    
    active_news = [news for news in news_list if news.get('is_active', True)]
    active_news.sort(key=lambda x: x['date'], reverse=True)
    latest_news = active_news[:3]
    
    return render_template(
        'pages/public/index.html',  # Correct Path
        terms_content=load_terms(),
        work_by_subject=work_by_subject,
        subjects=subjects,
        news=latest_news,
        is_host=is_host(),
        stats=get_common_stats(),   # Added stats here
        now=datetime.now()
    )

@public_bp.route('/all')
def all_tests():
    tests = load_tests()
    homework_list = load_homework()
    subjects = load_subjects()
    all_work = tests + homework_list
    
    return render_template(
        'pages/public/all.html',    # Updated Path
        terms_content=load_terms(),
        tests=all_work,
        subjects=subjects,
        is_host=is_host(),
        stats=get_common_stats(),   # Added stats here
        now=datetime.now()
    )

@public_bp.route('/homework')
def homework():
    homework_list = load_homework()
    return render_template(
        'pages/public/homework.html', # Updated Path
        terms_content=load_terms(),
        homework=homework_list,
        is_host=is_host(),
        stats=get_common_stats(),     # Added stats here
        now=datetime.now()
    )

@public_bp.route('/subject/<subject_name>')
def subject_details(subject_name):
    from models.subjects import get_subject_details
    from services.subject_service import get_subject_with_stats
    
    subjects = load_subjects()
    subject_details, subject_work = get_subject_with_stats(subject_name)
    
    return render_template(
        'pages/public/subject.html',  # Updated Path
        terms_content=load_terms(),
        subject_name=subject_name,
        subject_details=subject_details,
        tests=subject_work,
        stats=get_common_stats(),     # Using helper here
        now=datetime.now(),
        subjects=subjects,
        is_host=is_host()
    )

@public_bp.route('/updates_log')
def updates_log():
    from models.updates import load_updates
    updates_list = load_updates()
    active_updates = [u for u in updates_list if u.get('is_active', True)]
    
    return render_template(
        'pages/public/updates_log.html', # Updated Path
        terms_content=load_terms(),
        updates=active_updates,
        stats=get_common_stats(),        # Added stats here
        now=datetime.now()               # Added now here just in case base.html needs it
    )