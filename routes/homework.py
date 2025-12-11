"""
Маршруты для работы с домашними заданиями
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime

from models.homework import Homework
from models.subject import Subject
from utils.decorators import host_required
from utils.validators import validate_homework_data
from utils.helpers import calculate_days_left

homework_bp = Blueprint('homework', __name__)


@homework_bp.route('/')
def index():
    """Страница всех домашних заданий"""
    # Получаем все домашние задания
    all_homework = Homework.get_all()
    
    # Разделяем на активные и просроченные
    active_homework = []
    overdue_homework = []
    
    for hw in all_homework:
        hw.days_left = calculate_days_left(hw.date, hw.time, hw.due_date)
        if hw.days_left >= 0:
            active_homework.append(hw)
        else:
            overdue_homework.append(hw)
    
    # Получаем предметы для фильтра
    subjects = Subject.get_all()
    
    return render_template(
        'pages/homework.html',
        active_homework=active_homework,
        overdue_homework=overdue_homework,
        subjects=subjects,
        total_count=len(all_homework)
    )


@homework_bp.route('/add', methods=['GET', 'POST'])
@host_required
def add():
    """Добавить домашнее задание"""
    if request.method == 'POST':
        # Получаем данные из формы
        data = {
            'subject': request.form.get('subject', '').strip(),
            'title': request.form.get('title', '').strip(),
            'date': request.form.get('date', '').strip(),
            'time': request.form.get('time', '23:59').strip(),
            'description': request.form.get('description', '').strip(),
            'type': request.form.get('type', 'Mājasdarbs').strip(),
            'due_date': request.form.get('due_date', '').strip() or None
        }
        
        # Валидация
        is_valid, errors = validate_homework_data(data)
        
        if not is_valid:
            for field, error in errors.items():
                flash(f'❌ {error}', 'danger')
            return redirect(url_for('homework.add'))
        
        # Создаем домашнее задание
        hw = Homework(
            subject=data['subject'],
            title=data['title'],
            date=data['date'],
            time=data['time'],
            description=data['description'],
            type=data['type'],
            due_date=data['due_date']
        )
        
        if hw.save():
            flash(f'✅ Mājasdarbs "{hw.title}" pievienots!', 'success')
            return redirect(url_for('homework.index'))
        else:
            flash('❌ Kļūda pievienojot mājasdarbu', 'danger')
    
    # GET запрос - показываем форму
    subjects = Subject.get_all()
    return render_template(
        'forms/add_homework.html',
        subjects=subjects,
        today=datetime.now().strftime('%Y-%m-%d')
    )


@homework_bp.route('/<int:homework_id>')
def detail(homework_id):
    """Детальная страница домашнего задания"""
    hw = Homework.get_by_id(homework_id)
    
    if not hw:
        flash('❌ Mājasdarbs nav atrasts', 'danger')
        return redirect(url_for('homework.index'))
    
    hw.days_left = calculate_days_left(hw.date, hw.time, hw.due_date)
    
    return render_template(
        'pages/homework_detail.html',
        homework=hw
    )


@homework_bp.route('/<int:homework_id>/edit', methods=['GET', 'POST'])
@host_required
def edit(homework_id):
    """Редактировать домашнее задание"""
    hw = Homework.get_by_id(homework_id)
    
    if not hw:
        flash('❌ Mājasdarbs nav atrasts', 'danger')
        return redirect(url_for('homework.index'))
    
    if request.method == 'POST':
        # Обновляем данные
        data = {
            'subject': request.form.get('subject', '').strip(),
            'title': request.form.get('title', '').strip(),
            'date': request.form.get('date', '').strip(),
            'time': request.form.get('time', '23:59').strip(),
            'description': request.form.get('description', '').strip(),
            'type': request.form.get('type', 'Mājasdarbs').strip(),
            'due_date': request.form.get('due_date', '').strip() or None
        }
        
        # Валидация
        is_valid, errors = validate_homework_data(data)
        
        if not is_valid:
            for field, error in errors.items():
                flash(f'❌ {error}', 'danger')
            return redirect(url_for('homework.edit', homework_id=homework_id))
        
        # Обновляем объект
        hw.subject = data['subject']
        hw.title = data['title']
        hw.date = data['date']
        hw.time = data['time']
        hw.description = data['description']
        hw.type = data['type']
        hw.due_date = data['due_date']
        
        if hw.save():
            flash(f'✅ Mājasdarbs "{hw.title}" atjaunināts!', 'success')
            return redirect(url_for('homework.detail', homework_id=homework_id))
        else:
            flash('❌ Kļūda atjauninot mājasdarbu', 'danger')
    
    # GET запрос - показываем форму
    subjects = Subject.get_all()
    return render_template(
        'forms/edit_homework.html',
        homework=hw,
        subjects=subjects
    )


@homework_bp.route('/<int:homework_id>/delete', methods=['POST'])
@host_required
def delete(homework_id):
    """Удалить домашнее задание"""
    hw = Homework.get_by_id(homework_id)
    
    if not hw:
        flash('❌ Mājasdarbs nav atrasts', 'danger')
        return redirect(url_for('homework.index'))
    
    title = hw.title
    
    if hw.delete():
        flash(f'✅ Mājasdarbs "{title}" dzēsts!', 'success')
    else:
        flash('❌ Kļūda dzēšot mājasdarbu', 'danger')
    
    return redirect(url_for('homework.index'))


@homework_bp.route('/by-subject/<subject_name>')
def by_subject(subject_name):
    """Домашние задания по предмету"""
    homework_list = Homework.get_by_subject(subject_name)
    
    # Добавляем days_left
    for hw in homework_list:
        hw.days_left = calculate_days_left(hw.date, hw.time, hw.due_date)
    
    # Разделяем на активные и просроченные
    active = [hw for hw in homework_list if hw.days_left >= 0]
    overdue = [hw for hw in homework_list if hw.days_left < 0]
    
    subject = Subject.get_by_name(subject_name)
    
    return render_template(
        'pages/homework_by_subject.html',
        subject=subject,
        active_homework=active,
        overdue_homework=overdue
    )


@homework_bp.route('/upcoming')
def upcoming():
    """Предстоящие домашние задания (API)"""
    limit = request.args.get('limit', 10, type=int)
    
    upcoming_homework = Homework.get_upcoming(limit=limit)
    
    return jsonify({
        'homework': [hw.to_dict() for hw in upcoming_homework],
        'count': len(upcoming_homework)
    })


@homework_bp.route('/calendar')
def calendar():
    """Календарь домашних заданий"""
    all_homework = Homework.get_all()
    
    # Группируем по месяцам
    from collections import defaultdict
    homework_by_month = defaultdict(list)
    
    for hw in all_homework:
        try:
            date = datetime.strptime(hw.date, '%Y-%m-%d')
            month_key = date.strftime('%Y-%m')
            hw.days_left = calculate_days_left(hw.date, hw.time, hw.due_date)
            homework_by_month[month_key].append(hw)
        except:
            pass
    
    return render_template(
        'pages/homework_calendar.html',
        homework_by_month=dict(homework_by_month)
    )


@homework_bp.route('/export/<format>')
def export(format):
    """Экспорт домашних заданий"""
    all_homework = Homework.get_all()
    
    if format == 'json':
        return jsonify({
            'homework': [hw.to_dict() for hw in all_homework],
            'exported_at': datetime.now().isoformat(),
            'count': len(all_homework)
        })
    
    elif format == 'ics':
        from utils.calendar_utils import generate_calendar_for_homework
        
        ical_content = generate_calendar_for_homework(all_homework)
        
        from flask import make_response
        response = make_response(ical_content)
        response.headers['Content-Type'] = 'text/calendar'
        response.headers['Content-Disposition'] = 'attachment; filename=homework.ics'
        
        return response
    
    else:
        flash('❌ Nezināms eksporta formāts', 'danger')
        return redirect(url_for('homework.index'))


@homework_bp.route('/search')
def search():
    """Поиск домашних заданий"""
    query = request.args.get('q', '').strip()
    
    if not query:
        return redirect(url_for('homework.index'))
    
    results = Homework.search(query)
    
    # Добавляем days_left
    for hw in results:
        hw.days_left = calculate_days_left(hw.date, hw.time, hw.due_date)
    
    return render_template(
        'pages/homework_search.html',
        results=results,
        query=query,
        count=len(results)
    )


@homework_bp.route('/stats')
def stats():
    """Статистика домашних заданий"""
    all_homework = Homework.get_all()
    
    from collections import defaultdict
    
    # Статистика по предметам
    by_subject = defaultdict(int)
    by_type = defaultdict(int)
    by_status = {'active': 0, 'overdue': 0}
    
    for hw in all_homework:
        by_subject[hw.subject] += 1
        by_type[hw.type] += 1
        
        days_left = calculate_days_left(hw.date, hw.time, hw.due_date)
        if days_left >= 0:
            by_status['active'] += 1
        else:
            by_status['overdue'] += 1
    
    stats_data = {
        'total': len(all_homework),
        'by_subject': dict(by_subject),
        'by_type': dict(by_type),
        'by_status': by_status
    }
    
    return jsonify(stats_data)


@homework_bp.route('/mark-complete/<int:homework_id>', methods=['POST'])
def mark_complete(homework_id):
    """Отметить домашнее задание как выполненное (для будущей функциональности)"""
    # Эта функция может быть расширена в будущем
    # для отслеживания выполненных заданий пользователем
    
    flash('✅ Функция būs pieejama nākotnē!', 'info')
    return redirect(url_for('homework.detail', homework_id=homework_id))