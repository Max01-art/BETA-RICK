"""
Модель для работы с тестами
"""
from datetime import datetime
from functools import lru_cache
from models.database import get_db_connection, is_postgresql_connection
from utils.date_utils import calculate_days_left


def init_tests_table():
    """Инициализирует таблицу тестов"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        if is_postgresql_connection(conn):
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tests (
                    id SERIAL PRIMARY KEY,
                    subject TEXT NOT NULL,
                    type TEXT NOT NULL,
                    date TEXT NOT NULL,
                    time TEXT DEFAULT '23:59',
                    description TEXT,
                    due_date TEXT,
                    added_date TEXT
                )
            ''')
        else:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    subject TEXT NOT NULL,
                    type TEXT NOT NULL,
                    date TEXT NOT NULL,
                    time TEXT DEFAULT '23:59',
                    description TEXT,
                    due_date TEXT,
                    added_date TEXT
                )
            ''')
        
        conn.commit()
        print("✅ Tests table initialized")
    except Exception as e:
        print(f"❌ Error initializing tests table: {e}")
        conn.rollback()
    finally:
        conn.close()


@lru_cache(maxsize=256)
def load_tests():
    """Загружает все тесты с кешированием"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM tests ORDER BY date, time')
        
        if is_postgresql_connection(conn):
            tests_data = cursor.fetchall()
            tests = []
            for row in tests_data:
                test_dict = {}
                for i, column in enumerate(cursor.description):
                    test_dict[column.name] = row[i]
                tests.append(test_dict)
        else:
            tests_data = cursor.fetchall()
            tests = [dict(test) for test in tests_data]
        
        # Добавляем days_left
        for test in tests:
            time_value = test.get('time', '23:59')
            test['days_left'] = calculate_days_left(test['date'], time_value, test.get('due_date'))
        
        print(f"✅ Loaded {len(tests)} tests")
        return tests
    except Exception as e:
        print(f"❌ Error loading tests: {e}")
        return []
    finally:
        conn.close()


def save_test(subject, test_type, date, time, description, due_date=None):
    """Сохраняет новый тест"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M')
        
        if not time:
            time = '23:59'
        
        if is_postgresql_connection(conn):
            cursor.execute(
                'INSERT INTO tests (subject, type, date, time, description, due_date, added_date) VALUES (%s, %s, %s, %s, %s, %s, %s)',
                (subject, test_type, date, time, description, due_date, current_time)
            )
        else:
            cursor.execute(
                'INSERT INTO tests (subject, type, date, time, description, due_date, added_date) VALUES (?, ?, ?, ?, ?, ?, ?)',
                (subject, test_type, date, time, description, due_date, current_time)
            )
        
        conn.commit()
        print(f"✅ Test saved: {subject} - {test_type}")
        load_tests.cache_clear()
        return True
    except Exception as e:
        print(f"❌ Error saving test: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def delete_test(test_id):
    """Удаляет тест"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        if is_postgresql_connection(conn):
            cursor.execute('DELETE FROM tests WHERE id = %s', (test_id,))
        else:
            cursor.execute('DELETE FROM tests WHERE id = ?', (test_id,))
        
        conn.commit()
        print(f"✅ Test deleted: {test_id}")
        load_tests.cache_clear()
        return True
    except Exception as e:
        print(f"❌ Error deleting test: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def get_test_by_id(test_id):
    """Получает тест по ID"""
    tests = load_tests()
    return next((t for t in tests if t['id'] == test_id), None)