"""
Модель для работы с предметами (subjects)
"""
from datetime import datetime
from models.database import get_db_connection, is_postgresql_connection


def init_subjects_table():
    """Инициализирует таблицу предметов"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        if is_postgresql_connection(conn):
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS subjects (
                    id SERIAL PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    color TEXT DEFAULT '#4361ee',
                    created_date TEXT,
                    description TEXT
                )
            ''')
        else:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS subjects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    color TEXT DEFAULT '#4361ee',
                    created_date TEXT,
                    description TEXT
                )
            ''')
        
        conn.commit()
        print("✅ Subjects table initialized")
    except Exception as e:
        print(f"❌ Error initializing subjects table: {e}")
        conn.rollback()
    finally:
        conn.close()


def load_subjects():
    """Загружает все предметы"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM subjects ORDER BY name')
        
        if is_postgresql_connection(conn):
            subjects_data = cursor.fetchall()
            subjects = []
            for row in subjects_data:
                subjects.append({
                    'id': row[0],
                    'name': row[1],
                    'color': row[2],
                    'created_date': row[3],
                    'description': row[4] if len(row) > 4 else ''
                })
            return subjects
        else:
            subjects = cursor.fetchall()
            return [dict(subject) for subject in subjects]
    except Exception as e:
        print(f"❌ Error loading subjects: {e}")
        return []
    finally:
        conn.close()


def save_subject(name, color, description=''):
    """Сохраняет новый предмет"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M')
        
        if is_postgresql_connection(conn):
            cursor.execute(
                'INSERT INTO subjects (name, color, created_date, description) VALUES (%s, %s, %s, %s)',
                (name, color, current_time, description)
            )
        else:
            cursor.execute(
                'INSERT INTO subjects (name, color, created_date, description) VALUES (?, ?, ?, ?)',
                (name, color, current_time, description)
            )
        
        conn.commit()
        print(f"✅ Subject saved: {name}")
        return True
    except Exception as e:
        print(f"❌ Error saving subject: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def delete_subject(subject_id):
    """Удаляет предмет и все связанные работы"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Получаем имя предмета
        if is_postgresql_connection(conn):
            cursor.execute('SELECT name FROM subjects WHERE id = %s', (subject_id,))
        else:
            cursor.execute('SELECT name FROM subjects WHERE id = ?', (subject_id,))
        
        subject_result = cursor.fetchone()
        
        if subject_result:
            subject_name = subject_result[0] if is_postgresql_connection(conn) else subject_result['name']
            
            # Удаляем связанные работы
            if is_postgresql_connection(conn):
                cursor.execute('DELETE FROM tests WHERE subject = %s', (subject_name,))
                cursor.execute('DELETE FROM homework WHERE subject = %s', (subject_name,))
                cursor.execute('DELETE FROM subjects WHERE id = %s', (subject_id,))
            else:
                cursor.execute('DELETE FROM tests WHERE subject = ?', (subject_name,))
                cursor.execute('DELETE FROM homework WHERE subject = ?', (subject_name,))
                cursor.execute('DELETE FROM subjects WHERE id = ?', (subject_id,))
            
            conn.commit()
            print(f"✅ Subject '{subject_name}' deleted")
            return True
    except Exception as e:
        print(f"❌ Error deleting subject: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def get_subject_details(subject_name):
    """Получает детальную информацию о предмете"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        if is_postgresql_connection(conn):
            cursor.execute('SELECT * FROM subjects WHERE name = %s', (subject_name,))
        else:
            cursor.execute('SELECT * FROM subjects WHERE name = ?', (subject_name,))
        
        subject = cursor.fetchone()
        if subject:
            if is_postgresql_connection(conn):
                return {
                    'id': subject[0],
                    'name': subject[1],
                    'color': subject[2],
                    'created_date': subject[3],
                    'description': subject[4] if len(subject) > 4 else ''
                }
            else:
                return dict(subject)
        return None
    except Exception as e:
        print(f"❌ Error getting subject details: {e}")
        return None
    finally:
        conn.close()


def update_subject(subject_id, name, color, description=''):
    """Обновляет информацию о предмете"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        if is_postgresql_connection(conn):
            cursor.execute(
                'UPDATE subjects SET name = %s, color = %s, description = %s WHERE id = %s',
                (name, color, description, subject_id)
            )
        else:
            cursor.execute(
                'UPDATE subjects SET name = ?, color = ?, description = ? WHERE id = ?',
                (name, color, description, subject_id)
            )
        
        conn.commit()
        print(f"✅ Subject updated: {name}")
        return True
    except Exception as e:
        print(f"❌ Error updating subject: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()