"""
Авторизация и управление сессиями
"""
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from config import Config

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Страница входа"""
    # Если уже авторизован, редирект
    if session.get('is_host'):
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        password = request.form.get('password', '').strip()
        
        # Проверка пароля из конфигурации
        if password == Config.HOST_PASSWORD:
            session['is_host'] = True
            session.permanent = True
            
            flash('Veiksmīgi ielogojies!', 'success')
            
            # Редирект на страницу, откуда пришли
            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for('main.index'))
        else:
            flash('Nepareiza parole!', 'error')
    
    return render_template('pages/login.html')


@auth_bp.route('/logout')
def logout():
    """Выход из системы"""
    session.pop('is_host', None)
    session.pop('user_id', None)
    
    flash('Tu esi veiksmīgi izlogojies!', 'info')
    return redirect(url_for('main.index'))


@auth_bp.route('/check')
def check_auth():
    """Проверка авторизации (для API)"""
    from flask import jsonify
    
    return jsonify({
        'is_host': session.get('is_host', False),
        'authenticated': 'is_host' in session or 'user_id' in session
    })


@auth_bp.route('/session_info')
def session_info():
    """Информация о сессии (только для авторизованных)"""
    if not session.get('is_host'):
        flash('Nav tiesību!', 'error')
        return redirect(url_for('auth.login'))
    
    session_data = {
        'is_host': session.get('is_host', False),
        'user_id': session.get('user_id'),
        'theme': session.get('theme', 'default'),
        'permanent': session.permanent,
    }
    
    return render_template('pages/session_info.html', session_data=session_data)