"""
Модель для условий использования
"""
from datetime import datetime
from core.database import get_db_connection, is_postgresql


class Terms:
    """Класс для работы с условиями использования"""
    
    def __init__(self, id=None, content='', updated_date=None):
        self.id = id
        self.content = content
        self.updated_date = updated_date or datetime.now().strftime('%Y-%m-%d %H:%M')
    
    @staticmethod
    def get_latest():
        """Получить последнюю версию условий"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM terms ORDER BY updated_date DESC LIMIT 1')
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return Terms._from_db_row(result)
        
        # Если нет записей, создаём дефолтные условия
        default_terms = Terms(
            content=Terms.get_default_content()
        )
        default_terms.save()
        return default_terms
    
    @staticmethod
    def get_by_id(terms_id):
        """Получить условия по ID"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if is_postgresql(conn):
            cursor.execute('SELECT * FROM terms WHERE id = %s', (terms_id,))
        else:
            cursor.execute('SELECT * FROM terms WHERE id = ?', (terms_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        return Terms._from_db_row(result) if result else None
    
    @staticmethod
    def get_all():
        """Получить все версии условий"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM terms ORDER BY updated_date DESC')
        results = cursor.fetchall()
        conn.close()
        
        return [Terms._from_db_row(row) for row in results]
    
    def save(self):
        """Сохранить условия"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M')
            self.updated_date = current_time
            
            if self.id:
                # Обновление существующей записи
                if is_postgresql(conn):
                    cursor.execute('''
                        UPDATE terms 
                        SET content = %s, updated_date = %s
                        WHERE id = %s
                    ''', (self.content, self.updated_date, self.id))
                else:
                    cursor.execute('''
                        UPDATE terms 
                        SET content = ?, updated_date = ?
                        WHERE id = ?
                    ''', (self.content, self.updated_date, self.id))
            else:
                # Создание новой записи
                if is_postgresql(conn):
                    cursor.execute('''
                        INSERT INTO terms (content, updated_date)
                        VALUES (%s, %s)
                        RETURNING id
                    ''', (self.content, self.updated_date))
                    self.id = cursor.fetchone()[0]
                else:
                    cursor.execute('''
                        INSERT INTO terms (content, updated_date)
                        VALUES (?, ?)
                    ''', (self.content, self.updated_date))
                    self.id = cursor.lastrowid
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"❌ Ошибка сохранения условий: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def delete(self):
        """Удалить условия"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            if is_postgresql(conn):
                cursor.execute('DELETE FROM terms WHERE id = %s', (self.id,))
            else:
                cursor.execute('DELETE FROM terms WHERE id = ?', (self.id,))
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"❌ Ошибка удаления условий: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    @staticmethod
    def get_default_content():
        """Получить дефолтный контент условий"""
        return """
# Lietošanas noteikumi

## 1. Vispārīgie noteikumi

Classmate ir izglītības organizācijas rīks, kas paredzēts skolēnu un studentu mācību darbu pārvaldībai.

## 2. Datu izmantošana

- Visi lietotāju dati tiek glabāti droši
- Mēs nedalāmies ar jūsu datiem ar trešajām personām
- Jūs varat jebkurā laikā dzēst savus datus

## 3. Lietotāja atbildība

- Lietotājs ir atbildīgs par savu kontu drošību
- Aizliegts publicēt nepiemērotu saturu
- Aizliegts izmantot sistēmu nelikumīgiem mērķiem

## 4. Pakalpojuma izmantošana

- Pakalpojums tiek sniegts "kā ir"
- Mēs paturam tiesības mainīt vai pārtraukt pakalpojumu
- Mēs negarantējam nepārtrauktu pieejamību

## 5. Intelektuālais īpašums

- Visa sistēmas satura autortiesības pieder Classmate
- Lietotāja ievadītais saturs paliek lietotāja īpašums

## 6. Izmaiņas noteikumos

Mēs paturam tiesības jebkurā laikā mainīt šos noteikumus. Par būtiskām izmaiņām lietotāji tiks informēti.

## 7. Kontakti

Ja jums ir jautājumi par šiem noteikumiem, lūdzu, sazinieties ar mums.

---

Pēdējā atjaunošana: {date}
Versija: 1.0
        """.format(date=datetime.now().strftime('%Y-%m-%d'))
    
    def to_dict(self):
        """Преобразовать в словарь"""
        return {
            'id': self.id,
            'content': self.content,
            'updated_date': self.updated_date
        }
    
    @staticmethod
    def _from_db_row(row):
        """Создать объект из строки БД"""
        if not row:
            return None
        
        if isinstance(row, dict):
            return Terms(
                id=row['id'],
                content=row['content'],
                updated_date=row.get('updated_date')
            )
        else:
            return Terms(
                id=row[0],
                content=row[1],
                updated_date=row[2] if len(row) > 2 else None
            )
    
    def get_content_html(self):
        """Получить контент в HTML формате (конвертация Markdown)"""
        try:
            # Простая конвертация Markdown в HTML
            html = self.content
            
            # Заголовки
            html = html.replace('# ', '<h1>').replace('\n', '</h1>\n', 1)
            html = html.replace('## ', '<h2>').replace('\n', '</h2>\n')
            html = html.replace('### ', '<h3>').replace('\n', '</h3>\n')
            
            # Списки
            lines = html.split('\n')
            in_list = False
            result = []
            
            for line in lines:
                if line.strip().startswith('- '):
                    if not in_list:
                        result.append('<ul>')
                        in_list = True
                    result.append(f'<li>{line.strip()[2:]}</li>')
                else:
                    if in_list:
                        result.append('</ul>')
                        in_list = False
                    result.append(line)
            
            if in_list:
                result.append('</ul>')
            
            html = '\n'.join(result)
            
            # Параграфы
            html = html.replace('\n\n', '</p><p>')
            html = f'<p>{html}</p>'
            
            # Жирный текст
            html = html.replace('**', '<strong>', 1).replace('**', '</strong>', 1)
            
            return html
            
        except Exception as e:
            print(f"❌ Ошибка конвертации Markdown: {e}")
            return self.content
    
    def __repr__(self):
        return f"<Terms version {self.id} - {self.updated_date}>"