"""
Сервис для отправки email уведомлений
"""
import os
import queue
import smtplib
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from config.settings import SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD

# Глобальная очередь для асинхронной отправки
email_queue = queue.Queue()
email_thread = None


def start_email_worker():
    """Запускает фоновый процесс для отправки email"""
    global email_thread
    
    if email_thread is None or not email_thread.is_alive():
        email_thread = threading.Thread(target=email_worker, daemon=True)
        email_thread.start()
        print("✅ Email worker started")


def email_worker():
    """Фоновый процесс для отправки email"""
    while True:
        try:
            # Ждем задачу в очереди (макс 5 минут)
            task = email_queue.get(timeout=300)
            
            if task is None:  # Сигнал остановки
                break
            
            to_email, subject, html_content = task
            print(f"📧 Sending email to: {to_email}")
            send_email_via_smtp(to_email, subject, html_content)
            email_queue.task_done()
        except queue.Empty:
            continue
        except Exception as e:
            print(f"❌ Email worker error: {e}")


def send_email_async(to_email, subject, html_content):
    """Асинхронно отправляет email (не блокирует сервер)"""
    try:
        email_queue.put((to_email, subject, html_content))
        print(f"✅ Email queued: {to_email}")
        return True
    except Exception as e:
        print(f"❌ Cannot queue email: {e}")
        return False


def send_email_via_smtp(to_email, subject, html_content):
    """Отправляет email через SMTP с таймаутом"""
    try:
        if not SMTP_USERNAME or not SMTP_PASSWORD:
            print("❌ SMTP credentials not configured!")
            return False
        
        print(f"🔧 Connecting to SMTP server...")
        
        msg = MIMEMultipart()
        msg['From'] = SMTP_USERNAME
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(html_content, 'html'))
        
        # Создаем соединение с таймаутом
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=30)
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        print(f"✅ Email sent successfully: {to_email}")
        return True
    except Exception as e:
        print(f"❌ Email sending error: {e}")
        return False


def send_notification_email(email, work, days_until):
    """Отправляет уведомление о работе"""
    try:
        subject = f"🔔 Напоминание: {work['subject']} - {work.get('type', 'Работа')}"
        
        message = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2>📚 Classmate Напоминание</h2>
            <p><strong>{'🚨 ЗАВТРА' if days_until == 1 else '⏰ Через 3 дня'}</strong></p>
            <hr>
            <p><strong>Предмет:</strong> {work['subject']}</p>
            <p><strong>Тип:</strong> {work.get('type', 'Работа')}</p>
            <p><strong>Дата:</strong> {work['date']}</p>
            {f"<p><strong>Описание:</strong> {work.get('description', '')}</p>" if work.get('description') else ''}
            <hr>
            <p style="color: gray; font-size: 12px;">Это автоматическое уведомление от Classmate</p>
        </body>
        </html>
        """
        
        return send_email_async(email, subject, message)
    except Exception as e:
        print(f"❌ Error preparing notification: {e}")
        return False