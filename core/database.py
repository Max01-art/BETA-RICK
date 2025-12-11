"""
Database connection and management
Работа с базой данных SQLite
"""
import sqlite3
import os
from datetime import datetime


def get_db_connection():
    """
    Получить соединение с SQLite БД
    """
    conn = sqlite3.connect('school.db')
    conn.row_factory = sqlite3.Row
    return conn


def is_postgresql(conn):
    """
    Проверить тип соединения (всегда False для SQLite)
    """
    return False


def init_db():
    """
    Инициализация всех таблиц БД
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        print("🔍 Инициализация базы данных...")
        
        # SQL для создания таблиц
        tables = get_table_schemas()
        
        for table_name, schema in tables.items():
            try:
                cursor.execute(schema)
                print(f"✅ Таблица {table_name} создана/проверена")
            except Exception as e:
                print(f"⚠️ Таблица {table_name}: {e}")
        
        conn.commit()
        print("✅ База данных инициализирована!")
        
    except Exception as e:
        print(f"❌ Ошибка инициализации БД: {e}")
        conn.rollback()
        raise e
    finally:
        conn.close()


def get_table_schemas():
    """
    Получить схемы всех таблиц для SQLite
    """
    return {
        'subjects': '''
            CREATE TABLE IF NOT EXISTS subjects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                color TEXT DEFAULT '#4361ee',
                description TEXT,
                created_date TEXT
            )
        ''',
        
        'tests': '''
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
        ''',
        
        'homework': '''
            CREATE TABLE IF NOT EXISTS homework (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT NOT NULL,
                title TEXT NOT NULL,
                date TEXT NOT NULL,
                time TEXT DEFAULT '23:59',
                description TEXT,
                type TEXT DEFAULT 'Mājasdarbs',
                due_date TEXT,
                added_date TEXT
            )
        ''',
        
        'news': '''
            CREATE TABLE IF NOT EXISTS news (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                date TEXT NOT NULL,
                image_url TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_date TEXT,
                updated_date TEXT
            )
        ''',
        
        'updates': '''
            CREATE TABLE IF NOT EXISTS updates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                date TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                created_date TEXT,
                updated_date TEXT
            )
        ''',
        
        'terms': '''
            CREATE TABLE IF NOT EXISTS terms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                updated_date TEXT
            )
        ''',
        
        'email_subscriptions': '''
            CREATE TABLE IF NOT EXISTS email_subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                notify_1_day BOOLEAN DEFAULT 1,
                notify_3_days BOOLEAN DEFAULT 1,
                is_active BOOLEAN DEFAULT 1,
                created_date TEXT
            )
        ''',
        
        'email_subject_subscriptions': '''
            CREATE TABLE IF NOT EXISTS email_subject_subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                subject_name TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                created_date TEXT,
                UNIQUE(email, subject_name)
            )
        ''',
        
        'sent_notifications': '''
            CREATE TABLE IF NOT EXISTS sent_notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_email TEXT NOT NULL,
                work_id INTEGER NOT NULL,
                work_type TEXT NOT NULL,
                notification_type TEXT NOT NULL,
                sent_date TEXT,
                UNIQUE(user_email, work_id, notification_type)
            )
        ''',
        
        'user_settings': '''
            CREATE TABLE IF NOT EXISTS user_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT UNIQUE NOT NULL,
                theme TEXT DEFAULT 'default',
                primary_color TEXT DEFAULT '#4361ee',
                secondary_color TEXT DEFAULT '#3f37c9',
                bg_gradient TEXT DEFAULT 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                custom_background TEXT,
                created_date TEXT,
                updated_date TEXT
            )
        ''',
        
        'timer_sessions': '''
            CREATE TABLE IF NOT EXISTS timer_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                seconds INTEGER NOT NULL,
                date TEXT NOT NULL,
                created_at TEXT
            )
        '''
    }


def execute_query(query, params=None, fetch_one=False, fetch_all=False):
    """
    Универсальная функция для выполнения запросов
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        if fetch_one:
            result = cursor.fetchone()
            conn.close()
            return result
        elif fetch_all:
            result = cursor.fetchall()
            conn.close()
            return result
        else:
            conn.commit()
            conn.close()
            return True
            
    except Exception as e:
        print(f"❌ Query error: {e}")
        conn.rollback()
        conn.close()
        return None