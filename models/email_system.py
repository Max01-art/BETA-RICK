"""
Модель для email системы уведомлений
"""
from datetime import datetime
from models.database import get_db_connection, is_postgresql_connection


def init_email_tables():
    """Инициализирует таблицы email системы"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Email subscriptions table
        if is_postgresql_connection(conn):
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS email_subscriptions (
                    id SERIAL PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    notify_1_day BOOLEAN DEFAULT TRUE,
                    notify_3_days BOOLEAN DEFAULT TRUE,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        else:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS email_subscriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    notify_1_day BOOLEAN DEFAULT 1,
                    notify_3_days BOOLEAN DEFAULT 1,
                    is_active BOOLEAN DEFAULT 1,
                    created_date TEXT
                )
            ''')
        
        # Subject subscriptions table
        if is_postgresql_connection(conn):
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS email_subject_subscriptions (
                    id SERIAL PRIMARY KEY,
                    email TEXT NOT NULL,
                    subject_name TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(email, subject_name)
                )
            ''')
        else:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS email_subject_subscriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL,
                    subject_name TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    created_date TEXT,
                    UNIQUE(email, subject_name)
                )
            ''')
        
        # Sent notifications table
        if is_postgresql_connection(conn):
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sent_notifications (
                    id SERIAL PRIMARY KEY,
                    user_email TEXT NOT NULL,
                    work_id INTEGER NOT NULL,
                    work_type TEXT NOT NULL,
                    notification_type TEXT NOT NULL,
                    sent_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_email, work_id, notification_type)
                )
            ''')
        else:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sent_notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_email TEXT NOT NULL,
                    work_id INTEGER NOT NULL,
                    work_type TEXT NOT NULL,
                    notification_type TEXT NOT NULL,
                    sent_date TEXT,
                    UNIQUE(user_email, work_id, notification_type)
                )
            ''')
        
        conn.commit()
        print("✅ Email tables initialized")
    except Exception as e:
        print(f"❌ Error initializing email tables: {e}")
        conn.rollback()
    finally:
        conn.close()


def get_email_subscribers(subject_name, days_until):
    """Получает подписчиков для уведомлений"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        if is_postgresql_connection(conn):
            cursor.execute('''
                SELECT DISTINCT es.email 
                FROM email_subscriptions es
                JOIN email_subject_subscriptions ess ON es.email = ess.email
                WHERE ess.subject_name = %s 
                AND ess.is_active = TRUE 
                AND es.is_active = TRUE
                AND ((es.notify_1_day = TRUE AND %s = 1) OR (es.notify_3_days = TRUE AND %s = 3))
            ''', (subject_name, days_until, days_until))
        else:
            cursor.execute('''
                SELECT DISTINCT es.email 
                FROM email_subscriptions es
                JOIN email_subject_subscriptions ess ON es.email = ess.email
                WHERE ess.subject_name = ? 
                AND ess.is_active = 1 
                AND es.is_active = 1
                AND ((es.notify_1_day = 1 AND ? = 1) OR (es.notify_3_days = 1 AND ? = 3))
            ''', (subject_name, days_until, days_until))
        
        subscribers = cursor.fetchall()
        return [sub[0] if is_postgresql_connection(conn) else sub['email'] for sub in subscribers]
    except Exception as e:
        print(f"❌ Error getting subscribers: {e}")
        return []
    finally:
        conn.close()