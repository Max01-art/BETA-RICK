"""
Модель для обновлений приложения
"""
from datetime import datetime
from core.database import get_db_connection, is_postgresql


class Update:
    """Класс для работы с обновлениями приложения"""
    
    def __init__(self, id=None, title='', content='', date=None, 
                 is_active=True, created_date=None, updated_date=None):
        self.id = id
        self.title = title
        self.content = content
        self.date = date or datetime.now().strftime('%Y-%m-%d')
        self.is_active = is_active
        self.created_date = created_date or datetime.now().strftime('%Y-%m-%d %H:%M')
        self.updated_date = updated_date
    
    @staticmethod
    def get_all():
        """Получить все обновления"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM updates ORDER BY date DESC, created_date DESC')
        results = cursor.fetchall()
        conn.close()
        
        return [Update._from_db_row(row) for row in results]
    
    @staticmethod
    def get_active(limit=None):
        """Получить активные обновления"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if is_postgresql(conn):
            if limit:
                cursor.execute(
                    'SELECT * FROM updates WHERE is_active = TRUE ORDER BY date DESC, created_date DESC LIMIT %s',
                    (limit,)
                )
            else:
                cursor.execute(
                    'SELECT * FROM updates WHERE is_active = TRUE ORDER BY date DESC, created_date DESC'
                )
        else:
            if limit:
                cursor.execute(
                    'SELECT * FROM updates WHERE is_active = 1 ORDER BY date DESC, created_date DESC LIMIT ?',
                    (limit,)
                )
            else:
                cursor.execute(
                    'SELECT * FROM updates WHERE is_active = 1 ORDER BY date DESC, created_date DESC'
                )
        
        results = cursor.fetchall()
        conn.close()
        
        return [Update._from_db_row(row) for row in results]
    
    @staticmethod
    def get_by_id(update_id):
        """Получить обновление по ID"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if is_postgresql(conn):
            cursor.execute('SELECT * FROM updates WHERE id = %s', (update_id,))
        else:
            cursor.execute('SELECT * FROM updates WHERE id = ?', (update_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        return Update._from_db_row(result) if result else None
    
    @staticmethod
    def get_latest(count=5):
        """Получить последние обновления"""
        return Update.get_active(limit=count)
    
    def save(self):
        """Сохранить обновление"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M')
            
            if self.id:
                # Обновление существующей записи
                self.updated_date = current_time
                
                if is_postgresql(conn):
                    cursor.execute('''
                        UPDATE updates 
                        SET title = %s, content = %s, date = %s, 
                            is_active = %s, updated_date = %s
                        WHERE id = %s
                    ''', (self.title, self.content, self.date, 
                          self.is_active, self.updated_date, self.id))
                else:
                    cursor.execute('''
                        UPDATE updates 
                        SET title = ?, content = ?, date = ?, 
                            is_active = ?, updated_date = ?
                        WHERE id = ?
                    ''', (self.title, self.content, self.date, 
                          self.is_active, self.updated_date, self.id))
            else:
                # Создание новой записи
                if is_postgresql(conn):
                    cursor.execute('''
                        INSERT INTO updates (title, content, date, is_active, created_date)
                        VALUES (%s, %s, %s, %s, %s)
                        RETURNING id
                    ''', (self.title, self.content, self.date, self.is_active, self.created_date))
                    self.id = cursor.fetchone()[0]
                else:
                    cursor.execute('''
                        INSERT INTO updates (title, content, date, is_active, created_date)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (self.title, self.content, self.date, self.is_active, self.created_date))
                    self.id = cursor.lastrowid
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"❌ Ошибка сохранения обновления: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def delete(self):
        """Удалить обновление"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            if is_postgresql(conn):
                cursor.execute('DELETE FROM updates WHERE id = %s', (self.id,))
            else:
                cursor.execute('DELETE FROM updates WHERE id = ?', (self.id,))
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"❌ Ошибка удаления обновления: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def toggle_active(self):
        """Переключить активность обновления"""
        self.is_active = not self.is_active
        return self.save()
    
    @staticmethod
    def search(query):
        """Поиск обновлений"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        search_pattern = f'%{query}%'
        
        if is_postgresql(conn):
            cursor.execute('''
                SELECT * FROM updates 
                WHERE title ILIKE %s OR content ILIKE %s
                ORDER BY date DESC
            ''', (search_pattern, search_pattern))
        else:
            cursor.execute('''
                SELECT * FROM updates 
                WHERE title LIKE ? OR content LIKE ?
                ORDER BY date DESC
            ''', (search_pattern, search_pattern))
        
        results = cursor.fetchall()
        conn.close()
        
        return [Update._from_db_row(row) for row in results]
    
    @staticmethod
    def count():
        """Получить количество обновлений"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM updates')
        count = cursor.fetchone()[0]
        conn.close()
        
        return count
    
    @staticmethod
    def count_active():
        """Получить количество активных обновлений"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if is_postgresql(conn):
            cursor.execute('SELECT COUNT(*) FROM updates WHERE is_active = TRUE')
        else:
            cursor.execute('SELECT COUNT(*) FROM updates WHERE is_active = 1')
        
        count = cursor.fetchone()[0]
        conn.close()
        
        return count
    
    def to_dict(self):
        """Преобразовать в словарь"""
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'date': self.date,
            'is_active': self.is_active,
            'created_date': self.created_date,
            'updated_date': self.updated_date
        }
    
    @staticmethod
    def _from_db_row(row):
        """Создать объект из строки БД"""
        if not row:
            return None
        
        if isinstance(row, dict):
            return Update(
                id=row['id'],
                title=row['title'],
                content=row['content'],
                date=row['date'],
                is_active=row.get('is_active', True),
                created_date=row.get('created_date'),
                updated_date=row.get('updated_date')
            )
        else:
            return Update(
                id=row[0],
                title=row[1],
                content=row[2],
                date=row[3],
                is_active=bool(row[4]) if len(row) > 4 else True,
                created_date=row[5] if len(row) > 5 else None,
                updated_date=row[6] if len(row) > 6 else None
            )
    
    def __repr__(self):
        return f"<Update {self.title} - {self.date}>"