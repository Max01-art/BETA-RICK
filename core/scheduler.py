"""
Task scheduler for notifications
"""
import threading
import time
from datetime import datetime
from core.database import get_db_connection, is_postgresql
from core.email_service import EmailService


def check_upcoming_work():
    """
    Проверить предстоящие работы и отправить уведомления
    """
    try:
        print("🔍 Проверка предстоящих работ...")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        is_postgres = is_postgresql(conn)
        
        # Получаем работы через 1 и 3 дня
        if is_postgres:
            cursor.execute("""
                SELECT '1_day' as notify_type, 'test' as source, id, subject, type, date, description 
                FROM tests WHERE date::DATE = CURRENT_DATE + INTERVAL '1 day'
                UNION ALL
                SELECT '1_day' as notify_type, 'homework' as source, id, subject, 'Mājasdarbs' as type, date, description 
                FROM homework WHERE date::DATE = CURRENT_DATE + INTERVAL '1 day'
                UNION ALL  
                SELECT '3_days' as notify_type, 'test' as source, id, subject, type, date, description 
                FROM tests WHERE date::DATE = CURRENT_DATE + INTERVAL '3 days'
                UNION ALL
                SELECT '3_days' as notify_type, 'homework' as source, id, subject, 'Mājasdarbs' as type, date, description 
                FROM homework WHERE date::DATE = CURRENT_DATE + INTERVAL '3 days'
            """)
        else:
            cursor.execute("""
                SELECT '1_day' as notify_type, 'test' as source, id, subject, type, date, description 
                FROM tests WHERE date = DATE('now', '+1 day')
                UNION ALL
                SELECT '1_day' as notify_type, 'homework' as source, id, subject, 'Mājasdarbs' as type, date, description 
                FROM homework WHERE date = DATE('now', '+1 day')
                UNION ALL
                SELECT '3_days' as notify_type, 'test' as source, id, subject, type, date, description 
                FROM tests WHERE date = DATE('now', '+3 days')
                UNION ALL
                SELECT '3_days' as notify_type, 'homework' as source, id, subject, 'Mājasdarbs' as type, date, description 
                FROM homework WHERE date = DATE('now', '+3 days')
            """)
        
        upcoming_work = cursor.fetchall()
        conn.close()
        
        print(f"🔍 Найдено работ: {len(upcoming_work)}")
        
        # Группируем по типу уведомления
        work_by_days = {'1_day': [], '3_days': []}
        for work in upcoming_work:
            work_dict = {
                'id': work[2],
                'subject': work[3],
                'type': work[4],
                'date': work[5],
                'description': work[6]
            }
            work_by_days[work[0]].append(work_dict)
        
        # Отправляем уведомления
        email_service = EmailService()
        emails_sent = 0
        
        for work in work_by_days['1_day']:
            if send_notifications_for_work(work, days_until=1, email_service=email_service):
                emails_sent += 1
        
        for work in work_by_days['3_days']:
            if send_notifications_for_work(work, days_until=3, email_service=email_service):
                emails_sent += 1
        
        print(f"✅ Отправлено уведомлений: {emails_sent}")
        
    except Exception as e:
        print(f"❌ Ошибка проверки работ: {e}")
        import traceback
        print(traceback.format_exc())


def send_notifications_for_work(work, days_until, email_service):
    """
    Отправить уведомления подписчикам о работе
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        is_postgres = is_postgresql(conn)
        
        # Находим подписчиков на этот предмет
        if is_postgres:
            cursor.execute('''
                SELECT DISTINCT es.email 
                FROM email_subscriptions es
                JOIN email_subject_subscriptions ess ON es.email = ess.email
                WHERE ess.subject_name = %s 
                AND ess.is_active = TRUE 
                AND es.is_active = TRUE
                AND ((es.notify_1_day = TRUE AND %s = 1) OR (es.notify_3_days = TRUE AND %s = 3))
            ''', (work['subject'], days_until, days_until))
        else:
            cursor.execute('''
                SELECT DISTINCT es.email 
                FROM email_subscriptions es
                JOIN email_subject_subscriptions ess ON es.email = ess.email
                WHERE ess.subject_name = ? 
                AND ess.is_active = 1 
                AND es.is_active = 1
                AND ((es.notify_1_day = 1 AND ? = 1) OR (es.notify_3_days = 1 AND ? = 3))
            ''', (work['subject'], days_until, days_until))
        
        subscribers = cursor.fetchall()
        conn.close()
        
        print(f"📧 Подписчиков на {work['subject']}: {len(subscribers)}")
        
        # Отправляем уведомления
        success_count = 0
        for subscriber in subscribers:
            email = subscriber[0] if isinstance(subscriber, tuple) else subscriber['email']
            
            if email_service.send_notification_email(email, work, days_until):
                success_count += 1
        
        return success_count > 0
        
    except Exception as e:
        print(f"❌ Ошибка отправки уведомлений: {e}")
        return False


def scheduler_worker(app):
    """
    Фоновый процесс планировщика
    """
    last_check_date = None
    
    while True:
        try:
            with app.app_context():
                now = datetime.now()
                current_time = now.strftime("%H:%M")
                today_date = now.strftime("%Y-%m-%d")
                
                # Проверяем в 08:00 каждый день
                if current_time >= "08:00" and current_time <= "08:05":
                    if last_check_date != today_date:
                        print(f"🕐 Запуск ежедневной проверки: {current_time}")
                        check_upcoming_work()
                        last_check_date = today_date
                        print("✅ Проверка завершена")
                else:
                    if last_check_date == today_date and current_time > "08:05":
                        last_check_date = None
                
                time.sleep(60)  # Проверяем каждую минуту
                
        except Exception as e:
            print(f"❌ Ошибка в планировщике: {e}")
            time.sleep(300)


def init_scheduler(app):
    """
    Инициализировать планировщик
    """
    scheduler_thread = threading.Thread(
        target=scheduler_worker,
        args=(app,),
        daemon=True
    )
    scheduler_thread.start()
    print("✅ Планировщик запущен")


def manual_check():
    """
    Ручная проверка (для отладки)
    """
    check_upcoming_work()