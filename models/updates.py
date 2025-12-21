"""
Модель для обновлений (Updates)
"""
from datetime import datetime
from models.database import get_db_connection, is_postgresql_connection


def init_updates_table():
    """Инициализирует таблицу обновлений"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        if is_postgresql_connection(conn):
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS updates (
                    id SERIAL PRIMARY KEY,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    date TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_date TEXT,
                    updated_date TEXT
                )
            ''')
        else:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS updates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    date TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    created_date TEXT,
                    updated_date TEXT
                )
            ''')
        
        conn.commit()
        print("✅ Updates table initialized")
    except Exception as e:
        print(f"❌ Error initializing updates table: {e}")
        conn.rollback()
    finally:
        conn.close()


def load_updates():
    """Загружает все обновления"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM updates ORDER BY date DESC')
        
        if is_postgresql_connection(conn):
            updates_data = cursor.fetchall()
            updates = []
            for row in updates_data:
                updates.append({
                    'id': row[0],
                    'title': row[1],
                    'content': row[2],
                    'date': row[3],
                    'is_active': row[4],
                    'created_date': row[5],
                    'updated_date': row[6] if len(row) > 6 else None
                })
            return updates
        else:
            updates = cursor.fetchall()
            return [dict(update) for update in updates]
    except Exception as e:
        print(f"❌ Error loading updates: {e}")
        return []
    finally:
        conn.close()


def save_update(title, content, date, is_active):
    """Сохраняет новое обновление"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M')
        
        if is_postgresql_connection(conn):
            cursor.execute(
                'INSERT INTO updates (title, content, date, is_active, created_date) VALUES (%s, %s, %s, %s, %s)',
                (title, content, date, is_active, current_time)
            )
        else:
            cursor.execute(
                'INSERT INTO updates (title, content, date, is_active, created_date) VALUES (?, ?, ?, ?, ?)',
                (title, content, date, is_active, current_time)
            )
        
        conn.commit()
        print(f"✅ Update saved: {title}")
        return True
    except Exception as e:
        print(f"❌ Error saving update: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def update_update(update_id, title, content, date, is_active):
    """Обновляет обновление"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M')
        
        if is_postgresql_connection(conn):
            cursor.execute(
                '''UPDATE updates SET title = %s, content = %s, date = %s, 
                   is_active = %s, updated_date = %s WHERE id = %s''',
                (title, content, date, is_active, current_time, update_id)
            )
        else:
            cursor.execute(
                '''UPDATE updates SET title = ?, content = ?, date = ?, 
                   is_active = ?, updated_date = ? WHERE id = ?''',
                (title, content, date, is_active, current_time, update_id)
            )
        
        conn.commit()
        print(f"✅ Update updated: {update_id}")
        return True
    except Exception as e:
        print(f"❌ Error updating update: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def delete_update(update_id):
    """Удаляет обновление"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        if is_postgresql_connection(conn):
            cursor.execute('DELETE FROM updates WHERE id = %s', (update_id,))
        else:
            cursor.execute('DELETE FROM updates WHERE id = ?', (update_id,))
        
        conn.commit()
        print(f"✅ Update deleted: {update_id}")
        return True
    except Exception as e:
        print(f"❌ Error deleting update: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()