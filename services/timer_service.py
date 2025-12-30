"""
Timer Service - Pomodoro timer data management
"""

from models.database import get_db_connection
from config.settings import DATABASE_URL
from datetime import datetime, timedelta
import json


def save_timer_data(user_id, seconds):
    """
    Сохраняет сессию таймера
    
    Args:
        user_id (str): ID пользователя/устройства
        seconds (int): Количество секунд сессии
        
    Returns:
        bool: True если успешно
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if DATABASE_URL:  # PostgreSQL
            cursor.execute(
                """
                INSERT INTO timer_sessions 
                (user_id, duration_seconds, session_date, created_at)
                VALUES (%s, %s, %s, %s)
                """,
                (user_id, seconds, datetime.now().date(), datetime.now())
            )
        else:  # SQLite
            cursor.execute(
                """
                INSERT INTO timer_sessions 
                (user_id, duration_seconds, session_date, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (user_id, seconds, datetime.now().date().isoformat(), 
                 datetime.now().isoformat())
            )
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error saving timer data: {e}")
        return False


def get_user_timer_stats(user_id):
    """
    Получает статистику таймера пользователя
    
    Args:
        user_id (str): ID пользователя
        
    Returns:
        dict: Статистика
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        today = datetime.now().date()
        week_ago = today - timedelta(days=7)
        
        # Сегодня
        if DATABASE_URL:
            cursor.execute(
                """
                SELECT COALESCE(SUM(duration_seconds), 0) 
                FROM timer_sessions 
                WHERE user_id = %s AND session_date = %s
                """,
                (user_id, today)
            )
        else:
            cursor.execute(
                """
                SELECT COALESCE(SUM(duration_seconds), 0) 
                FROM timer_sessions 
                WHERE user_id = ? AND session_date = ?
                """,
                (user_id, today.isoformat())
            )
        
        today_seconds = cursor.fetchone()[0]
        
        # За неделю
        if DATABASE_URL:
            cursor.execute(
                """
                SELECT COALESCE(SUM(duration_seconds), 0) 
                FROM timer_sessions 
                WHERE user_id = %s AND session_date >= %s
                """,
                (user_id, week_ago)
            )
        else:
            cursor.execute(
                """
                SELECT COALESCE(SUM(duration_seconds), 0) 
                FROM timer_sessions 
                WHERE user_id = ? AND session_date >= ?
                """,
                (user_id, week_ago.isoformat())
            )
        
        week_seconds = cursor.fetchone()[0]
        
        # Количество сессий сегодня
        if DATABASE_URL:
            cursor.execute(
                """
                SELECT COUNT(*) 
                FROM timer_sessions 
                WHERE user_id = %s AND session_date = %s
                """,
                (user_id, today)
            )
        else:
            cursor.execute(
                """
                SELECT COUNT(*) 
                FROM timer_sessions 
                WHERE user_id = ? AND session_date = ?
                """,
                (user_id, today.isoformat())
            )
        
        sessions_count = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'today_minutes': today_seconds // 60,
            'today_seconds': today_seconds,
            'week_minutes': week_seconds // 60,
            'week_seconds': week_seconds,
            'sessions_today': sessions_count,
            'avg_daily_minutes': (week_seconds // 60) // 7 if week_seconds > 0 else 0
        }
        
    except Exception as e:
        print(f"Error getting timer stats: {e}")
        return {
            'today_minutes': 0,
            'today_seconds': 0,
            'week_minutes': 0,
            'week_seconds': 0,
            'sessions_today': 0,
            'avg_daily_minutes': 0
        }


def get_timer_history(user_id, days=7):
    """
    История сессий таймера
    
    Args:
        user_id (str): ID пользователя
        days (int): Количество дней назад
        
    Returns:
        list: Список сессий
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        date_limit = datetime.now().date() - timedelta(days=days)
        
        if DATABASE_URL:
            cursor.execute(
                """
                SELECT duration_seconds, session_date, created_at
                FROM timer_sessions
                WHERE user_id = %s AND session_date >= %s
                ORDER BY created_at DESC
                """,
                (user_id, date_limit)
            )
        else:
            cursor.execute(
                """
                SELECT duration_seconds, session_date, created_at
                FROM timer_sessions
                WHERE user_id = ? AND session_date >= ?
                ORDER BY created_at DESC
                """,
                (user_id, date_limit.isoformat())
            )
        
        sessions = []
        for row in cursor.fetchall():
            sessions.append({
                'duration_seconds': row[0],
                'duration_minutes': row[0] // 60,
                'date': row[1],
                'timestamp': row[2]
            })
        
        conn.close()
        return sessions
        
    except Exception as e:
        print(f"Error getting timer history: {e}")
        return []


# SQL для создания таблицы (если нужно)
def create_timer_table():
    """Создает таблицу для таймера если её нет"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if DATABASE_URL:  # PostgreSQL
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS timer_sessions (
                    id SERIAL PRIMARY KEY,
                    user_id VARCHAR(255) NOT NULL,
                    duration_seconds INTEGER NOT NULL,
                    session_date DATE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_timer_user_date 
                ON timer_sessions(user_id, session_date)
            """)
        else:  # SQLite
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS timer_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    duration_seconds INTEGER NOT NULL,
                    session_date TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_timer_user_date 
                ON timer_sessions(user_id, session_date)
            """)
        
        conn.commit()
        conn.close()
        print("✓ Timer table created")
        return True
        
    except Exception as e:
        print(f"Error creating timer table: {e}")
        return False