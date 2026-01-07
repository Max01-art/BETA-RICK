"""
API маршруты для AJAX запросов
Комбинированная версия со всеми эндпоинтами
"""
from flask import Blueprint, jsonify, request, session
from datetime import datetime
from models.subjects import load_subjects, update_subject
from models.tests import load_tests, save_test, delete_test
from models.homework import load_homework, save_homework, delete_homework
from models.news import load_news
from utils.auth import is_host, login_required
from services.theme_service import save_user_theme, save_custom_theme

api_bp = Blueprint('api', __name__)


# ==================== ПРОВЕРКА СОСТОЯНИЯ ====================

@api_bp.route('/status', methods=['GET'])
def status():
    """Проверка статуса API"""
    return jsonify({
        'success': True,
        'status': 'online',
        'timestamp': datetime.now().isoformat(),
        'is_host': is_host()
    })


@api_bp.route('/stats', methods=['GET'])
def get_stats():
    """Получить общую статистику"""
    tests = load_tests()
    homework_list = load_homework()
    subjects = load_subjects()
    
    today = datetime.now().date()
    today_work = [
        w for w in tests + homework_list 
        if w.get('date') == today.strftime('%Y-%m-%d')
    ]
    
    return jsonify({
        'success': True,
        'stats': {
            'total_tests': len(tests),
            'total_homework': len(homework_list),
            'total_work': len(tests) + len(homework_list),
            'total_subjects': len(subjects),
            'today_work': len(today_work)
        }
    })


# ==================== РАБОТЫ (твой оригинальный функционал) ====================

