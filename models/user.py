"""
Модель пользователей (для будущего расширения)
"""
from datetime import datetime
from core.database import get_db_connection, is_postgresql


class User:
    """Класс для работы с пользователями"""
    
    def __init__(self, id=None, email='', device_id='', theme='default', 
                 created_date=None):
        self.id = id
        self.email = email
        self.device_id = device_id
        self.theme = theme
        self.created_date = created_date or datetime.now().strftime('%Y-%m-%d %H:%M')
    
    @staticmethod
    def get_by_device_id(device_id):
        """Получить пользователя по device_id"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if is_postgresql(conn):
            cursor.execute('SELECT * FROM user_settings WHERE device_id = %s', (device_id,))
        else:
            cursor.execute('SELECT * FROM user_settings WHERE device_id = ?', (device_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        return User._from_db_row(result) if result else None
    
    @staticmethod
    def get_by_email(email):
        """Получить пользователя по email"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if is_postgresql(conn):
            cursor.execute('SELECT * FROM email_subscriptions WHERE email = %s', (email,))
        else:
            cursor.execute('SELECT * FROM email_subscriptions WHERE email = ?', (email,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            if isinstance(result, dict):
                return {
                    'id': result['id'],
                    'email': result['email'],
                    'notify_1_day': result.get('notify_1_day', True),
                    'notify_3_days': result.get('notify_3_days', True),
                    'is_active': result.get('is_active', True)
                }
            else:
                return {
                    'id': result[0],
                    'email': result[1],
                    'notify_1_day': bool(result[2]) if len(result) > 2 else True,
                    'notify_3_days': bool(result[3]) if len(result) > 3 else True,
                    'is_active': bool(result[4]) if len(result) > 4 else True
                }
        
        return None
    
    def save_settings(self, theme=None, custom_background=None):
        """Сохранить настройки пользователя"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M')
            
            # Проверяем существование
            if is_postgresql(conn):
                cursor.execute('SELECT id FROM user_settings WHERE device_id = %s', (self.device_id,))
            else:
                cursor.execute('SELECT id FROM user_settings WHERE device_id = ?', (self.device_id,))
            
            existing = cursor.fetchone()
            
            if existing:
                # Обновление
                if is_postgresql(conn):
                    if theme:
                        cursor.execute('''
                            UPDATE user_settings 
                            SET theme = %s, updated_date = %s 
                            WHERE device_id = %s
                        ''', (theme, current_time, self.device_id))
                    if custom_background:
                        cursor.execute('''
                            UPDATE user_settings 
                            SET custom_background = %s, updated_date = %s 
                            WHERE device_id = %s
                        ''', (custom_background, current_time, self.device_id))
                else:
                    if theme:
                        cursor.execute('''
                            UPDATE user_settings 
                            SET theme = ?, updated_date = ? 
                            WHERE device_id = ?
                        ''', (theme, current_time, self.device_id))
                    if custom_background:
                        cursor.execute('''
                            UPDATE user_settings 
                            SET custom_background = ?, updated_date = ? 
                            WHERE device_id = ?
                        ''', (custom_background, current_time, self.device_id))
            else:
                # Создание
                if is_postgresql(conn):
                    cursor.execute('''
                        INSERT INTO user_settings (device_id, theme, custom_background, created_date, updated_date)
                        VALUES (%s, %s, %s, %s, %s)
                    ''', (self.device_id, theme or 'default', custom_background, current_time, current_time))
                else:
                    cursor.execute('''
                        INSERT INTO user_settings (device_id, theme, custom_background, created_date, updated_date)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (self.device_id, theme or 'default', custom_background, current_time, current_time))
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"❌ Ошибка сохранения настроек: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    @staticmethod
    def get_timer_stats(user_id):
        """Получить статистику таймера"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        try:
            # Сегодняшнее время
            if is_postgresql(conn):
                cursor.execute('''
                    SELECT SUM(seconds) FROM timer_sessions 
                    WHERE user_id = %s AND date = %s
                ''', (user_id, today))
            else:
                cursor.execute('''
                    SELECT SUM(seconds) FROM timer_sessions 
                    WHERE user_id = ? AND date = ?
                ''', (user_id, today))
            
            today_seconds = cursor.fetchone()[0] or 0
            
            # Общее время
            if is_postgresql(conn):
                cursor.execute('''
                    SELECT SUM(seconds) FROM timer_sessions WHERE user_id = %s
                ''', (user_id,))
            else:
                cursor.execute('''
                    SELECT SUM(seconds) FROM timer_sessions WHERE user_id = ?
                ''', (user_id,))
            
            total_seconds = cursor.fetchone()[0] or 0
            
            conn.close()
            
            return {
                'today_seconds': today_seconds,
                'total_seconds': total_seconds,
                'user_id': user_id
            }
            
        except Exception as e:
            print(f"❌ Ошибка получения статистики: {e}")
            conn.close()
            return {
                'today_seconds': 0,
                'total_seconds': 0,
                'user_id': user_id
            }
    
    @staticmethod
    def save_timer_session(user_id, seconds):
        """Сохранить сессию таймера"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M')
            
            # Проверяем существование
            if is_postgresql(conn):
                cursor.execute('''
                    SELECT id, seconds FROM timer_sessions 
                    WHERE user_id = %s AND date = %s
                ''', (user_id, today))
            else:
                cursor.execute('''
                    SELECT id, seconds FROM timer_sessions 
                    WHERE user_id = ? AND date = ?
                ''', (user_id, today))
            
            existing = cursor.fetchone()
            
            if existing:
                # Обновление
                session_id = existing[0]
                if is_postgresql(conn):
                    cursor.execute('''
                        UPDATE timer_sessions 
                        SET seconds = %s 
                        WHERE id = %s
                    ''', (seconds, session_id))
                else:
                    cursor.execute('''
                        UPDATE timer_sessions 
                        SET seconds = ? 
                        WHERE id = ?
                    ''', (seconds, session_id))
            else:
                # Создание
                if is_postgresql(conn):
                    cursor.execute('''
                        INSERT INTO timer_sessions (user_id, seconds, date, created_at)
                        VALUES (%s, %s, %s, %s)
                    ''', (user_id, seconds, today, current_time))
                else:
                    cursor.execute('''
                        INSERT INTO timer_sessions (user_id, seconds, date, created_at)
                        VALUES (?, ?, ?, ?)
                    ''', (user_id, seconds, today, current_time))
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"❌ Ошибка сохранения таймера: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def to_dict(self):
        """Преобразовать в словарь"""
        return {
            'id': self.id,
            'email': self.email,
            'device_id': self.device_id,
            'theme': self.theme,
            'created_date': self.created_date
        }
    
    @staticmethod
    def _from_db_row(row):
        """Создать объект из строки БД"""
        if not row:
            return None
        
        if isinstance(row, dict):
            return User(
                id=row['id'],
                device_id=row.get('device_id', ''),
                theme=row.get('theme', 'default'),
                created_date=row.get('created_date')
            )
        else:
            return User(
                id=row[0],
                device_id=row[1] if len(row) > 1 else '',
                theme=row[2] if len(row) > 2 else 'default',
                created_date=row[7] if len(row) > 7 else None
            )
    
    def __repr__(self):
        return f"<User {self.device_id}>"