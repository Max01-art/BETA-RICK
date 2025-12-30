"""
Scheduler Service - Planned tasks (email notifications, cleanup)
"""

from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import atexit


scheduler = BackgroundScheduler()


def start_scheduler():
    """Запускает планировщик задач"""
    
    # Проверка дедлайнов каждый час
    scheduler.add_job(
        func=check_deadlines,
        trigger="interval",
        hours=1,
        id='check_deadlines',
        replace_existing=True
    )
    
    # Очистка старых данных каждый день в 3:00
    scheduler.add_job(
        func=cleanup_old_data,
        trigger="cron",
        hour=3,
        minute=0,
        id='cleanup',
        replace_existing=True
    )
    
    scheduler.start()
    print("✓ Scheduler started")
    
    # Остановка при выходе
    atexit.register(lambda: scheduler.shutdown())


def check_deadlines():
    """Проверяет приближающиеся дедлайны"""
    try:
        from models.tests import load_tests
        from models.homework import load_homework
        
        print(f"[{datetime.now()}] Checking deadlines...")
        
        tests = load_tests()
        homework = load_homework()
        all_work = tests + homework
        
        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)
        
        # Работы на сегодня и завтра
        urgent = []
        for work in all_work:
            try:
                work_date = datetime.strptime(work['date'], '%Y-%m-%d').date()
                if work_date in [today, tomorrow]:
                    urgent.append(work)
            except:
                continue
        
        if urgent:
            print(f"Found {len(urgent)} urgent work items")
            # Здесь можно отправить email/push уведомления
        
    except Exception as e:
        print(f"Error checking deadlines: {e}")


def cleanup_old_data():
    """Удаляет старые данные (>6 месяцев)"""
    try:
        from models.database import get_db_connection
        
        print(f"[{datetime.now()}] Cleaning up old data...")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        six_months_ago = datetime.now() - timedelta(days=180)
        
        # Удаление старых сессий таймера
        cursor.execute(
            "DELETE FROM timer_sessions WHERE created_at < ?",
            (six_months_ago.isoformat(),)
        )
        
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        
        print(f"Cleaned up {deleted} old records")
        
    except Exception as e:
        print(f"Error cleaning up data: {e}")


def send_deadline_notifications():
    """Отправляет уведомления о дедлайнах"""
    # TODO: интеграция с email service
    pass