@api_bp.route('/next_work')
def api_next_work():
    """Возвращает следующую работу (твой оригинальный код)"""
    try:
        tests = load_tests()
        homework_list = load_homework()
        all_work = tests + homework_list
        
        if not all_work:
            return jsonify({
                'success': True,
                'next_work': None,
                'message': 'Nav darbu'
            })
        
        # Находим ближайшую работу
        upcoming_work = []
        today = datetime.now().date()
        
        for work in all_work:
            try:
                work_date = datetime.strptime(work['date'], '%Y-%m-%d').date()
                days_left = (work_date - today).days
                
                if days_left >= 0:
                    work_copy = work.copy()
                    work_copy['days_left'] = days_left
                    upcoming_work.append(work_copy)
            except:
                continue
        
        if not upcoming_work:
            return jsonify({
                'success': True,
                'next_work': None,
                'message': 'Nav tuvojošos darbu'
            })
        
        # Сортируем по близости
        upcoming_work.sort(key=lambda x: x['days_left'])
        next_work = upcoming_work[0]
        
        return jsonify({
            'success': True,
            'next_work': next_work,
            'total_upcoming': len(upcoming_work)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/work', methods=['GET'])
def get_all_work():
    """Получить все работы с фильтрацией (новый функционал)"""
    tests = load_tests()
    homework_list = load_homework()
    all_work = tests + homework_list
    
    # Фильтрация по предмету
    subject = request.args.get('subject')
    if subject:
        all_work = [w for w in all_work if w.get('subject') == subject]
    
    # Фильтрация по дате
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    if date_from:
        all_work = [w for w in all_work if w.get('date', '') >= date_from]
    if date_to:
        all_work = [w for w in all_work if w.get('date', '') <= date_to]
    
    return jsonify({
        'success': True,
        'work': all_work,
        'count': len(all_work)
    })


@api_bp.route('/work/<int:work_id>', methods=['GET'])
def get_work_by_id(work_id):
    """Получить работу по ID (новый функционал)"""
    tests = load_tests()
    homework_list = load_homework()
    all_work = tests + homework_list
    
    work = next((w for w in all_work if w.get('id') == work_id), None)
    
    if not work:
        return jsonify({
            'success': False,
            'error': 'Darbs nav atrasts'
        }), 404
    
    return jsonify({
        'success': True,
        'work': work
    })


@api_bp.route('/work', methods=['POST'])
@login_required
def create_work():
    """Создать новую работу (новый функционал)"""
    data = request.get_json()
    
    if not data:
        return jsonify({
            'success': False,
            'error': 'Nav datu'
        }), 400
    
    work_type = data.get('type', 'test')
    
    try:
        if work_type == 'homework':
            save_homework(
                data.get('subject'),
                data.get('title'),
                data.get('date'),
                data.get('time', '23:59'),
                data.get('description', ''),
                data.get('due_date')
            )
        else:
            save_test(
                data.get('subject'),
                data.get('test_type'),
                data.get('date'),
                data.get('time', '23:59'),
                data.get('description', ''),
                data.get('due_date')
            )
        
        return jsonify({
            'success': True,
            'message': 'Darbs pievienots!'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/work/<int:work_id>', methods=['DELETE'])
@login_required
def delete_work(work_id):
    """Удалить работу (новый функционал)"""
    # Пробуем удалить как тест
    try:
        delete_test(work_id)
        return jsonify({
            'success': True,
            'message': 'Darbs izdzēsts!'
        })
    except:
        pass
    
    # Пробуем удалить как домашнее задание
    try:
        delete_homework(work_id)
        return jsonify({
            'success': True,
            'message': 'Darbs izdzēsts!'
        })
    except:
        pass
    
    return jsonify({
        'success': False,
        'error': 'Darbs nav atrasts'
    }), 404


# ==================== ПРЕДМЕТЫ ====================

@api_bp.route('/subjects', methods=['GET'])
def get_subjects():
    """Получить все предметы (новый функционал)"""
    subjects = load_subjects()
    
    return jsonify({
        'success': True,
        'subjects': subjects,
        'count': len(subjects)
    })


@api_bp.route('/subjects/<int:subject_id>', methods=['GET'])
def get_subject(subject_id):
    """Получить предмет по ID (новый функционал)"""
    from models.subjects import get_subject_by_id
    
    subject = get_subject_by_id(subject_id)
    
    if not subject:
        return jsonify({
            'success': False,
            'error': 'Priekšmets nav atrasts'
        }), 404
    
    return jsonify({
        'success': True,
        'subject': subject
    })


@api_bp.route('/subject/<int:subject_id>/update', methods=['POST'])
@login_required
def api_update_subject(subject_id):
    """Обновляет информацию о предмете (твой оригинальный код)"""
    try:
        data = request.get_json()
        name = data.get('name')
        color = data.get('color')
        description = data.get('description', '')
        
        if update_subject(subject_id, name, color, description):
            return jsonify({'success': True, 'message': 'Priekšmets atjaunināts'})
        else:
            return jsonify({'success': False, 'error': 'Kļūda atjauninot'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


# ==================== НОВОСТИ ====================

@api_bp.route('/news', methods=['GET'])
def get_news():
    """Получить новости (новый функционал)"""
    news_list = load_news()
    
    # Фильтрация активных
    active_only = request.args.get('active', 'true').lower() == 'true'
    if active_only:
        news_list = [n for n in news_list if n.get('is_active', True)]
    
    # Ограничение количества
    limit = request.args.get('limit', type=int)
    if limit:
        news_list = news_list[:limit]
    
    return jsonify({
        'success': True,
        'news': news_list,
        'count': len(news_list)
    })


@api_bp.route('/news/<int:news_id>', methods=['GET'])
def get_news_by_id(news_id):
    """Получить новость по ID (новый функционал)"""
    from models.news import get_news_by_id as get_news
    
    news = get_news(news_id)
    
    if not news:
        return jsonify({
            'success': False,
            'error': 'Ziņa nav atrasta'
        }), 404
    
    return jsonify({
        'success': True,
        'news': news
    })


# ==================== ПОИСК ====================

@api_bp.route('/search', methods=['GET'])
def search():
    """Поиск по работам (новый функционал)"""
    query = request.args.get('q', '').strip()
    
    if not query:
        return jsonify({
            'success': False,
            'error': 'Meklēšanas vaicājums nav norādīts'
        }), 400
    
    tests = load_tests()
    homework_list = load_homework()
    all_work = tests + homework_list
    
    # Поиск
    query_lower = query.lower()
    results = [
        w for w in all_work if 
        query_lower in str(w.get('subject', '')).lower() or
        query_lower in str(w.get('title', '')).lower() or
        query_lower in str(w.get('type', '')).lower() or
        query_lower in str(w.get('description', '')).lower()
    ]
    
    return jsonify({
        'success': True,
        'results': results,
        'count': len(results),
        'query': query
    })


# ==================== КАЛЕНДАРЬ ====================

@api_bp.route('/calendar', methods=['GET'])
def get_calendar_data():
    """Получить данные для календаря (новый функционал)"""
    tests = load_tests()
    homework_list = load_homework()
    all_work = tests + homework_list
    
    # Группировка по датам
    calendar_data = {}
    for work in all_work:
        date = work.get('date')
        if date:
            if date not in calendar_data:
                calendar_data[date] = []
            calendar_data[date].append(work)
    
    return jsonify({
        'success': True,
        'calendar': calendar_data,
        'total_days': len(calendar_data)
    })


# ==================== ТЕМЫ (твой оригинальный функционал) ====================

@api_bp.route('/set_theme', methods=['POST'])
def api_set_theme():
    """Сохраняет тему пользователя (твой оригинальный код)"""
    try:
        data = request.get_json()
        theme = data.get('theme', 'default')
        
        session['theme'] = theme
        device_id = request.remote_addr
        save_user_theme(device_id, theme)
        
        return jsonify({'success': True, 'theme': theme})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@api_bp.route('/save_custom_theme', methods=['POST'])
@login_required
def api_save_custom_theme():
    """Сохраняет кастомные настройки темы (твой оригинальный код)"""
    try:
        data = request.get_json()
        device_id = request.remote_addr
        save_custom_theme(device_id, data)
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@api_bp.route('/theme', methods=['GET'])
def get_theme():
    """Получить текущую тему (новый функционал)"""
    theme = session.get('theme', 'light')
    
    return jsonify({
        'success': True,
        'theme': theme
    })


@api_bp.route('/theme', methods=['POST'])
def set_theme():
    """Установить тему оформления (новый функционал - альтернатива)"""
    data = request.get_json()
    theme = data.get('theme', 'light')
    
    if theme not in ['light', 'dark', 'auto']:
        return jsonify({
            'success': False,
            'error': 'Nepareiza tēma'
        }), 400
    
    session['theme'] = theme
    
    return jsonify({
        'success': True,
        'theme': theme
    })


# ==================== ТАЙМЕР (твой оригинальный функционал) ====================

@api_bp.route('/timer/stats')
def get_timer_stats():
    """Получает статистику таймера (твой оригинальный код)"""
    from services.timer_service import get_user_timer_stats
    
    try:
        user_id = request.remote_addr
        stats = get_user_timer_stats(user_id)
        
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@api_bp.route('/timer/save', methods=['POST'])
def save_timer_session():
    """Сохраняет сессию таймера (твой оригинальный код)"""
    from services.timer_service import save_timer_data
    
    try:
        data = request.get_json()
        seconds = data.get('seconds', 0)
        user_id = request.remote_addr
        
        if save_timer_data(user_id, seconds):
            return jsonify({'success': True, 'saved_seconds': seconds})
        else:
            return jsonify({'success': False, 'error': 'Save failed'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


# ==================== ЭКСПОРТ ====================

@api_bp.route('/export/work', methods=['GET'])
def export_work():
    """Экспорт работ в JSON (новый функционал)"""
    tests = load_tests()
    homework_list = load_homework()
    all_work = tests + homework_list
    
    export_format = request.args.get('format', 'json')
    
    if export_format == 'json':
        return jsonify({
            'success': True,
            'data': all_work,
            'exported_at': datetime.now().isoformat()
        })
    
    return jsonify({
        'success': False,
        'error': 'Neatbalstīts formāts'
    }), 400