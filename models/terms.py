"""
Модель для условий использования (Terms)
"""
from datetime import datetime
from models.database import get_db_connection, is_postgresql_connection


def init_terms_table():
    """Инициализирует таблицу условий использования"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        if is_postgresql_connection(conn):
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS terms (
                    id SERIAL PRIMARY KEY,
                    content TEXT NOT NULL,
                    updated_date TEXT
                )
            ''')
        else:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS terms (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT NOT NULL,
                    updated_date TEXT
                )
            ''')
        
        # Добавляем начальные данные
        cursor.execute('SELECT COUNT(*) FROM terms')
        count = cursor.fetchone()[0]
        
        if count == 0:
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M')
            if is_postgresql_connection(conn):
                cursor.execute(
                    'INSERT INTO terms (content, updated_date) VALUES (%s, %s)',
                    ('Šeit būs lietošanas noteikumi...', current_time)
                )
            else:
                cursor.execute(
                    'INSERT INTO terms (content, updated_date) VALUES (?, ?)',
                    ('Šeit būs lietošanas noteikumi...', current_time)
                )
        
        conn.commit()
        print("✅ Terms table initialized")
    except Exception as e:
        print(f"❌ Error initializing terms table: {e}")
        conn.rollback()
    finally:
        conn.close()


def load_terms():
    """Загружает условия использования"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT content FROM terms ORDER BY id DESC LIMIT 1')
        terms = cursor.fetchone()
        
        if terms:
            if is_postgresql_connection(conn):
                return terms[0]
            else:
                return terms['content']
        return 'Šeit būs lietošanas noteikumi...'
    except Exception as e:
        print(f"❌ Error loading terms: {e}")
        return 'Šeit būs lietošanas noteikumi...'
    finally:
        conn.close()


def save_terms(content):
    """Сохраняет новые условия использования"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M')
        
        if is_postgresql_connection(conn):
            cursor.execute(
                'INSERT INTO terms (content, updated_date) VALUES (%s, %s)',
                (content, current_time)
            )
        else:
            cursor.execute(
                'INSERT INTO terms (content, updated_date) VALUES (?, ?)',
                (content, current_time)
            )
        
        conn.commit()
        print("✅ Terms saved")
        return True
    except Exception as e:
        print(f"❌ Error saving terms: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()