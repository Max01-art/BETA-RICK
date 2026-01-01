"""
Защищенные маршруты (доступные только хосту)
"""
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
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
        return render_template('pages/auth/login.html', error="Nepareiza parole!")
    
    return render_template('pages/auth/login.html')


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
        'pages/admin/add_work.html',
        terms_content=load_terms(),
        min_date=min_date,
        subjects=subjects,
        work_type='test'
    )


@admin_bp.route('/add_homework', methods=['GET', 'POST'])
@login_required
def add_homework_route():
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
        'pages/admin/add_work.html',
        terms_content=load_terms(),
        min_date=min_date,
        subjects=subjects,
        work_type='homework'
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
            flash('Priekšmets pievienots!', 'success')
            return redirect('/')
    
    return render_template('pages/admin/edit_subject.html', 
                         terms_content=load_terms(),
                         subject=None)


@admin_bp.route('/edit_subject/<int:subject_id>', methods=['GET', 'POST'])
@login_required
def edit_subject(subject_id):
    """Редактировать предмет"""
    from models.subjects import get_subject_by_id, update_subject
    
    if request.method == 'POST':
        subject_name = request.form.get('subject_name')
        color = request.form.get('color', '#3498db')
        description = request.form.get('description', '')
        
        if update_subject(subject_id, subject_name, color, description):
            flash('Priekšmets atjaunināts!', 'success')
            return redirect('/')
    
    subject = get_subject_by_id(subject_id)
    return render_template('pages/admin/edit_subject.html',
                         terms_content=load_terms(),
                         subject=subject)


@admin_bp.route('/delete/<int:test_id>')
@login_required
def delete_test_route(test_id):
    """Удалить тест"""
    delete_test(test_id)
    flash('Tests izdzēsts!', 'success')
    return redirect('/all')


@admin_bp.route('/delete_homework/<int:hw_id>')
@login_required
def delete_homework_route(hw_id):
    """Удалить домашнее задание"""
    delete_homework(hw_id)
    flash('Mājasdarbs izdzēsts!', 'success')
    return redirect('/homework')


@admin_bp.route('/delete_subject/<int:subject_id>')
@login_required
def delete_subject_route(subject_id):
    """Удалить предмет"""
    delete_subject(subject_id)
    flash('Priekšmets izdzēsts!', 'success')
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
                upload_dir = 'static/uploads'
                
                # Создаем директорию если её нет
                os.makedirs(upload_dir, exist_ok=True)
                
                file_path = os.path.join(upload_dir, unique_filename)
                file.save(file_path)
                image_url = f"/static/uploads/{unique_filename}"
        
        save_news(
            request.form.get('title'),
            request.form.get('content'),
            request.form.get('date'),
            image_url,
            request.form.get('is_active') == 'on'
        )
        flash('Ziņa pievienota!', 'success')
        return redirect('/news')
    
    news_list = load_news()
    min_date = datetime.now().strftime('%Y-%m-%d')
    
    return render_template(
        'pages/admin/manage_news.html',
        terms_content=load_terms(),
        news=news_list,
        min_date=min_date
    )


@admin_bp.route('/edit_news/<int:news_id>', methods=['GET', 'POST'])
@login_required
def edit_news(news_id):
    """Редактировать новость"""
    from models.news import get_news_by_id
    
    if request.method == 'POST':
        from werkzeug.utils import secure_filename
        import uuid
        import os
        
        image_url = request.form.get('existing_image', '')
        
        # Новое изображение
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4().hex}_{filename}"
                upload_dir = 'static/uploads'
                os.makedirs(upload_dir, exist_ok=True)
                
                file_path = os.path.join(upload_dir, unique_filename)
                file.save(file_path)
                image_url = f"/static/uploads/{unique_filename}"
        
        update_news(
            news_id,
            request.form.get('title'),
            request.form.get('content'),
            request.form.get('date'),
            image_url,
            request.form.get('is_active') == 'on'
        )
        flash('Ziņa atjaunināta!', 'success')
        return redirect('/news')
    
    news = get_news_by_id(news_id)
    return render_template('pages/admin/manage_news.html',
                         terms_content=load_terms(),
                         news_item=news,
                         min_date=datetime.now().strftime('%Y-%m-%d'))


@admin_bp.route('/delete_news/<int:news_id>')
@login_required
def delete_news_route(news_id):
    """Удалить новость"""
    delete_news(news_id)
    flash('Ziņa izdzēsta!', 'success')
    return redirect('/news')


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
        flash('Atjauninājums pievienots!', 'success')
        return redirect('/updates')
    
    updates_list = load_updates()
    min_date = datetime.now().strftime('%Y-%m-%d')
    
    return render_template(
        'pages/admin/manage_news.html',
        terms_content=load_terms(),
        updates=updates_list,
        min_date=min_date
    )


