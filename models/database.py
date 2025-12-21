"""
Модуль для работы с базой данных
"""
import os
import sqlite3
import psycopg
from datetime import datetime
from config.settings import DB_FILE, DATABASE_URL


def get_db_connection():
    """Универсальное подключение к базе данных"""
    # PostgreSQL (Render)
    if DATABASE_URL:
        try:
            conn = psycopg.connect(DATABASE_URL)
            print("✅ PostgreSQL connection successful")
            return conn
        except Exception as e:
            print(f"❌ PostgreSQL error: {e}")
            # Fallback to SQLite
            try:
                conn = sqlite3.connect(DB_FILE)
                conn.row_factory = sqlite3.Row
                print("✅ SQLite connection (fallback)")
                return conn
            except Exception as e2:
                print(f"❌ SQLite error: {e2}")
                raise e
    
    # SQLite (local development)
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        print("✅ SQLite connection (development)")
        return conn
    except Exception as e:
        print(f"❌ SQLite error: {e}")
        raise e


def is_postgresql_connection(conn):
    """Проверяет тип подключения"""
    return isinstance(conn, psycopg.Connection)


def init_database():
    """Инициализирует все таблицы"""
    from models.subjects import init_subjects_table
    from models.tests import init_tests_table
    from models.homework import init_homework_table
    from models.news import init_news_table
    from models.terms import init_terms_table
    from models.users import init_user_tables
    from models.email_system import init_email_tables
    
    print("🔧 Initializing database tables...")
    
    init_subjects_table()
    init_tests_table()
    init_homework_table()
    init_news_table()
    init_terms_table()
    init_user_tables()
    init_email_tables()
    
    print("✅ Database initialization complete!")


def reset_transaction():
    """Сбрасывает статус транзакции PostgreSQL"""
    try:
        conn = get_db_connection()
        if isinstance(conn, psycopg.Connection):
            conn.rollback()
            print("✅ Transaction reset")
        conn.close()
    except Exception as e:
        print(f"❌ Error resetting transaction: {e}")