"""
API endpoints для AJAX запросов
"""
from flask import Blueprint, jsonify, request, session
from datetime import datetime
from models.test import Test
from models.homework import Homework
from models.subject import Subject
from models.user import User

api_bp = Blueprint('api', __name__)


@api_bp.route('/next_work')
def api_next_work():
    """Получить следующую работу"""
    try:
        # Получаем предстоящие работы
        tests = Test.get_upcoming(limit=10)
        homework = Homework.get_upcoming(limit=10)
        
        all_work = []
        
        # Преобразуем в словари и добавляем days_left
        for test in tests:
            test_dict = test.to_dict()
            all_work.append(test_dict)
        
        for hw in homework:
            hw_dict = hw.to_dict()
            all_work.append(hw_dict)
        
        if not all_work:
            return jsonify({
                'success': True,
                'next_work': None,
                'message': 'Nav tuvojošos darbu'
            })
        
        # Сортируем по дате
        all_work.sort(key=lambda x: (x['date'], x.get('time', '23:59')))
        
        return jsonify({
            'success': True,
            'next_work': all_work[0],
            'total_upcoming': len(all_work)
        })
        
    except Exception as e:
        print(f"❌ API error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/set_theme', methods=['POST'])
def api_set_theme():
    """Сохранить тему пользователя"""
    try:
        data = request.get_json()
        theme = data.get('theme', 'light')
        
        # Сохраняем в сессии
        session['theme'] = theme
        
        # Сохраняем для устройства (опционально)
        from utils.helpers import generate_device_id
        device_id = generate_device_id()
        
        user = User(device_id=device_id, theme=theme)
        user.save_settings(theme=theme)
        
        return jsonify({
            'success': True,
            'theme': theme
        })
        
    except Exception as e:
        print(f"❌ Theme save error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/timer/stats')
def api_timer_stats():
    """Статистика таймера"""
    try:
        from utils.helpers import generate_device_id
        user_id = generate_device_id()
        
        stats = User.get_timer_stats(user_id)
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        print(f"❌ Timer stats error: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'stats': {
                'today_seconds': 0,
                'total_seconds': 0
            }
        })


@api_bp.route('/timer/save', methods=['POST'])
def api_timer_save():
    """Сохранить сессию таймера"""
    try:
        data = request.get_json()
        seconds = data.get('seconds', 0)
        
        from utils.helpers import generate_device_id
        user_id = generate_device_id()
        
        success = User.save_timer_session(user_id, seconds)
        
        return jsonify({
            'success': success,
            'saved_seconds': seconds
        })
        
    except Exception as e:
        print(f"❌ Timer save error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/search')
def api_search():
    """Универсальный поиск"""
    try:
        query = request.args.get('q', '').strip()
        
        if not query:
            return jsonify({
                'success': True,
                'results': []
            })
        
        # Поиск по всем сущностям
        subjects = Subject.search(query)
        tests = Test.search(query)
        homework = Homework.search(query)
        
        results = {
            'subjects': [s.to_dict() for s in subjects],
            'tests': [t.to_dict() for t in tests],
            'homework': [h.to_dict() for h in homework],
            'total': len(subjects) + len(tests) + len(homework)
        }
        
        return jsonify({
            'success': True,
            'results': results,
            'query': query
        })
        
    except Exception as e:
        print(f"❌ Search error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/stats/summary')
def api_stats_summary():
    """Общая статистика системы"""
    try:
        stats = {
            'subjects_count': Subject.count(),
            'tests_count': Test.count(),
            'homework_count': Homework.count(),
            'upcoming_tests': len(Test.get_upcoming()),
            'upcoming_homework': len(Homework.get_upcoming()),
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        print(f"❌ Stats error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/work/<work_type>/<int:work_id>')
def api_get_work(work_type, work_id):
    """Получить информацию о работе"""
    try:
        if work_type == 'test':
            work = Test.get_by_id(work_id)
        elif work_type == 'homework':
            work = Homework.get_by_id(work_id)
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid work type'
            }), 400
        
        if not work:
            return jsonify({
                'success': False,
                'error': 'Not found'
            }), 404
        
        return jsonify({
            'success': True,
            'work': work.to_dict()
        })
        
    except Exception as e:
        print(f"❌ Get work error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/health')
def api_health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'version': '2.1.0'
    })