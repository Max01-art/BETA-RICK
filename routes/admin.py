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


# ==================== АВТОРИЗАЦИЯ ====================

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Вход в режим редактирования"""
    from config.settings import HOST_PASSWORD, HOST_USERNAME
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == HOST_USERNAME and password == HOST_PASSWORD:
            session['is_host'] = True
            flash('Veiksmīgi pieteicies!', 'success')
            return redirect('/')
        
        return render_template(
            'pages/auth/login.html',
            error="Nepareizi dati!"
        )
    
    return render_template('pages/auth/login.html')


@admin_bp.route('/logout')
def logout():
    """Выход из режима редактирования"""
    session.pop('is_host', None)
    flash('Veiksmīgi atteicies!', 'info')
    return redirect('/')


@admin_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Регистрация (пока не используется)"""
    if request.method == 'POST':
        # TODO: Implement user registration
        flash('Reģistrācija vēl nav pieejama', 'warning')
        return redirect(url_for('admin.login'))
    
    return render_template('pages/auth/register.html')


# ==================== DASHBOARD ====================

@admin_bp.route('/admin/dashboard')
@login_required
def dashboard():
    """Главная панель администратора"""
    tests = load_tests()
    homework_list = load_homework()
    subjects = load_subjects()
    news_list = load_news()
    updates_list = load_updates()
    
    # Статистика
    today = datetime.now().date()
    upcoming_tests = [t for t in tests if t.get('date', '') >= today.strftime('%Y-%m-%d')]
    upcoming_homework = [h for h in homework_list if h.get('date', '') >= today.strftime('%Y-%m-%d')]
    
    stats = {
        'total_works': len(tests) + len(homework_list),
        'total_tests': len(tests),
        'total_homework': len(homework_list),
        'upcoming_tests': len(upcoming_tests),
        'upcoming_homework': len(upcoming_homework),
        'total_subjects': len(subjects),
        'total_news': len(news_list),
        'total_updates': len(updates_list),
        'active_news': len([n for n in news_list if n.get('is_active', True)]),
        'users': 0  # TODO: implement user count
    }
    
    return render_template(
        'pages/admin/dashboard.html',
        terms_content=load_terms(),
        stats=stats,
        is_host=True
    )


@admin_bp.route('/admin/analytics')
@login_required
def analytics():
    """Аналитика и статистика"""
    from services.subject_service import get_subjects_with_work_count
    
    tests = load_tests()
    homework_list = load_homework()
    subjects = get_subjects_with_work_count()
    
    # Расчёт аналитики
    total_works = len(tests) + len(homework_list)
    today = datetime.now().date()
    
    # Работы по дням (последние 30 дней)
    from collections import defaultdict
    from datetime import timedelta
    
    daily_stats = defaultdict(int)
    for work in tests + homework_list:
        work_date = work.get('date')
        if work_date:
            daily_stats[work_date] += 1
    
    analytics_data = {
        'active_users': 0,  # TODO: implement
        'total_works': total_works,
        'avg_per_day': round(total_works / 30, 2) if total_works > 0 else 0,
        'subjects_data': subjects,
        'tests_vs_homework': {
            'tests': len(tests),
            'homework': len(homework_list)
        },
        'daily_stats': dict(sorted(daily_stats.items(), reverse=True)[:30])
    }
    
    return render_template(
        'pages/admin/analytics.html',
        terms_content=load_terms(),
        analytics=analytics_data,
        is_host=True
    )


# ==================== ТЕСТЫ ====================

@admin_bp.route('/admin/add', methods=['GET', 'POST'])
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
        flash('Tests pievienots!', 'success')
        return redirect('/all')
    
    min_date = datetime.now().strftime('%Y-%m-%d')
    return render_template(
        'pages/admin/add_work.html',
        terms_content=load_terms(),
        min_date=min_date,
        subjects=subjects,
        work_type='test',
        is_host=True
    )


@admin_bp.route('/admin/manage_tests')
@login_required
def manage_tests():
    """Управление тестами"""
    tests = load_tests()
    subjects = load_subjects()
    
    # Сортировка по дате
    tests.sort(key=lambda x: x.get('date', ''), reverse=True)
    
    return render_template(
        'pages/admin/manage_tests.html',
        terms_content=load_terms(),
        tests=tests,
        subjects=subjects,
        is_host=True
    )


