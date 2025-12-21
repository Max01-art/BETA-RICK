"""
Модель для работы с домашними заданиями
"""
from datetime import datetime
from functools import lru_cache
from models.database import get_db_connection, is_postgresql_connection
from utils.date_utils import calculate_days_left


def init_homework_table():
    """Инициализирует таблицу домашних заданий"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        if is_postgresql_connection(conn):
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS homework (
                    id SERIAL PRIMARY KEY,
                    subject TEXT NOT NULL,
                    title TEXT NOT NULL,
                    date TEXT NOT NULL,
                    time TEXT DEFAULT '23:59',
                    description TEXT,
                    type TEXT DEFAULT 'Mājasdarbs',
                    due_date TEXT,
                    added_date TEXT
                )
            ''')
        else:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS homework (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    subject TEXT NOT NULL,
                    title TEXT NOT NULL,
                    date TEXT NOT NULL,
                    time TEXT DEFAULT '23:59',
                    description TEXT,
                    type TEXT DEFAULT 'Mājasdarbs',
                    due_date TEXT,
                    added_date TEXT
                )
            ''')
        
        conn.commit()
        print("✅ Homework table initialized")
    except Exception as e:
        print(f"❌ Error initializing homework table: {e}")
        conn.rollback()
    finally:
        conn.close()


@lru_cache(maxsize=256)
def load_homework():
    """Загружает все домашние задания с кешированием"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM homework ORDER BY date, time')
        
        if is_postgresql_connection(conn):
            homework_data = cursor.fetchall()
            homework = []
            for row in homework_data:
                hw_dict = {}
                for i, column in enumerate(cursor.description):
                    hw_dict[column.name] = row[i]
                homework.append(hw_dict)
        else:
            homework_data = cursor.fetchall()
            homework = [dict(hw) for hw in homework_data]
        
        # Добавляем days_left
        for hw in homework:
            time_value = hw.get('time', '23:59')
            hw['days_left'] = calculate_days_left(hw['date'], time_value, hw.get('due_date'))
        
        print(f"✅ Loaded {len(homework)} homework items")
        return homework
    except Exception as e:
        print(f"❌ Error loading homework: {e}")
        return []
    finally:
        conn.close()


def save_homework(subject, title, date, time, description, due_date=None):
    """Сохраняет новое домашнее задание"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M')
        
        if not time:
            time = '23:59'
        
        if is_postgresql_connection(conn):
            cursor.execute(
                '''INSERT INTO homework (subject, title, date, time, description, due_date, type, added_date) 
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)''',
                (subject, title, date, time, description, due_date, 'Mājasdarbs', current_time)
            )
        else:
            cursor.execute(
                '''INSERT INTO homework (subject, title, date, time, description, due_date, type, added_date) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                (subject, title, date, time, description, due_date, 'Mājasdarbs', current_time)
            )
        
        conn.commit()
        print(f"✅ Homework saved: {subject} - {title}")
        load_homework.cache_clear()
        return True
    except Exception as e:
        print(f"❌ Error saving homework: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def delete_homework(hw_id):
    """Удаляет домашнее задание"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        if is_postgresql_connection(conn):
            cursor.execute('DELETE FROM homework WHERE id = %s', (hw_id,))
        else:
            cursor.execute('DELETE FROM homework WHERE id = ?', (hw_id,))
        
        conn.commit()
        print(f"✅ Homework deleted: {hw_id}")
        load_homework.cache_clear()
        return True
    except Exception as e:
        print(f"❌ Error deleting homework: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def get_homework_by_id(hw_id):
    """Получает домашнее задание по ID"""
    homework_list = load_homework()
    return next((hw for hw in homework_list if hw['id'] == hw_id), None)