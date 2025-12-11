"""
Маршруты для работы с тестами/экзаменами
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime

from models.test import Test
from models.subject import Subject
from utils.decorators import host_required
from utils.validators import validate_test_data
from utils.helpers import calculate_days_left

tests_bp = Blueprint('tests', __name__)


@tests_bp.route('/')
def index():
    """Страница всех тестов"""
    # Получаем все тесты
    all_tests = Test.get_all()
    
    # Разделяем на предстоящие и прошедшие
    upcoming_tests = []
    past_tests = []
    
    for test in all_tests:
        test.days_left = calculate_days_left(test.date, test.time, test.due_date)
        if test.days_left >= 0:
            upcoming_tests.append(test)
        else:
            past_tests.append(test)
    
    # Получаем предметы для фильтра
    subjects = Subject.get_all()
    
    return render_template(
        'pages/all_tests.html',
        upcoming_tests=upcoming_tests,
        past_tests=past_tests,
        subjects=subjects,
        total_count=len(all_tests)
    )


@tests_bp.route('/add', methods=['GET', 'POST'])
@host_required
def add():
    """Добавить тест"""
    if request.method == 'POST':
        # Получаем данные из формы
        data = {
            'subject': request.form.get('subject', '').strip(),
            'type': request.form.get('type', 'Kontroldarbs').strip(),
            'date': request.form.get('date', '').strip(),
            'time': request.form.get('time', '09:00').strip(),
            'description': request.form.get('description', '').strip(),
            'due_date': request.form.get('due_date', '').strip() or None
        }
        
        # Валидация
        is_valid, errors = validate_test_data(data)
        
        if not is_valid:
            for field, error in errors.items():
                flash(f'❌ {error}', 'danger')
            return redirect(url_for('tests.add'))
        
        # Создаем тест
        test = Test(
            subject=data['subject'],
            type=data['type'],
            date=data['date'],
            time=data['time'],
            description=data['description'],
            due_date=data['due_date']
        )
        
        if test.save():
            flash(f'✅ Tests "{test.type}" pievienots priekšmetam {test.subject}!', 'success')
            return redirect(url_for('tests.index'))
        else:
            flash('❌ Kļūda pievienojot testu', 'danger')
    
    # GET запрос - показываем форму
    subjects = Subject.get_all()
    test_types = ['Kontroldarbs', 'Eksāmens', 'Tests', 'Pārbaudes darbs', 'Laboratorijas darbs']
    
    return render_template(
        'forms/add_test.html',
        subjects=subjects,
        test_types=test_types,
        today=datetime.now().strftime('%Y-%m-%d')
    )


@tests_bp.route('/<int:test_id>')
def detail(test_id):
    """Детальная страница теста"""
    test = Test.get_by_id(test_id)
    
    if not test:
        flash('❌ Tests nav atrasts', 'danger')
        return redirect(url_for('tests.index'))
    
    test.days_left = calculate_days_left(test.date, test.time, test.due_date)
    
    # Получаем другие тесты по этому предмету
    related_tests = Test.get_by_subject(test.subject)
    related_tests = [t for t in related_tests if t.id != test_id][:5]
    
    return render_template(
        'pages/test_detail.html',
        test=test,
        related_tests=related_tests
    )


@tests_bp.route('/<int:test_id>/edit', methods=['GET', 'POST'])
@host_required
def edit(test_id):
    """Редактировать тест"""
    test = Test.get_by_id(test_id)
    
    if not test:
        flash('❌ Tests nav atrasts', 'danger')
        return redirect(url_for('tests.index'))
    
    if request.method == 'POST':
        # Обновляем данные
        data = {
            'subject': request.form.get('subject', '').strip(),
            'type': request.form.get('type', 'Kontroldarbs').strip(),
            'date': request.form.get('date', '').strip(),
            'time': request.form.get('time', '09:00').strip(),
            'description': request.form.get('description', '').strip(),
            'due_date': request.form.get('due_date', '').strip() or None
        }
        
        # Валидация
        is_valid, errors = validate_test_data(data)
        
        if not is_valid:
            for field, error in errors.items():
                flash(f'❌ {error}', 'danger')
            return redirect(url_for('tests.edit', test_id=test_id))
        
        # Обновляем объект
        test.subject = data['subject']
        test.type = data['type']
        test.date = data['date']
        test.time = data['time']
        test.description = data['description']
        test.due_date = data['due_date']
        
        if test.save():
            flash(f'✅ Tests atjaunināts!', 'success')
            return redirect(url_for('tests.detail', test_id=test_id))
        else:
            flash('❌ Kļūda atjauninot testu', 'danger')
    
    # GET запрос - показываем форму
    subjects = Subject.get_all()
    test_types = ['Kontroldarbs', 'Eksāmens', 'Tests', 'Pārbaudes darbs', 'Laboratorijas darbs']
    
    return render_template(
        'forms/edit_test.html',
        test=test,
        subjects=subjects,
        test_types=test_types
    )


@tests_bp.route('/<int:test_id>/delete', methods=['POST'])
@host_required
def delete(test_id):
    """Удалить тест"""
    test = Test.get_by_id(test_id)
    
    if not test:
        flash('❌ Tests nav atrasts', 'danger')
        return redirect(url_for('tests.index'))
    
    subject = test.subject
    test_type = test.type
    
    if test.delete():
        flash(f'✅ Tests "{test_type}" priekšmetam {subject} dzēsts!', 'success')
    else:
        flash('❌ Kļūda dzēšot testu', 'danger')
    
    return redirect(url_for('tests.index'))


@tests_bp.route('/by-subject/<subject_name>')
def by_subject(subject_name):
    """Тесты по предмету"""
    tests = Test.get_by_subject(subject_name)
    
    # Добавляем days_left
    for test in tests:
        test.days_left = calculate_days_left(test.date, test.time, test.due_date)
    
    # Разделяем на предстоящие и прошедшие
    upcoming = [t for t in tests if t.days_left >= 0]
    past = [t for t in tests if t.days_left < 0]
    
    subject = Subject.get_by_name(subject_name)
    
    return render_template(
        'pages/tests_by_subject.html',
        subject=subject,
        upcoming_tests=upcoming,
        past_tests=past
    )


@tests_bp.route('/by-type/<test_type>')
def by_type(test_type):
    """Тесты по типу"""
    all_tests = Test.get_all()
    
    # Фильтруем по типу
    filtered_tests = [t for t in all_tests if t.type == test_type]
    
    # Добавляем days_left
    for test in filtered_tests:
        test.days_left = calculate_days_left(test.date, test.time, test.due_date)
    
    # Разделяем на предстоящие и прошедшие
    upcoming = [t for t in filtered_tests if t.days_left >= 0]
    past = [t for t in filtered_tests if t.days_left < 0]
    
    return render_template(
        'pages/tests_by_type.html',
        test_type=test_type,
        upcoming_tests=upcoming,
        past_tests=past,
        total_count=len(filtered_tests)
    )


@tests_bp.route('/upcoming')
def upcoming():
    """Предстоящие тесты (API)"""
    limit = request.args.get('limit', 10, type=int)
    
    upcoming_tests = Test.get_upcoming(limit=limit)
    
    return jsonify({
        'tests': [t.to_dict() for t in upcoming_tests],
        'count': len(upcoming_tests)
    })


@tests_bp.route('/calendar')
def calendar():
    """Календарь тестов"""
    all_tests = Test.get_all()
    
    # Группируем по месяцам
    from collections import defaultdict
    tests_by_month = defaultdict(list)
    
    for test in all_tests:
        try:
            date = datetime.strptime(test.date, '%Y-%m-%d')
            month_key = date.strftime('%Y-%m')
            test.days_left = calculate_days_left(test.date, test.time, test.due_date)
            tests_by_month[month_key].append(test)
        except:
            pass
    
    return render_template(
        'pages/tests_calendar.html',
        tests_by_month=dict(tests_by_month)
    )


@tests_bp.route('/export/<format>')
def export(format):
    """Экспорт тестов"""
    all_tests = Test.get_all()
    
    if format == 'json':
        return jsonify({
            'tests': [t.to_dict() for t in all_tests],
            'exported_at': datetime.now().isoformat(),
            'count': len(all_tests)
        })
    
    elif format == 'ics':
        from utils.calendar_utils import generate_calendar_for_tests
        
        ical_content = generate_calendar_for_tests(all_tests)
        
        from flask import make_response
        response = make_response(ical_content)
        response.headers['Content-Type'] = 'text/calendar'
        response.headers['Content-Disposition'] = 'attachment; filename=tests.ics'
        
        return response
    
    else:
        flash('❌ Nezināms eksporta formāts', 'danger')
        return redirect(url_for('tests.index'))


@tests_bp.route('/search')
def search():
    """Поиск тестов"""
    query = request.args.get('q', '').strip()
    
    if not query:
        return redirect(url_for('tests.index'))
    
    results = Test.search(query)
    
    # Добавляем days_left
    for test in results:
        test.days_left = calculate_days_left(test.date, test.time, test.due_date)
    
    return render_template(
        'pages/tests_search.html',
        results=results,
        query=query,
        count=len(results)
    )


@tests_bp.route('/stats')
def stats():
    """Статистика тестов"""
    all_tests = Test.get_all()
    
    from collections import defaultdict
    
    # Статистика по предметам
    by_subject = defaultdict(int)
    by_type = defaultdict(int)
    by_status = {'upcoming': 0, 'past': 0}
    
    for test in all_tests:
        by_subject[test.subject] += 1
        by_type[test.type] += 1
        
        days_left = calculate_days_left(test.date, test.time, test.due_date)
        if days_left >= 0:
            by_status['upcoming'] += 1
        else:
            by_status['past'] += 1
    
    stats_data = {
        'total': len(all_tests),
        'by_subject': dict(by_subject),
        'by_type': dict(by_type),
        'by_status': by_status
    }
    
    return jsonify(stats_data)


@tests_bp.route('/this-week')
def this_week():
    """Тесты на этой неделе"""
    from datetime import timedelta
    
    all_tests = Test.get_all()
    today = datetime.now()
    week_end = today + timedelta(days=7)
    
    week_tests = []
    
    for test in all_tests:
        try:
            test_date = datetime.strptime(test.date, '%Y-%m-%d')
            if today <= test_date <= week_end:
                test.days_left = calculate_days_left(test.date, test.time, test.due_date)
                week_tests.append(test)
        except:
            pass
    
    # Сортируем по дате
    week_tests.sort(key=lambda x: x.date)
    
    return render_template(
        'pages/tests_this_week.html',
        tests=week_tests,
        count=len(week_tests)
    )


@tests_bp.route('/download/<int:test_id>.ics')
def download_ics(test_id):
    """Скачать отдельный тест как ICS"""
    test = Test.get_by_id(test_id)
    
    if not test:
        flash('❌ Tests nav atrasts', 'danger')
        return redirect(url_for('tests.index'))
    
    from utils.calendar_utils import generate_calendar_for_tests
    
    ical_content = generate_calendar_for_tests([test])
    
    from flask import make_response
    response = make_response(ical_content)
    response.headers['Content-Type'] = 'text/calendar'
    response.headers['Content-Disposition'] = f'attachment; filename=test_{test_id}.ics'
    
    return response