@admin_bp.route('/admin/delete/<int:test_id>')
@login_required
def delete_test_route(test_id):
    """Удалить тест"""
    delete_test(test_id)
    flash('Tests izdzēsts!', 'success')
    return redirect('/admin/manage_tests')


# ==================== ДОМАШНИЕ ЗАДАНИЯ ====================

@admin_bp.route('/admin/add_homework', methods=['GET', 'POST'])
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
        flash('Mājasdarbs pievienots!', 'success')
        return redirect('/homework')
    
    min_date = datetime.now().strftime('%Y-%m-%d')
    return render_template(
        'pages/admin/add_work.html',
        terms_content=load_terms(),
        min_date=min_date,
        subjects=subjects,
        work_type='homework',
        is_host=True
    )


@admin_bp.route('/admin/manage_homework')
@login_required
def manage_homework():
    """Управление домашними заданиями"""
    homework_list = load_homework()
    subjects = load_subjects()
    
    # Сортировка по дате
    homework_list.sort(key=lambda x: x.get('date', ''), reverse=True)
    
    return render_template(
        'pages/admin/manage_homework.html',
        terms_content=load_terms(),
        homework=homework_list,
        subjects=subjects,
        is_host=True
    )


@admin_bp.route('/admin/delete_homework/<int:hw_id>')
@login_required
def delete_homework_route(hw_id):
    """Удалить домашнее задание"""
    delete_homework(hw_id)
    flash('Mājasdarbs izdzēsts!', 'success')
    return redirect('/admin/manage_homework')


# ==================== ПРЕДМЕТЫ ====================

@admin_bp.route('/admin/add_subject', methods=['GET', 'POST'])
@login_required
def add_subject():
    """Добавить предмет"""
    if request.method == 'POST':
        subject_name = request.form.get('subject_name')
        color = request.form.get('color', '#3498db')
        description = request.form.get('description', '')
        
        if subject_name and save_subject(subject_name, color, description):
            flash('Priekšmets pievienots!', 'success')
            return redirect('/admin/manage_subjects')
        else:
            flash('Kļūda pievienojot priekšmetu!', 'error')
    
    return render_template(
        'pages/admin/edit_subject.html',
        terms_content=load_terms(),
        subject=None,
        is_host=True
    )


@admin_bp.route('/admin/edit_subject/<int:subject_id>', methods=['GET', 'POST'])
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
            return redirect('/admin/manage_subjects')
        else:
            flash('Kļūda atjauninot priekšmetu!', 'error')
    
    subject = get_subject_by_id(subject_id)
    
    if not subject:
        flash('Priekšmets nav atrasts!', 'error')
        return redirect('/admin/manage_subjects')
    
    return render_template(
        'pages/admin/edit_subject.html',
        terms_content=load_terms(),
        subject=subject,
        is_host=True
    )


@admin_bp.route('/admin/manage_subjects')
@login_required
def manage_subjects():
    """Управление предметами"""
    subjects = load_subjects()
    
    # Добавляем количество работ для каждого предмета
    tests = load_tests()
    homework_list = load_homework()
    all_work = tests + homework_list
    
    for subject in subjects:
        subject['work_count'] = sum(
            1 for work in all_work 
            if work.get('subject') == subject['name']
        )
    
    return render_template(
        'pages/admin/manage_subjects.html',
        terms_content=load_terms(),
        subjects=subjects,
        is_host=True
    )


@admin_bp.route('/admin/delete_subject/<int:subject_id>')
@login_required
def delete_subject_route(subject_id):
    """Удалить предмет"""
    delete_subject(subject_id)
    flash('Priekšmets izdzēsts!', 'success')
    return redirect('/admin/manage_subjects')


# ==================== НОВОСТИ ====================

@admin_bp.route('/admin/news', methods=['GET', 'POST'])
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
        return redirect('/admin/news')
    
    news_list = load_news()
    news_list.sort(key=lambda x: x.get('date', ''), reverse=True)
    min_date = datetime.now().strftime('%Y-%m-%d')
    
    return render_template(
        'pages/admin/manage_news.html',
        terms_content=load_terms(),
        news=news_list,
        min_date=min_date,
        is_host=True
    )


