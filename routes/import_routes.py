"""
Маршруты для импорта данных (ICS календари, RTU расписание)
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from werkzeug.utils import secure_filename
import os
from datetime import datetime

from utils.decorators import host_required
from utils.calendar_utils import parse_ics_file
from utils.rtu_scraper import RTUScraper, scrape_rtu_schedule, scrape_rtu_exams
from models.test import Test
from models.homework import Homework
from models.subject import Subject

import_routes_bp = Blueprint('import_routes', __name__)


@import_routes_bp.route('/ics', methods=['GET', 'POST'])
@host_required
def import_ics():
    """Импорт из ICS календаря"""
    if request.method == 'POST':
        # Проверяем файл
        if 'ics_file' not in request.files:
            flash('❌ Nav izvēlēts fails', 'danger')
            return redirect(url_for('import_routes.import_ics'))
        
        file = request.files['ics_file']
        
        if file.filename == '':
            flash('❌ Nav izvēlēts fails', 'danger')
            return redirect(url_for('import_routes.import_ics'))
        
        if not file.filename.endswith('.ics'):
            flash('❌ Failam jābūt .ics formātā', 'danger')
            return redirect(url_for('import_routes.import_ics'))
        
        try:
            # Читаем содержимое файла
            content = file.read().decode('utf-8')
            
            # Парсим ICS
            events = parse_ics_file(content)
            
            if not events:
                flash('⚠️ ICS failā nav atrasti notikumi', 'warning')
                return redirect(url_for('import_routes.import_ics'))
            
            # Импортируем в БД
            imported_count = 0
            errors = []
            import_type = request.form.get('import_type', 'tests')  # tests or homework
            
            for event in events:
                try:
                    # Создаем/обновляем предмет
                    subject_name = event.get('subject', event.get('summary', 'Nezināms'))
                    subject = Subject.get_by_name(subject_name)
                    
                    if not subject:
                        subject = Subject(name=subject_name)
                        subject.save()
                    
                    # Создаем тест или домашнее задание
                    if import_type == 'tests':
                        test = Test(
                            subject=subject_name,
                            type=event.get('type', 'Kontroldarbs'),
                            date=event.get('date'),
                            time=event.get('time', '09:00'),
                            description=event.get('description', '')
                        )
                        test.save()
                    else:
                        hw = Homework(
                            subject=subject_name,
                            title=event.get('summary', ''),
                            date=event.get('date'),
                            time=event.get('time', '23:59'),
                            description=event.get('description', '')
                        )
                        hw.save()
                    
                    imported_count += 1
                    
                except Exception as e:
                    errors.append(f"Kļūda importējot '{event.get('summary')}': {str(e)}")
            
            # Результаты
            if imported_count > 0:
                flash(f'✅ Veiksmīgi importēti {imported_count} notikumi!', 'success')
            
            if errors:
                for error in errors[:5]:  # Показываем только первые 5 ошибок
                    flash(f'⚠️ {error}', 'warning')
            
            return redirect(url_for('main.index'))
            
        except Exception as e:
            flash(f'❌ Kļūda nolasot ICS failu: {str(e)}', 'danger')
            return redirect(url_for('import_routes.import_ics'))
    
    # GET запрос - показываем форму
    return render_template('import_ics.html')


@import_routes_bp.route('/rtu', methods=['GET', 'POST'])
@host_required
def import_rtu():
    """Импорт из RTU расписания"""
    if request.method == 'POST':
        try:
            # Получаем параметры
            program_id = request.form.get('program_id', 1393, type=int)
            course_id = request.form.get('course_id', 1, type=int)
            semester_id = request.form.get('semester_id', 28, type=int)
            import_type = request.form.get('import_type', 'schedule')  # schedule or exams
            
            scraper = RTUScraper()
            
            # Получаем данные
            if import_type == 'exams':
                items = scraper.get_exams(program_id, course_id, semester_id)
                success_message = 'eksāmeni'
            else:
                items = scraper.get_schedule(program_id, course_id, semester_id)
                success_message = 'nodarbības'
            
            if not items:
                flash('⚠️ Nav atrasti dati RTU sistēmā', 'warning')
                return redirect(url_for('import_routes.import_rtu'))
            
            # Импортируем
            stats = scraper.import_to_database(items, import_type)
            
            if stats['imported'] > 0:
                flash(f'✅ Veiksmīgi importēti {stats["imported"]} {success_message}!', 'success')
            
            if stats['errors'] > 0:
                flash(f'⚠️ Kļūdas: {stats["errors"]}', 'warning')
            
            return redirect(url_for('main.index'))
            
        except Exception as e:
            flash(f'❌ Kļūda importējot no RTU: {str(e)}', 'danger')
            return redirect(url_for('import_routes.import_rtu'))
    
    # GET запрос - показываем форму
    return render_template('import_rtu.html')


@import_routes_bp.route('/json', methods=['GET', 'POST'])
@host_required
def import_json():
    """Импорт из JSON файла"""
    if request.method == 'POST':
        if 'json_file' not in request.files:
            flash('❌ Nav izvēlēts fails', 'danger')
            return redirect(url_for('import_routes.import_json'))
        
        file = request.files['json_file']
        
        if file.filename == '':
            flash('❌ Nav izvēlēts fails', 'danger')
            return redirect(url_for('import_routes.import_json'))
        
        if not file.filename.endswith('.json'):
            flash('❌ Failam jābūt .json formātā', 'danger')
            return redirect(url_for('import_routes.import_json'))
        
        try:
            import json
            
            # Читаем JSON
            content = file.read().decode('utf-8')
            data = json.loads(content)
            
            imported = {
                'subjects': 0,
                'tests': 0,
                'homework': 0
            }
            
            # Импортируем предметы
            if 'subjects' in data:
                for item in data['subjects']:
                    try:
                        subject = Subject(
                            name=item['name'],
                            color=item.get('color', '#4361ee'),
                            description=item.get('description', '')
                        )
                        if subject.save():
                            imported['subjects'] += 1
                    except:
                        pass
            
            # Импортируем тесты
            if 'tests' in data:
                for item in data['tests']:
                    try:
                        test = Test(
                            subject=item['subject'],
                            type=item['type'],
                            date=item['date'],
                            time=item.get('time', '09:00'),
                            description=item.get('description', '')
                        )
                        if test.save():
                            imported['tests'] += 1
                    except:
                        pass
            
            # Импортируем домашние задания
            if 'homework' in data:
                for item in data['homework']:
                    try:
                        hw = Homework(
                            subject=item['subject'],
                            title=item['title'],
                            date=item['date'],
                            time=item.get('time', '23:59'),
                            description=item.get('description', '')
                        )
                        if hw.save():
                            imported['homework'] += 1
                    except:
                        pass
            
            # Результаты
            total = sum(imported.values())
            
            if total > 0:
                flash(f'✅ Importēti: {imported["subjects"]} priekšmeti, {imported["tests"]} testi, {imported["homework"]} mājasdarbi', 'success')
            else:
                flash('⚠️ Nav importēti dati', 'warning')
            
            return redirect(url_for('main.index'))
            
        except json.JSONDecodeError:
            flash('❌ Nederīgs JSON formāts', 'danger')
        except Exception as e:
            flash(f'❌ Kļūda importējot: {str(e)}', 'danger')
        
        return redirect(url_for('import_routes.import_json'))
    
    # GET запрос - показываем форму
    return render_template('import_json.html')


@import_routes_bp.route('/bulk', methods=['GET', 'POST'])
@host_required
def bulk_import():
    """Массовый импорт через текстовое поле"""
    if request.method == 'POST':
        try:
            import_text = request.form.get('import_text', '').strip()
            import_type = request.form.get('import_type', 'tests')
            
            if not import_text:
                flash('❌ Nav ievadīti dati', 'danger')
                return redirect(url_for('import_routes.bulk_import'))
            
            # Парсим каждую строку
            lines = import_text.split('\n')
            imported_count = 0
            errors = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                try:
                    # Формат: Предмет | Название | Дата | Время
                    parts = [p.strip() for p in line.split('|')]
                    
                    if len(parts) < 3:
                        errors.append(f"Nepareiza rinda: {line}")
                        continue
                    
                    subject = parts[0]
                    title = parts[1]
                    date = parts[2]
                    time = parts[3] if len(parts) > 3 else '09:00' if import_type == 'tests' else '23:59'
                    
                    # Создаем предмет если нужно
                    subj = Subject.get_by_name(subject)
                    if not subj:
                        subj = Subject(name=subject)
                        subj.save()
                    
                    # Создаем работу
                    if import_type == 'tests':
                        test = Test(
                            subject=subject,
                            type='Kontroldarbs',
                            date=date,
                            time=time,
                            description=title
                        )
                        test.save()
                    else:
                        hw = Homework(
                            subject=subject,
                            title=title,
                            date=date,
                            time=time
                        )
                        hw.save()
                    
                    imported_count += 1
                    
                except Exception as e:
                    errors.append(f"Kļūda rindā '{line}': {str(e)}")
            
            # Результаты
            if imported_count > 0:
                flash(f'✅ Veiksmīgi importēti {imported_count} ieraksti!', 'success')
            
            if errors:
                for error in errors[:5]:
                    flash(f'⚠️ {error}', 'warning')
            
            return redirect(url_for('main.index'))
            
        except Exception as e:
            flash(f'❌ Kļūda importējot: {str(e)}', 'danger')
            return redirect(url_for('import_routes.bulk_import'))
    
    # GET запрос - показываем форму
    return render_template('import_bulk.html')


@import_routes_bp.route('/status')
def import_status():
    """Статус возможностей импорта (API)"""
    return jsonify({
        'available_imports': [
            {'type': 'ics', 'name': 'ICS Calendar', 'enabled': True},
            {'type': 'rtu', 'name': 'RTU Schedule', 'enabled': True},
            {'type': 'json', 'name': 'JSON Import', 'enabled': True},
            {'type': 'bulk', 'name': 'Bulk Text Import', 'enabled': True}
        ],
        'supported_formats': ['.ics', '.json', 'text'],
        'max_file_size': '16MB'
    })