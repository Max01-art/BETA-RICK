"""
Модель для работы с домашними заданиями
"""
from datetime import datetime
from core.database import get_db_connection, is_postgresql
from utils.helpers import calculate_days_left


class Homework:
    """Класс для работы с домашними заданиями"""
    
    def __init__(self, id=None, subject=None, title='', date=None, 
                 time='23:59', description='', type='Mājasdarbs', 
                 due_date=None, added_date=None):
        self.id = id
        self.subject = subject
        self.title = title
        self.date = date
        self.time = time
        self.description = description
        self.type = type
        self.due_date = due_date
        self.added_date = added_date or datetime.now().strftime('%Y-%m-%d %H:%M')
    
    @staticmethod
    def get_all(order_by='date, time'):
        """Получить все домашние задания"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(f'SELECT * FROM homework ORDER BY {order_by}')
        results = cursor.fetchall()
        conn.close()
        
        homework_list = [Homework._from_db_row(row) for row in results]
        
        # Добавляем days_left
        for hw in homework_list:
            hw.days_left = calculate_days_left(hw.date, hw.time, hw.due_date)
        
        return homework_list
    
    @staticmethod
    def get_upcoming(limit=None):
        """Получить предстоящие домашние задания"""
        all_homework = Homework.get_all()
        upcoming = [hw for hw in all_homework if hw.days_left >= 0]
        
        if limit:
            return upcoming[:limit]
        return upcoming
    
    @staticmethod
    def get_by_id(homework_id):
        """Получить домашнее задание по ID"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if is_postgresql(conn):
            cursor.execute('SELECT * FROM homework WHERE id = %s', (homework_id,))
        else:
            cursor.execute('SELECT * FROM homework WHERE id = ?', (homework_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            hw = Homework._from_db_row(result)
            hw.days_left = calculate_days_left(hw.date, hw.time, hw.due_date)
            return hw
        return None
    
    @staticmethod
    def get_by_subject(subject_name):
        """Получить домашние задания по предмету"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if is_postgresql(conn):
            cursor.execute('SELECT * FROM homework WHERE subject = %s ORDER BY date, time', (subject_name,))
        else:
            cursor.execute('SELECT * FROM homework WHERE subject = ? ORDER BY date, time', (subject_name,))
        
        results = cursor.fetchall()
        conn.close()
        
        homework_list = [Homework._from_db_row(row) for row in results]
        
        for hw in homework_list:
            hw.days_left = calculate_days_left(hw.date, hw.time, hw.due_date)
        
        return homework_list
    
    def save(self):
        """Сохранить домашнее задание"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            if self.id:
                # Обновление
                if is_postgresql(conn):
                    cursor.execute('''
                        UPDATE homework 
                        SET subject = %s, title = %s, date = %s, time = %s, 
                            description = %s, type = %s, due_date = %s
                        WHERE id = %s
                    ''', (self.subject, self.title, self.date, self.time, 
                          self.description, self.type, self.due_date, self.id))
                else:
                    cursor.execute('''
                        UPDATE homework 
                        SET subject = ?, title = ?, date = ?, time = ?, 
                            description = ?, type = ?, due_date = ?
                        WHERE id = ?
                    ''', (self.subject, self.title, self.date, self.time, 
                          self.description, self.type, self.due_date, self.id))
            else:
                # Создание
                if is_postgresql(conn):
                    cursor.execute('''
                        INSERT INTO homework (subject, title, date, time, description, type, due_date, added_date)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    ''', (self.subject, self.title, self.date, self.time, 
                          self.description, self.type, self.due_date, self.added_date))
                    self.id = cursor.fetchone()[0]
                else:
                    cursor.execute('''
                        INSERT INTO homework (subject, title, date, time, description, type, due_date, added_date)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (self.subject, self.title, self.date, self.time, 
                          self.description, self.type, self.due_date, self.added_date))
                    self.id = cursor.lastrowid
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"❌ Ошибка сохранения домашнего задания: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def delete(self):
        """Удалить домашнее задание"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            if is_postgresql(conn):
                cursor.execute('DELETE FROM homework WHERE id = %s', (self.id,))
            else:
                cursor.execute('DELETE FROM homework WHERE id = ?', (self.id,))
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"❌ Ошибка удаления домашнего задания: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    @staticmethod
    def search(query):
        """Поиск домашних заданий"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        search_pattern = f'%{query}%'
        
        if is_postgresql(conn):
            cursor.execute('''
                SELECT * FROM homework 
                WHERE subject ILIKE %s OR title ILIKE %s OR description ILIKE %s
                ORDER BY date
            ''', (search_pattern, search_pattern, search_pattern))
        else:
            cursor.execute('''
                SELECT * FROM homework 
                WHERE subject LIKE ? OR title LIKE ? OR description LIKE ?
                ORDER BY date
            ''', (search_pattern, search_pattern, search_pattern))
        
        results = cursor.fetchall()
        conn.close()
        
        return [Homework._from_db_row(row) for row in results]
    
    @staticmethod
    def count():
        """Получить количество домашних заданий"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM homework')
        count = cursor.fetchone()[0]
        conn.close()
        
        return count
    
    def to_dict(self):
        """Преобразовать в словарь"""
        return {
            'id': self.id,
            'subject': self.subject,
            'title': self.title,
            'date': self.date,
            'time': self.time,
            'description': self.description,
            'type': self.type,
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
            return Homework(
                id=row['id'],
                subject=row['subject'],
                title=row['title'],
                date=row['date'],
                time=row.get('time', '23:59'),
                description=row.get('description', ''),
                type=row.get('type', 'Mājasdarbs'),
                due_date=row.get('due_date'),
                added_date=row.get('added_date')
            )
        else:
            return Homework(
                id=row[0],
                subject=row[1],
                title=row[2],
                date=row[3],
                time=row[4] if len(row) > 4 else '23:59',
                description=row[5] if len(row) > 5 else '',
                type=row[6] if len(row) > 6 else 'Mājasdarbs',
                due_date=row[7] if len(row) > 7 else None,
                added_date=row[8] if len(row) > 8 else None
            )
    
    def __repr__(self):
        return f"<Homework {self.subject} - {self.title} on {self.date}>"