@admin_bp.route('/admin/edit_news/<int:news_id>', methods=['GET', 'POST'])
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
        return redirect('/admin/news')
    
    news = get_news_by_id(news_id)
    
    if not news:
        flash('Ziņa nav atrasta!', 'error')
        return redirect('/admin/news')
    
    return render_template(
        'pages/admin/manage_news.html',
        terms_content=load_terms(),
        news_item=news,
        min_date=datetime.now().strftime('%Y-%m-%d'),
        is_host=True
    )


@admin_bp.route('/admin/delete_news/<int:news_id>')
@login_required
def delete_news_route(news_id):
    """Удалить новость"""
    delete_news(news_id)
    flash('Ziņa izdzēsta!', 'success')
    return redirect('/admin/news')


# ==================== ОБНОВЛЕНИЯ ====================

@admin_bp.route('/admin/updates', methods=['GET', 'POST'])
@login_required
def manage_updates():
    """Управление обновлениями системы"""
    if request.method == 'POST':
        save_update(
            request.form.get('title'),
            request.form.get('content'),
            request.form.get('date'),
            request.form.get('is_active') == 'on'
        )
        flash('Atjauninājums pievienots!', 'success')
        return redirect('/admin/updates')
    
    updates_list = load_updates()
    updates_list.sort(key=lambda x: x.get('date', ''), reverse=True)
    min_date = datetime.now().strftime('%Y-%m-%d')
    
    return render_template(
        'pages/admin/manage_news.html',
        terms_content=load_terms(),
        updates=updates_list,
        min_date=min_date,
        is_host=True
    )


@admin_bp.route('/admin/edit_update/<int:update_id>', methods=['GET', 'POST'])
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
        return redirect('/admin/updates')
    
    update = get_update_by_id(update_id)
    
    if not update:
        flash('Atjauninājums nav atrasts!', 'error')
        return redirect('/admin/updates')
    
    return render_template(
        'pages/admin/manage_news.html',
        terms_content=load_terms(),
        update_item=update,
        min_date=datetime.now().strftime('%Y-%m-%d'),
        is_host=True
    )


@admin_bp.route('/admin/delete_update/<int:update_id>')
@login_required
def delete_update_route(update_id):
    """Удалить обновление"""
    delete_update(update_id)
    flash('Atjauninājums izdzēsts!', 'success')
    return redirect('/admin/updates')


# ==================== РЕДАКТИРОВАНИЕ РАБОТ ====================

@admin_bp.route('/admin/edit_work/<int:work_id>', methods=['GET', 'POST'])
@login_required
def edit_work(work_id):
    """Редактировать работу (тест или ДЗ)"""
    # Пробуем найти в тестах
    tests = load_tests()
    work = next((t for t in tests if t.get('id') == work_id), None)
    work_type = 'test'
    
    # Если нет в тестах, ищем в домашних заданиях
    if not work:
        homework_list = load_homework()
        work = next((h for h in homework_list if h.get('id') == work_id), None)
        work_type = 'homework'
    
    if not work:
        flash('Darbs nav atrasts!', 'error')
        return redirect('/all')
    
    subjects = load_subjects()
    
    if request.method == 'POST':
        from models.tests import update_test
        from models.homework import update_homework
        
        if work_type == 'test':
            update_test(
                work_id,
                request.form.get('subject'),
                request.form.get('type'),
                request.form.get('date'),
                request.form.get('time', '23:59'),
                request.form.get('description', ''),
                request.form.get('due_date')
            )
        else:
            update_homework(
                work_id,
                request.form.get('subject'),
                request.form.get('title'),
                request.form.get('date'),
                request.form.get('time', '23:59'),
                request.form.get('description', ''),
                request.form.get('due_date')
            )
        
        flash('Darbs atjaunināts!', 'success')
        return redirect('/all')
    
    return render_template(
        'pages/admin/edit_work.html',
        terms_content=load_terms(),
        work=work,
        work_type=work_type,
        subjects=subjects,
        is_host=True
    )