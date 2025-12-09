"""
Модель для работы с предметами
"""
from datetime import datetime
from core.database import get_db_connection, is_postgresql


class Subject:
    """Класс для работы с предметами"""
    
    def __init__(self, id=None, name=None, color='#4361ee', description='', created_date=None):
        self.id = id
        self.name = name
        self.color = color
        self.description = description
        self.created_date = created_date or datetime.now().strftime('%Y-%m-%d %H:%M')
    
    @staticmethod
    def get_all(order_by='name'):
        """Получить все предметы"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(f'SELECT * FROM subjects ORDER BY {order_by}')
        results = cursor.fetchall()
        conn.close()
        
        return [Subject._from_db_row(row) for row in results]
    
    @staticmethod
    def get_by_id(subject_id):
        """Получить предмет по ID"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if is_postgresql(conn):
            cursor.execute('SELECT * FROM subjects WHERE id = %s', (subject_id,))
        else:
            cursor.execute('SELECT * FROM subjects WHERE id = ?', (subject_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        return Subject._from_db_row(result) if result else None
    
    @staticmethod
    def get_by_name(name):
        """Получить предмет по названию"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if is_postgresql(conn):
            cursor.execute('SELECT * FROM subjects WHERE name = %s', (name,))
        else:
            cursor.execute('SELECT * FROM subjects WHERE name = ?', (name,))
        
        result = cursor.fetchone()
        conn.close()
        
        return Subject._from_db_row(result) if result else None
    
    def save(self):
        """Сохранить предмет"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            if self.id:
                # Обновление
                if is_postgresql(conn):
                    cursor.execute('''
                        UPDATE subjects 
                        SET name = %s, color = %s, description = %s 
                        WHERE id = %s
                    ''', (self.name, self.color, self.description, self.id))
                else:
                    cursor.execute('''
                        UPDATE subjects 
                        SET name = ?, color = ?, description = ? 
                        WHERE id = ?
                    ''', (self.name, self.color, self.description, self.id))
            else:
                # Создание
                if is_postgresql(conn):
                    cursor.execute('''
                        INSERT INTO subjects (name, color, description, created_date)
                        VALUES (%s, %s, %s, %s)
                        RETURNING id
                    ''', (self.name, self.color, self.description, self.created_date))
                    self.id = cursor.fetchone()[0]
                else:
                    cursor.execute('''
                        INSERT INTO subjects (name, color, description, created_date)
                        VALUES (?, ?, ?, ?)
                    ''', (self.name, self.color, self.description, self.created_date))
                    self.id = cursor.lastrowid
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"❌ Ошибка сохранения предмета: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def delete(self):
        """Удалить предмет и все связанные работы"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Удаляем связанные работы
            if is_postgresql(conn):
                cursor.execute('DELETE FROM tests WHERE subject = %s', (self.name,))
                cursor.execute('DELETE FROM homework WHERE subject = %s', (self.name,))
                cursor.execute('DELETE FROM subjects WHERE id = %s', (self.id,))
            else:
                cursor.execute('DELETE FROM tests WHERE subject = ?', (self.name,))
                cursor.execute('DELETE FROM homework WHERE subject = ?', (self.name,))
                cursor.execute('DELETE FROM subjects WHERE id = ?', (self.id,))
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"❌ Ошибка удаления предмета: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    @staticmethod
    def search(query):
        """Поиск предметов"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        search_pattern = f'%{query}%'
        
        if is_postgresql(conn):
            cursor.execute('''
                SELECT * FROM subjects 
                WHERE name ILIKE %s OR description ILIKE %s
            ''', (search_pattern, search_pattern))
        else:
            cursor.execute('''
                SELECT * FROM subjects 
                WHERE name LIKE ? OR description LIKE ?
            ''', (search_pattern, search_pattern))
        
        results = cursor.fetchall()
        conn.close()
        
        return [Subject._from_db_row(row) for row in results]
    
    @staticmethod
    def count():
        """Получить количество предметов"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM subjects')
        count = cursor.fetchone()[0]
        conn.close()
        
        return count
    
    def get_work_count(self):
        """Получить количество работ по предмету"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if is_postgresql(conn):
            cursor.execute('SELECT COUNT(*) FROM tests WHERE subject = %s', (self.name,))
            tests_count = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM homework WHERE subject = %s', (self.name,))
            homework_count = cursor.fetchone()[0]
        else:
            cursor.execute('SELECT COUNT(*) FROM tests WHERE subject = ?', (self.name,))
            tests_count = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM homework WHERE subject = ?', (self.name,))
            homework_count = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'tests': tests_count,
            'homework': homework_count,
            'total': tests_count + homework_count
        }
    
    def to_dict(self):
        """Преобразовать в словарь"""
        return {
            'id': self.id,
            'name': self.name,
            'color': self.color,
            'description': self.description,
            'created_date': self.created_date
        }
    
    @staticmethod
    def _from_db_row(row):
        """Создать объект из строки БД"""
        if not row:
            return None
        
        # Поддержка как tuple (PostgreSQL), так и dict (SQLite)
        if isinstance(row, dict):
            return Subject(
                id=row['id'],
                name=row['name'],
                color=row.get('color', '#4361ee'),
                description=row.get('description', ''),
                created_date=row.get('created_date')
            )
        else:
            return Subject(
                id=row[0],
                name=row[1],
                color=row[2] if len(row) > 2 else '#4361ee',
                description=row[3] if len(row) > 3 else '',
                created_date=row[4] if len(row) > 4 else None
            )
    
    def __repr__(self):
        return f"<Subject {self.name}>"