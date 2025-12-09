"""
Управление предметами
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from models.subject import Subject
from models.test import Test
from models.homework import Homework
from utils.decorators import host_required
from utils.helpers import get_work_by_subject

subjects_bp = Blueprint('subjects', __name__)


@subjects_bp.route('/')
def list_subjects():
    """Список всех предметов"""
    subjects = Subject.get_all()
    work_by_subject = get_work_by_subject()
    
    return render_template(
        'pages/subjects.html',
        subjects=subjects,
        work_by_subject=work_by_subject
    )


@subjects_bp.route('/add', methods=['GET', 'POST'])
@host_required
def add_subject():
    """Добавить новый предмет"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        color = request.form.get('color', '#4361ee')
        description = request.form.get('description', '')
        
        if not name:
            flash('Nosaukums ir obligāts!', 'error')
            return render_template('forms/add_subject.html')
        
        # Проверка на дубликаты
        existing = Subject.get_by_name(name)
        if existing:
            flash('Šāds priekšmets jau eksistē!', 'warning')
            return render_template('forms/add_subject.html')
        
        subject = Subject(name=name, color=color, description=description)
        
        if subject.save():
            flash(f'Priekšmets "{name}" veiksmīgi pievienots!', 'success')
            return redirect(url_for('main.index'))
        else:
            flash('Kļūda pievienojot priekšmetu!', 'error')
    
    return render_template('forms/add_subject.html')


@subjects_bp.route('/<int:subject_id>')
def subject_detail(subject_id):
    """Детальная страница предмета"""
    subject = Subject.get_by_id(subject_id)
    
    if not subject:
        flash('Priekšmets nav atrasts!', 'error')
        return redirect(url_for('main.index'))
    
    # Получаем все работы по предмету
    tests = Test.get_by_subject(subject.name)
    homework = Homework.get_by_subject(subject.name)
    
    # Объединяем и сортируем
    all_work = []
    
    for test in tests:
        work_dict = test.to_dict()
        work_dict['source'] = 'test'
        all_work.append(work_dict)
    
    for hw in homework:
        work_dict = hw.to_dict()
        work_dict['source'] = 'homework'
        all_work.append(work_dict)
    
    # Сортировка по дате
    all_work.sort(key=lambda x: x['date'])
    
    # Статистика
    work_count = subject.get_work_count()
    
    return render_template(
        'pages/subject_detail.html',
        subject=subject,
        work=all_work,
        work_count=work_count
    )


@subjects_bp.route('/<int:subject_id>/edit', methods=['GET', 'POST'])
@host_required
def edit_subject(subject_id):
    """Редактировать предмет"""
    subject = Subject.get_by_id(subject_id)
    
    if not subject:
        flash('Priekšmets nav atrasts!', 'error')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        subject.name = request.form.get('name', '').strip()
        subject.color = request.form.get('color', '#4361ee')
        subject.description = request.form.get('description', '')
        
        if subject.save():
            flash('Priekšmets atjaunināts!', 'success')
            return redirect(url_for('subjects.subject_detail', subject_id=subject.id))
        else:
            flash('Kļūda atjauninot!', 'error')
    
    return render_template('forms/edit_subject.html', subject=subject)


@subjects_bp.route('/<int:subject_id>/delete', methods=['POST'])
@host_required
def delete_subject(subject_id):
    """Удалить предмет"""
    subject = Subject.get_by_id(subject_id)
    
    if not subject:
        flash('Priekšmets nav atrasts!', 'error')
        return redirect(url_for('main.index'))
    
    subject_name = subject.name
    
    if subject.delete():
        flash(f'Priekšmets "{subject_name}" un visi tā darbi dzēsti!', 'success')
    else:
        flash('Kļūda dzēšot priekšmetu!', 'error')
    
    return redirect(url_for('main.index'))


@subjects_bp.route('/api/search')
def api_search_subjects():
    """API поиск предметов"""
    query = request.args.get('q', '').strip()
    
    if not query:
        return jsonify({'subjects': []})
    
    subjects = Subject.search(query)
    
    return jsonify({
        'subjects': [s.to_dict() for s in subjects]
    })


@subjects_bp.route('/api/<int:subject_id>/stats')
def api_subject_stats(subject_id):
    """API статистика предмета"""
    subject = Subject.get_by_id(subject_id)
    
    if not subject:
        return jsonify({'error': 'Not found'}), 404
    
    work_count = subject.get_work_count()
    
    return jsonify({
        'subject': subject.to_dict(),
        'work_count': work_count
    })