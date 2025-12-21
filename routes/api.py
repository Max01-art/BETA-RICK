"""
API маршруты (JSON endpoints)
"""
from flask import Blueprint, jsonify, request, session
from datetime import datetime
from models.tests import load_tests
from models.homework import load_homework
from models.subjects import update_subject
from utils.auth import is_host, login_required
from services.theme_service import save_user_theme, save_custom_theme

api_bp = Blueprint('api', __name__)


@api_bp.route('/next_work')
def api_next_work():
    """Возвращает следующую работу"""
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


@api_bp.route('/set_theme', methods=['POST'])
def api_set_theme():
    """Сохраняет тему пользователя"""
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
    """Сохраняет кастомные настройки темы"""
    try:
        data = request.get_json()
        device_id = request.remote_addr
        save_custom_theme(device_id, data)
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@api_bp.route('/subject/<int:subject_id>/update', methods=['POST'])
@login_required
def api_update_subject(subject_id):
    """Обновляет информацию о предмете"""
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


@api_bp.route('/timer/stats')
def get_timer_stats():
    """Получает статистику таймера"""
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
    """Сохраняет сессию таймера"""
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