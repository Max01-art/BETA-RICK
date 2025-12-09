"""
Модель для работы с новостями
"""
from datetime import datetime
from core.database import get_db_connection, is_postgresql


class News:
    """Класс для работы с новостями"""
    
    def __init__(self, id=None, title='', content='', date=None, 
                 image_url='', is_active=True, created_date=None, updated_date=None):
        self.id = id
        self.title = title
        self.content = content
        self.date = date or datetime.now().strftime('%Y-%m-%d')
        self.image_url = image_url
        self.is_active = is_active
        self.created_date = created_date or datetime.now().strftime('%Y-%m-%d %H:%M')
        self.updated_date = updated_date
    
    @staticmethod
    def get_all(order_by='date DESC'):
        """Получить все новости"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(f'SELECT * FROM news ORDER BY {order_by}')
        results = cursor.fetchall()
        conn.close()
        
        return [News._from_db_row(row) for row in results]
    
    @staticmethod
    def get_active(limit=None):
        """Получить активные новости"""
        all_news = News.get_all()
        active = [n for n in all_news if n.is_active]
        
        if limit:
            return active[:limit]
        return active
    
    @staticmethod
    def get_by_id(news_id):
        """Получить новость по ID"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if is_postgresql(conn):
            cursor.execute('SELECT * FROM news WHERE id = %s', (news_id,))
        else:
            cursor.execute('SELECT * FROM news WHERE id = ?', (news_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        return News._from_db_row(result) if result else None
    
    def save(self):
        """Сохранить новость"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            if self.id:
                # Обновление
                self.updated_date = datetime.now().strftime('%Y-%m-%d %H:%M')
                
                if is_postgresql(conn):
                    cursor.execute('''
                        UPDATE news 
                        SET title = %s, content = %s, date = %s, image_url = %s, 
                            is_active = %s, updated_date = %s
                        WHERE id = %s
                    ''', (self.title, self.content, self.date, self.image_url, 
                          self.is_active, self.updated_date, self.id))
                else:
                    cursor.execute('''
                        UPDATE news 
                        SET title = ?, content = ?, date = ?, image_url = ?, 
                            is_active = ?, updated_date = ?
                        WHERE id = ?
                    ''', (self.title, self.content, self.date, self.image_url, 
                          1 if self.is_active else 0, self.updated_date, self.id))
            else:
                # Создание
                if is_postgresql(conn):
                    cursor.execute('''
                        INSERT INTO news (title, content, date, image_url, is_active, created_date)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        RETURNING id
                    ''', (self.title, self.content, self.date, self.image_url, 
                          self.is_active, self.created_date))
                    self.id = cursor.fetchone()[0]
                else:
                    cursor.execute('''
                        INSERT INTO news (title, content, date, image_url, is_active, created_date)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (self.title, self.content, self.date, self.image_url, 
                          1 if self.is_active else 0, self.created_date))
                    self.id = cursor.lastrowid
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"❌ Ошибка сохранения новости: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def delete(self):
        """Удалить новость"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            if is_postgresql(conn):
                cursor.execute('DELETE FROM news WHERE id = %s', (self.id,))
            else:
                cursor.execute('DELETE FROM news WHERE id = ?', (self.id,))
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"❌ Ошибка удаления новости: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    @staticmethod
    def count():
        """Получить количество новостей"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM news')
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
            'image_url': self.image_url,
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
            return News(
                id=row['id'],
                title=row['title'],
                content=row['content'],
                date=row['date'],
                image_url=row.get('image_url', ''),
                is_active=row.get('is_active', True),
                created_date=row.get('created_date'),
                updated_date=row.get('updated_date')
            )
        else:
            return News(
                id=row[0],
                title=row[1],
                content=row[2],
                date=row[3],
                image_url=row[4] if len(row) > 4 else '',
                is_active=bool(row[5]) if len(row) > 5 else True,
                created_date=row[6] if len(row) > 6 else None,
                updated_date=row[7] if len(row) > 7 else None
            )
    
    def __repr__(self):
        return f"<News {self.title}>"