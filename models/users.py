"""
Модели для пользователей и настроек
"""
from datetime import datetime
from models.database import get_db_connection, is_postgresql_connection


def init_user_tables():
    """Инициализирует таблицы пользователей"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # User settings table
        if is_postgresql_connection(conn):
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_settings (
                    id SERIAL PRIMARY KEY,
                    device_id TEXT UNIQUE NOT NULL,
                    theme TEXT DEFAULT 'default',
                    primary_color TEXT DEFAULT '#4361ee',
                    secondary_color TEXT DEFAULT '#3f37c9',
                    bg_gradient TEXT DEFAULT 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    custom_background TEXT,
                    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        else:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT UNIQUE NOT NULL,
                    theme TEXT DEFAULT 'default',
                    primary_color TEXT DEFAULT '#4361ee',
                    secondary_color TEXT DEFAULT '#3f37c9',
                    bg_gradient TEXT DEFAULT 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    custom_background TEXT,
                    created_date TEXT,
                    updated_date TEXT
                )
            ''')
        
        # Timer sessions table
        if is_postgresql_connection(conn):
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS timer_sessions (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    seconds INTEGER NOT NULL,
                    date TEXT NOT NULL,
                    created_at TEXT
                )
            ''')
        else:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS timer_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    seconds INTEGER,
                    date TEXT,
                    created_at TEXT
                )
            ''')
        
        conn.commit()
        print("✅ User tables initialized")
    except Exception as e:
        print(f"❌ Error initializing user tables: {e}")
        conn.rollback()
    finally:
        conn.close()


def get_user_settings(device_id):
    """Получает настройки пользователя"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        if is_postgresql_connection(conn):
            cursor.execute(
                'SELECT theme, custom_background, updated_date FROM user_settings WHERE device_id = %s',
                (device_id,)
            )
        else:
            cursor.execute(
                'SELECT theme, custom_background, updated_date FROM user_settings WHERE device_id = ?',
                (device_id,)
            )
        
        result = cursor.fetchone()
        
        if result:
            if is_postgresql_connection(conn):
                return {
                    'theme': result[0],
                    'custom_background': result[1],
                    'updated_date': result[2]
                }
            else:
                return dict(result)
        
        return None
    except Exception as e:
        print(f"❌ Error getting user settings: {e}")
        return None
    finally:
        conn.close()