"""
Защищенные маршруты (доступные только хосту)
"""
from flask import Blueprint, render_template, request, redirect, url_for, session
from datetime import datetime
from models.subjects import load_subjects, save_subject, delete_subject
from models.tests import load_tests, save_test, delete_test
from models.homework import load_homework, save_homework, delete_homework
from models.news import load_news, save_news, delete_news, update_news
from models.terms import load_terms, save_terms
from models.updates import load_updates, save_update, delete_update, update_update
from utils.auth import is_host, login_required

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Вход в режим редактирования"""
    from config.settings import HOST_PASSWORD
    
    if request.method == 'POST':
        if request.form.get('password') == HOST_PASSWORD:
            session['is_host'] = True
            return redirect('/')
        return render_template('login.html', error="Nepareiza parole!")
    
    return render_template('login.html')


@admin_bp.route('/logout')
def logout():
    """Выход из режима редактирования"""
    session.pop('is_host', None)
    return redirect('/')


@admin_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_test():
    """Добавить тест"""
    subjects = load_subjects()
    
    if request.method == 'POST':
        time_value = request.form.get('time', '23:59')
        due_date = request.form.get('due_date')
        
        save_test(
            request.form.get('subject'),
            request.form.get('type'),
            request.form.get('date'),
            time_value,
            request.form.get('description', ''),
            due_date
        )
        return redirect('/')
    
    min_date = datetime.now().strftime('%Y-%m-%d')
    return render_template(
        'add.html',
        terms_content=load_terms(),
        min_date=min_date,
        subjects=subjects
    )


@admin_bp.route('/add_homework', methods=['GET', 'POST'])
@login_required
def add_homework():
    """Добавить домашнее задание"""
    subjects = load_subjects()
    
    if request.method == 'POST':
        time_value = request.form.get('time', '23:59')
        due_date = request.form.get('due_date')
        
        save_homework(
            request.form.get('subject'),
            request.form.get('title'),
            request.form.get('date'),
            time_value,
            request.form.get('description', ''),
            due_date
        )
        return redirect('/homework')
    
    min_date = datetime.now().strftime('%Y-%m-%d')
    return render_template(
        'add_homework.html',
        terms_content=load_terms(),
        min_date=min_date,
        subjects=subjects
    )


@admin_bp.route('/add_subject', methods=['GET', 'POST'])
@login_required
def add_subject():
    """Добавить предмет"""
    if request.method == 'POST':
        subject_name = request.form.get('subject_name')
        color = request.form.get('color', '#3498db')
        description = request.form.get('description', '')
        
        if subject_name and save_subject(subject_name, color, description):
            return redirect('/')
    
    return render_template('add_subject.html', terms_content=load_terms())


@admin_bp.route('/delete/<int:test_id>')
@login_required
def delete_test_route(test_id):
    """Удалить тест"""
    delete_test(test_id)
    return redirect('/all')


@admin_bp.route('/delete_homework/<int:hw_id>')
@login_required
def delete_homework_route(hw_id):
    """Удалить домашнее задание"""
    delete_homework(hw_id)
    return redirect('/homework')


@admin_bp.route('/delete_subject/<int:subject_id>')
@login_required
def delete_subject_route(subject_id):
    """Удалить предмет"""
    delete_subject(subject_id)
    return redirect('/')


@admin_bp.route('/news', methods=['GET', 'POST'])
@login_required
def manage_news():
    """Управление новостями"""
    if request.method == 'POST':
        from werkzeug.utils import secure_filename
        import uuid
        import os
        
        image_url = ''
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4().hex}_{filename}"
                file_path = os.path.join('static/uploads', unique_filename)
                file.save(file_path)
                image_url = f"/static/uploads/{unique_filename}"
        
        save_news(
            request.form.get('title'),
            request.form.get('content'),
            request.form.get('date'),
            image_url,
            request.form.get('is_active') == 'on'
        )
        return redirect('/news')
    
    news_list = load_news()
    min_date = datetime.now().strftime('%Y-%m-%d')
    
    return render_template(
        'news.html',
        terms_content=load_terms(),
        news=news_list,
        min_date=min_date
    )


@admin_bp.route('/updates', methods=['GET', 'POST'])
@login_required
def manage_updates():
    """Управление обновлениями"""
    if request.method == 'POST':
        save_update(
            request.form.get('title'),
            request.form.get('content'),
            request.form.get('date'),
            request.form.get('is_active') == 'on'
        )
        return redirect('/updates')
    
    updates_list = load_updates()
    min_date = datetime.now().strftime('%Y-%m-%d')
    
    return render_template(
        'updates.html',
        terms_content=load_terms(),
        updates=updates_list,
        min_date=min_date
    )