@admin_bp.route('/edit_update/<int:update_id>', methods=['GET', 'POST'])
@login_required
def edit_update(update_id):
    """Редактировать обновление"""
    from models.updates import get_update_by_id
    
    if request.method == 'POST':
        update_update(
            update_id,
            request.form.get('title'),
            request.form.get('content'),
            request.form.get('date'),
            request.form.get('is_active') == 'on'
        )
        flash('Atjauninājums atjaunināts!', 'success')
        return redirect('/updates')
    
    update = get_update_by_id(update_id)
    return render_template('pages/admin/manage_news.html',
                         terms_content=load_terms(),
                         update_item=update,
                         min_date=datetime.now().strftime('%Y-%m-%d'))


@admin_bp.route('/delete_update/<int:update_id>')
@login_required
def delete_update_route(update_id):
    """Удалить обновление"""
    delete_update(update_id)
    flash('Atjauninājums izdzēsts!', 'success')
    return redirect('/updates')


@admin_bp.route('/dashboard')
@login_required
def dashboard():
    """Admin Dashboard"""
    tests = load_tests()
    homework_list = load_homework()
    subjects = load_subjects()
    news_list = load_news()
    
    stats = {
        'total_works': len(tests) + len(homework_list),
        'total_tests': len(tests),
        'total_homework': len(homework_list),
        'total_subjects': len(subjects),
        'total_news': len(news_list),
        'users': 0  # TODO: implement user count
    }
    
    return render_template('pages/admin/dashboard.html',
                         terms_content=load_terms(),
                         stats=stats,
                         is_host=True)


@admin_bp.route('/manage_tests')
@login_required
def manage_tests():
    """Управление тестами"""
    tests = load_tests()
    return render_template('pages/admin/manage_tests.html',
                         terms_content=load_terms(),
                         tests=tests,
                         is_host=True)


@admin_bp.route('/manage_homework')
@login_required
def manage_homework():
    """Управление домашними заданиями"""
    homework_list = load_homework()
    return render_template('pages/admin/manage_homework.html',
                         terms_content=load_terms(),
                         homework=homework_list,
                         is_host=True)


@admin_bp.route('/manage_subjects')
@login_required
def manage_subjects():
    """Управление предметами"""
    subjects = load_subjects()
    
    # Add work count for each subject
    tests = load_tests()
    homework_list = load_homework()
    all_work = tests + homework_list
    
    for subject in subjects:
        subject['work_count'] = sum(
            1 for work in all_work 
            if work.get('subject') == subject['name']
        )
    
    return render_template('pages/admin/manage_subjects.html',
                         terms_content=load_terms(),
                         subjects=subjects,
                         is_host=True)


@admin_bp.route('/analytics')
@login_required
def analytics():
    """Аналитика"""
    from services.subject_service import get_subjects_with_work_count
    
    tests = load_tests()
    homework_list = load_homework()
    subjects = get_subjects_with_work_count()
    
    # Calculate analytics
    total_works = len(tests) + len(homework_list)
    today = datetime.now().date()
    
    analytics_data = {
        'active_users': 0,  # TODO: implement
        'total_works': total_works,
        'avg_per_day': 0,  # TODO: calculate
        'subjects_data': subjects,
        'tests_vs_homework': {
            'tests': len(tests),
            'homework': len(homework_list)
        }
    }
    
    return render_template('pages/admin/analytics.html',
                         terms_content=load_terms(),
                         analytics=analytics_data,
                         is_host=True)


@admin_bp.route('/edit_work/<int:work_id>', methods=['GET', 'POST'])
@login_required
def edit_work(work_id):
    """Редактировать работу (тест или ДЗ)"""
    # Try to find in tests first
    tests = load_tests()
    work = next((t for t in tests if t.get('id') == work_id), None)
    work_type = 'test'
    
    # If not in tests, check homework
    if not work:
        homework_list = load_homework()
        work = next((h for h in homework_list if h.get('id') == work_id), None)
        work_type = 'homework'
    
    if not work:
        flash('Darbs nav atrasts!', 'error')
        return redirect('/')
    
    if request.method == 'POST':
        # Update logic here
        flash('Darbs atjaunināts!', 'success')
        return redirect('/all')
    
    subjects = load_subjects()
    return render_template('pages/admin/edit_work.html',
                         terms_content=load_terms(),
                         work=work,
                         work_type=work_type,
                         subjects=subjects,
                         is_host=True)