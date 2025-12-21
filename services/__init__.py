"""
Сервисы - заглушки для остальных модулей
"""

# ================= scheduler_service.py =================
def start_scheduler():
    """Запускает планировщик задач"""
    import threading
    import time
    from datetime import datetime
    
    def scheduler_worker():
        """Фоновый процесс планировщика"""
        print("✅ Scheduler started")
        last_check_date = None
        
        while True:
            try:
                now = datetime.now()
                current_time = now.strftime("%H:%M")
                today_date = now.strftime("%Y-%m-%d")
                
                # Проверка в 08:00
                if current_time >= "08:00" and current_time <= "08:05":
                    if last_check_date != today_date:
                        print(f"🕐 Running daily check: {current_time}")
                        # Здесь вызывается функция проверки уведомлений
                        # check_upcoming_work()
                        last_check_date = today_date
                        print("✅ Daily check complete")
                
                time.sleep(60)  # Проверка каждую минуту
            except Exception as e:
                print(f"❌ Scheduler error: {e}")
                time.sleep(300)
    
    scheduler_thread = threading.Thread(target=scheduler_worker, daemon=True)
    scheduler_thread.start()


# ================= websocket_service.py =================
def register_socketio_handlers(socketio):
    """Регистрирует WebSocket обработчики"""
    from flask_socketio import emit
    
    online_users = set()
    
    @socketio.on('connect')
    def handle_connect():
        """Новый пользователь подключился"""
        user_id = None  # request.sid в реальном использовании
        online_users.add(user_id)
        emit('online_count_update', {'count': len(online_users)}, broadcast=True)
        print(f"✅ User connected. Online: {len(online_users)}")
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Пользователь отключился"""
        user_id = None  # request.sid в реальном использовании
        if user_id in online_users:
            online_users.remove(user_id)
        emit('online_count_update', {'count': len(online_users)}, broadcast=True)
        print(f"❌ User disconnected. Online: {len(online_users)}")


# ================= subject_service.py =================
def get_subject_with_stats(subject_name):
    """Получает предмет со статистикой"""
    from models.subjects import get_subject_details
    from models.tests import load_tests
    from models.homework import load_homework
    
    tests = load_tests()
    homework_list = load_homework()
    
    subject_work = []
    
    # Собираем все работы для предмета
    for test in tests:
        if test['subject'] == subject_name:
            test_copy = test.copy()
            test_copy['source'] = 'test'
            subject_work.append(test_copy)
    
    for hw in homework_list:
        if hw['subject'] == subject_name:
            hw_copy = hw.copy()
            hw_copy['source'] = 'homework'
            subject_work.append(hw_copy)
    
    # Сортируем по дате
    subject_work.sort(key=lambda x: x['date'])
    
    subject_details = get_subject_details(subject_name)
    
    return subject_details, subject_work


# ================= timer_service.py =================
def get_user_timer_stats(user_id):
    """Получает статистику таймера пользователя"""
    from datetime import datetime
    from models.database import get_db_connection
    
    today = datetime.now().strftime('%Y-%m-%d')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Сегодняшнее время
    cursor.execute(
        'SELECT SUM(seconds) as total FROM timer_sessions WHERE user_id = ? AND date = ?',
        (user_id, today)
    )
    today_result = cursor.fetchone()
    today_seconds = today_result[0] if today_result and today_result[0] else 0
    
    # Общее время
    cursor.execute(
        'SELECT SUM(seconds) as total FROM timer_sessions WHERE user_id = ?',
        (user_id,)
    )
    total_result = cursor.fetchone()
    total_seconds = total_result[0] if total_result and total_result[0] else 0
    
    conn.close()
    
    return {
        'today_seconds': today_seconds,
        'total_seconds': total_seconds,
        'user_id': user_id[:8]
    }


def save_timer_data(user_id, seconds):
    """Сохраняет данные таймера"""
    from datetime import datetime
    from models.database import get_db_connection
    
    today = datetime.now().strftime('%Y-%m-%d')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Проверяем существующую сессию
        cursor.execute(
            'SELECT id FROM timer_sessions WHERE user_id = ? AND date = ?',
            (user_id, today)
        )
        existing = cursor.fetchone()
        
        if existing:
            # Обновляем
            cursor.execute(
                'UPDATE timer_sessions SET seconds = ? WHERE id = ?',
                (seconds, existing[0])
            )
        else:
            # Создаем новую
            cursor.execute(
                'INSERT INTO timer_sessions (user_id, seconds, date, created_at) VALUES (?, ?, ?, ?)',
                (user_id, seconds, today, datetime.now().strftime('%Y-%m-%d %H:%M'))
            )
        
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ Error saving timer data: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


# ================= theme_service.py =================
def save_user_theme(device_id, theme):
    """Сохраняет тему пользователя"""
    from datetime import datetime
    from models.database import get_db_connection, is_postgresql_connection
    from models.users import get_user_settings
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        existing_settings = get_user_settings(device_id)
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if existing_settings:
            # Обновляем
            if is_postgresql_connection(conn):
                cursor.execute(
                    'UPDATE user_settings SET theme = %s, updated_date = %s WHERE device_id = %s',
                    (theme, current_time, device_id)
                )
            else:
                cursor.execute(
                    'UPDATE user_settings SET theme = ?, updated_date = ? WHERE device_id = ?',
                    (theme, current_time, device_id)
                )
        else:
            # Создаем новый
            if is_postgresql_connection(conn):
                cursor.execute(
                    'INSERT INTO user_settings (device_id, theme, created_date, updated_date) VALUES (%s, %s, %s, %s)',
                    (device_id, theme, current_time, current_time)
                )
            else:
                cursor.execute(
                    'INSERT INTO user_settings (device_id, theme, created_date, updated_date) VALUES (?, ?, ?, ?)',
                    (device_id, theme, current_time, current_time)
                )
        
        conn.commit()
        print(f"✅ Theme saved for device: {device_id}")
        return True
    except Exception as e:
        print(f"❌ Error saving theme: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def save_custom_theme(device_id, settings):
    """Сохраняет кастомную тему"""
    import json
    from datetime import datetime
    from models.database import get_db_connection, is_postgresql_connection
    from models.users import get_user_settings
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        settings_json = json.dumps(settings)
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        existing_settings = get_user_settings(device_id)
        
        if existing_settings:
            # Обновляем
            if is_postgresql_connection(conn):
                cursor.execute(
                    'UPDATE user_settings SET custom_background = %s, updated_date = %s WHERE device_id = %s',
                    (settings_json, current_time, device_id)
                )
            else:
                cursor.execute(
                    'UPDATE user_settings SET custom_background = ?, updated_date = ? WHERE device_id = ?',
                    (settings_json, current_time, device_id)
                )
        else:
            # Создаем новый
            if is_postgresql_connection(conn):
                cursor.execute(
                    'INSERT INTO user_settings (device_id, custom_background, created_date, updated_date) VALUES (%s, %s, %s, %s)',
                    (device_id, settings_json, current_time, current_time)
                )
            else:
                cursor.execute(
                    'INSERT INTO user_settings (device_id, custom_background, created_date, updated_date) VALUES (?, ?, ?, ?)',
                    (device_id, settings_json, current_time, current_time)
                )
        
        conn.commit()
        print(f"✅ Custom theme saved: {device_id}")
        return True
    except Exception as e:
        print(f"❌ Error saving custom theme: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()