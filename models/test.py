"""
Модель для работы с тестами/контрольными
"""
from datetime import datetime
from core.database import get_db_connection, is_postgresql
from utils.helpers import calculate_days_left


class Test:
    """Класс для работы с тестами"""
    
    def __init__(self, id=None, subject=None, type='Kontroldarbs', date=None, 
                 time='23:59', description='', due_date=None, added_date=None):
        self.id = id
        self.subject = subject
        self.type = type
        self.date = date
        self.time = time
        self.description = description
        self.due_date = due_date
        self.added_date = added_date or datetime.now().strftime('%Y-%m-%d %H:%M')
    
    @staticmethod
    def get_all(order_by='date, time'):
        """Получить все тесты"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(f'SELECT * FROM tests ORDER BY {order_by}')
        results = cursor.fetchall()
        conn.close()
        
        tests = [Test._from_db_row(row) for row in results]
        
        # Добавляем days_left
        for test in tests:
            test.days_left = calculate_days_left(test.date, test.time, test.due_date)
        
        return tests
    
    @staticmethod
    def get_upcoming(limit=None):
        """Получить предстоящие тесты"""
        all_tests = Test.get_all()
        upcoming = [t for t in all_tests if t.days_left >= 0]
        
        if limit:
            return upcoming[:limit]
        return upcoming
    
    @staticmethod
    def get_by_id(test_id):
        """Получить тест по ID"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if is_postgresql(conn):
            cursor.execute('SELECT * FROM tests WHERE id = %s', (test_id,))
        else:
            cursor.execute('SELECT * FROM tests WHERE id = ?', (test_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            test = Test._from_db_row(result)
            test.days_left = calculate_days_left(test.date, test.time, test.due_date)
            return test
        return None
    
    @staticmethod
    def get_by_subject(subject_name):
        """Получить тесты по предмету"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if is_postgresql(conn):
            cursor.execute('SELECT * FROM tests WHERE subject = %s ORDER BY date, time', (subject_name,))
        else:
            cursor.execute('SELECT * FROM tests WHERE subject = ? ORDER BY date, time', (subject_name,))
        
        results = cursor.fetchall()
        conn.close()
        
        tests = [Test._from_db_row(row) for row in results]
        
        for test in tests:
            test.days_left = calculate_days_left(test.date, test.time, test.due_date)
        
        return tests
    
    def save(self):
        """Сохранить тест"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            if self.id:
                # Обновление
                if is_postgresql(conn):
                    cursor.execute('''
                        UPDATE tests 
                        SET subject = %s, type = %s, date = %s, time = %s, 
                            description = %s, due_date = %s
                        WHERE id = %s
                    ''', (self.subject, self.type, self.date, self.time, 
                          self.description, self.due_date, self.id))
                else:
                    cursor.execute('''
                        UPDATE tests 
                        SET subject = ?, type = ?, date = ?, time = ?, 
                            description = ?, due_date = ?
                        WHERE id = ?
                    ''', (self.subject, self.type, self.date, self.time, 
                          self.description, self.due_date, self.id))
            else:
                # Создание
                if is_postgresql(conn):
                    cursor.execute('''
                        INSERT INTO tests (subject, type, date, time, description, due_date, added_date)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    ''', (self.subject, self.type, self.date, self.time, 
                          self.description, self.due_date, self.added_date))
                    self.id = cursor.fetchone()[0]
                else:
                    cursor.execute('''
                        INSERT INTO tests (subject, type, date, time, description, due_date, added_date)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (self.subject, self.type, self.date, self.time, 
                          self.description, self.due_date, self.added_date))
                    self.id = cursor.lastrowid
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"❌ Ошибка сохранения теста: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def delete(self):
        """Удалить тест"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            if is_postgresql(conn):
                cursor.execute('DELETE FROM tests WHERE id = %s', (self.id,))
            else:
                cursor.execute('DELETE FROM tests WHERE id = ?', (self.id,))
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"❌ Ошибка удаления теста: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    @staticmethod
    def search(query):
        """Поиск тестов"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        search_pattern = f'%{query}%'
        
        if is_postgresql(conn):
            cursor.execute('''
                SELECT * FROM tests 
                WHERE subject ILIKE %s OR type ILIKE %s OR description ILIKE %s
                ORDER BY date
            ''', (search_pattern, search_pattern, search_pattern))
        else:
            cursor.execute('''
                SELECT * FROM tests 
                WHERE subject LIKE ? OR type LIKE ? OR description LIKE ?
                ORDER BY date
            ''', (search_pattern, search_pattern, search_pattern))
        
        results = cursor.fetchall()
        conn.close()
        
        return [Test._from_db_row(row) for row in results]
    
    @staticmethod
    def count():
        """Получить количество тестов"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM tests')
        count = cursor.fetchone()[0]
        conn.close()
        
        return count
    
    def to_dict(self):
        """Преобразовать в словарь"""
        return {
            'id': self.id,
            'subject': self.subject,
            'type': self.type,
            'date': self.date,
            'time': self.time,
            'description': self.description,
            'due_date': self.due_date,
            'added_date': self.added_date,
            'days_left': getattr(self, 'days_left', None)
        }
    
    @staticmethod
    def _from_db_row(row):
        """Создать объект из строки БД"""
        if not row:
            return None
        
        if isinstance(row, dict):
            return Test(
                id=row['id'],
                subject=row['subject'],
                type=row['type'],
                date=row['date'],
                time=row.get('time', '23:59'),
                description=row.get('description', ''),
                due_date=row.get('due_date'),
                added_date=row.get('added_date')
            )
        else:
            return Test(
                id=row[0],
                subject=row[1],
                type=row[2],
                date=row[3],
                time=row[4] if len(row) > 4 else '23:59',
                description=row[5] if len(row) > 5 else '',
                due_date=row[6] if len(row) > 6 else None,
                added_date=row[7] if len(row) > 7 else None
            )
    
    def __repr__(self):
        return f"<Test {self.subject} - {self.type} on {self.date}>"