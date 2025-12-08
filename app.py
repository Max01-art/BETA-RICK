from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file, make_response, g
import sqlite3
import os
import uuid
import re
import psycopg
import time
import threading
import socket
import queue
import json
from functools import lru_cache
from urllib.parse import urlparse   
from datetime import datetime, timedelta
from collections import defaultdict
import requests
from werkzeug.utils import secure_filename
from flask_socketio import SocketIO, emit
import smtplib
from email.mime.text import MIMEText  # ✅ Pareizi
from email.mime.multipart import MIMEMultipart  # ✅ Pareizi
from threading import Thread
import functools

app = Flask(__name__)
app.secret_key = 'classmate-secret-key-2024'
socketio = SocketIO(app, cors_allowed_origins="*")
# Globālie mainīgie optimizācijai
db_pool = None
data_cache = {}
CACHE_DURATION = 30  # 30 sekundes kešs
# Online lietotāju skaitītājs
online_users = set()

# E-pasta rinda asinhronai sūtīšanai
email_queue = queue.Queue()

# SQLite datu bāze
DB_FILE = 'school.db'
HOST_PASSWORD = "kolya333arbuz"  # Parole kursabiedriem

# UPLOAD MAPES IESTATĪJUMI
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024


class SimpleCache:
    def __init__(self):
        self._cache = {}
        self._timestamps = {}
    
    def get(self, key):
        if key in self._cache and datetime.now() - self._timestamps[key] < timedelta(seconds=30):
            return self._cache[key]
        return None
    
    def set(self, key, value):
        self._cache[key] = value
        self._timestamps[key] = datetime.now()
    
    def clear(self, key=None):
        if key:
            self._cache.pop(key, None)
            self._timestamps.pop(key, None)
        else:
            self._cache.clear()
            self._timestamps.clear()

cache = SimpleCache()

# ================= CONTEXT PROCESSORS =================

@app.context_processor
def inject_common_variables():
    """Injects common variables into ALL templates - FIXED VERSION"""
    def safe_format_date(date_value):
        """Safely formats date - handles strings and datetime objects"""
        if not date_value:
            return ''
        
        if isinstance(date_value, str):
            return date_value
        
        if hasattr(date_value, 'strftime'):
            try:
                return date_value.strftime('%d.%m.%Y')
            except:
                return str(date_value)
        
        return str(date_value)
    
    def safe_format_time(time_value):
        """Safely formats time"""
        if not time_value:
            return ''
        
        if isinstance(time_value, str):
            return time_value
        
        if hasattr(time_value, 'strftime'):
            try:
                return time_value.strftime('%H:%M')
            except:
                return str(time_value)
        
        return str(time_value)
    
    def get_status_color(days_left):
        """Returns Bootstrap color class based on days left"""
        if days_left is None:
            return 'secondary'
        if days_left == 0:
            return 'danger'
        if days_left == 1:
            return 'warning'
        if days_left <= 7:
            return 'info'
        return 'success'
    
    def is_mobile():
        """Checks if user is on mobile device"""
        user_agent = request.headers.get('User-Agent', '') if request else ''
        return 'Mobi' in user_agent
    
    # ✅ ВАЖНО: ВСЕГДА возвращаем словарь
    return {
        'current_year': datetime.now().year,
        'current_time': datetime.now(),
        'app_name': 'Classmate',
        'app_version': '2.0',
        'format_date': safe_format_date,
        'format_time': safe_format_time,
        'get_status_color': get_status_color,
        'is_mobile': is_mobile,
        'now': datetime.now,
    }


def check_upcoming_work_simple():
    """Оптимизированная проверка работ с исправлением типов PostgreSQL"""
    try:
        print("🔍 Проверка предстоящих работ...")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Определяем тип базы данных
        is_postgresql = 'DATABASE_URL' in os.environ
        
        if is_postgresql:
            # ✅ PostgreSQL - приводим типы
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
            # ✅ SQLite
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
        
        all_upcoming_work = cursor.fetchall()
        conn.close()
        
        print(f"🔍 Найдено работ: {len(all_upcoming_work)}")
        
        # Группируем и отправляем
        work_by_days = {'1_day': [], '3_days': []}
        for work in all_upcoming_work:
            work_dict = {
                'id': work[2], 
                'subject': work[3], 
                'type': work[4], 
                'date': work[5], 
                'description': work[6]
            }
            work_by_days[work[0]].append(work_dict)
            print(f"🔍 Найден: {work[3]} - {work[5]} ({work[0]})")
        
        # Отправляем уведомления
        emails_sent = 0
        for work in work_by_days['1_day']:
            if send_notifications_for_work_simple(work, days_until=1):
                emails_sent += 1
        
        for work in work_by_days['3_days']:
            if send_notifications_for_work_simple(work, days_until=3):
                emails_sent += 1
        
        print(f"✅ Отправлено писем: {emails_sent}")
        
    except Exception as e:
        print(f"❌ Ошибка при проверке работ: {e}")
        import traceback
        print(f"❌ Детали ошибки: {traceback.format_exc()}")

def send_notifications_for_work_simple(work, days_until):
    """Отправляет уведомления подписчикам о работе"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        print(f"🔍 Ищу подписчиков для: {work['subject']} ({days_until} дней)")
        
        # Находим подписчиков
        if 'DATABASE_URL' in os.environ:
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
                AND ess.is_active = TRUE 
                AND es.is_active = TRUE
                AND ((es.notify_1_day = TRUE AND ? = 1) OR (es.notify_3_days = TRUE AND ? = 3))
            ''', (work['subject'], days_until, days_until))
        
        subscribers = cursor.fetchall()
        conn.close()
        
        print(f"🔍 Найдено подписчиков: {len(subscribers)}")
        
        # Отправляем письма
        success_count = 0
        for subscriber in subscribers:
            email = subscriber[0]
            print(f"📧 Отправляю письмо: {email}")
            if send_email_notification(email, work, days_until):
                success_count += 1
        
        print(f"✅ Успешно отправлено: {success_count}/{len(subscribers)}")
        return success_count > 0
        
    except Exception as e:
        print(f"❌ Ошибка отправки уведомлений: {e}")
        return False
    
def simple_scheduler():
    """Улучшенный планировщик с проверкой каждые 5 минут"""
    last_check_date = None
    
    while True:
        try:
            now = datetime.now()
            current_time = now.strftime("%H:%M")
            today_date = now.strftime("%Y-%m-%d")
            
            # Проверяем каждый день в 08:00 (с запасом в 5 минут)
            if current_time >= "08:00" and current_time <= "08:05":
                if last_check_date != today_date:  # Проверяем только раз в день
                    print(f"🕐 Запуск ежедневной проверки: {current_time}")
                    check_upcoming_work_simple()
                    last_check_date = today_date
                    print("✅ Ежедневная проверка завершена")
            else:
                # Сбрасываем флаг проверки
                if last_check_date == today_date and current_time > "08:05":
                    last_check_date = None
            
            time.sleep(60)  # Проверяем каждую минуту
            
        except Exception as e:
            print(f"❌ Ошибка в планировщике: {e}")
            time.sleep(300)  # При ошибке ждем 5 минут




def email_worker():
    """Fona process e-pastu sūtīšanai"""
    while True:
        try:
            # Gaida e-pastu rindā (max 5 minūtes)
            task = email_queue.get(timeout=300)
            if task is None:  # Stop signal
                break
                
            to_email, subject, html_content = task
            print(f"📧 Fona process sūta e-pastu uz: {to_email}")
            send_email_via_smtp(to_email, subject, html_content)
            email_queue.task_done()
            
        except queue.Empty:
            continue
        except Exception as e:
            print(f"❌ Fona e-pasta kļūda: {e}")

# Startē fona darbinieku
email_thread = threading.Thread(target=email_worker, daemon=True)
email_thread.start()

def send_email_async(to_email, subject, html_content):
    """Asinhroni sūta e-pastu (neblokē serveri)"""
    try:
        email_queue.put((to_email, subject, html_content))
        print(f"✅ E-pasts ievietots rindā: {to_email}")
        return True
    except Exception as e:
        print(f"❌ Nevar ievietot e-pastu rindā: {e}")
        return False
    
# Оптимизированные функции с кешированием
@lru_cache(maxsize=64)
def load_subjects_cached():
    """Кешированные предметы на 30 секунд"""
    return load_subjects()

def load_tests_optimized():
    """Оптимизированная загрузка тестов"""
    cache_key = "tests_all"
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    tests = load_tests()
    cache.set(cache_key, tests)
    return tests

def load_homework_optimized():
    """Оптимизированная загрузка домашних заданий"""
    cache_key = "homework_all"
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    homework = load_homework()
    cache.set(cache_key, homework)
    return homework

def load_terms_cached():
    """Кешированные условия использования"""
    cache_key = "terms_content"
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    terms = load_terms()
    cache.set(cache_key, terms)
    return terms

def calculate_days_left(date_str, time_str='23:59', due_date_str=None):
    """Aprēķina atlikušās dienas līdz termiņam - izmanto due_date ja tas ir norādīts"""
    return calculate_days_left_with_due_date(date_str, time_str, due_date_str)

# Izveido upload mapi ja tā nav
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def reset_transaction():
    """Resetē PostgreSQL transakcijas statusu"""
    try:
        conn = get_db_connection()
        if isinstance(conn, psycopg.Connection):
            conn.rollback()
            print("✅ Transakcija resetēta")
        conn.close()
    except Exception as e:
        print(f"❌ Kļūda resetējot transakciju: {e}")

def update_tables_with_due_date():
    """Atjauno tabulas ar due_date lauku"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Pārbauda vai due_date lauks jau eksistē
        if isinstance(conn, psycopg.Connection):
            # PostgreSQL - pārbauda tests tabulu
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='tests' AND column_name='due_date'
            """)
            tests_has_due_date = cursor.fetchone()
            
            # Pārbauda homework tabulu
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='homework' AND column_name='due_date'
            """)
            homework_has_due_date = cursor.fetchone()
            
            if not tests_has_due_date:
                cursor.execute('ALTER TABLE tests ADD COLUMN due_date TEXT')
                print("✅ Pievienots due_date tests tabulai")
            
            if not homework_has_due_date:
                cursor.execute('ALTER TABLE homework ADD COLUMN due_date TEXT')
                print("✅ Pievienots due_date homework tabulai")
                
        else:
            # SQLite - pārbauda tests tabulu
            cursor.execute("PRAGMA table_info(tests)")
            tests_columns = [column[1] for column in cursor.fetchall()]
            if 'due_date' not in tests_columns:
                cursor.execute('ALTER TABLE tests ADD COLUMN due_date TEXT')
                print("✅ Pievienots due_date tests tabulai")
            
            # Pārbauda homework tabulu
            cursor.execute("PRAGMA table_info(homework)")
            homework_columns = [column[1] for column in cursor.fetchall()]
            if 'due_date' not in homework_columns:
                cursor.execute('ALTER TABLE homework ADD COLUMN due_date TEXT')
                print("✅ Pievienots due_date homework tabulai")
        
        conn.commit()
        print("✅ Tabulas atjauninātas ar due_date lauku")
        
    except Exception as e:
        print(f"❌ Kļūda atjauninot tabulas: {e}")
        conn.rollback()
    finally:
        conn.close()

def init_tables_if_not_exists():
    """Izveido tabulas tikai ja tās neeksistē - NEIZDZĒŠ DATUS!"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        print("🔍 Pārbaudu vai tabulas eksistē...")
        
        if isinstance(conn, psycopg.Connection):
            # ======================= POSTGRESQL =======================
            
            # ✅ GALVENĀS TABULAS
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS subjects (
                    id SERIAL PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    color TEXT DEFAULT '#4361ee',
                    created_date TEXT,
                    description TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tests (
                    id SERIAL PRIMARY KEY,
                    subject TEXT NOT NULL,
                    type TEXT NOT NULL,
                    date TEXT NOT NULL,
                    time TEXT DEFAULT '23:59',
                    description TEXT,
                    due_date TEXT,
                    added_date TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS homework (
                    id SERIAL PRIMARY KEY,
                    subject TEXT NOT NULL,
                    title TEXT NOT NULL,
                    date TEXT NOT NULL,
                    time TEXT DEFAULT '23:59',
                    description TEXT,
                    type TEXT DEFAULT 'Mājasdarbs',
                    due_date TEXT,
                    added_date TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS news (
                    id SERIAL PRIMARY KEY,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    date TEXT NOT NULL,
                    image_url TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_date TEXT,
                    updated_date TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS terms (
                    id SERIAL PRIMARY KEY,
                    content TEXT NOT NULL,
                    updated_date TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS updates (
                    id SERIAL PRIMARY KEY,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    date TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_date TEXT,
                    updated_date TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS timer_sessions (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    seconds INTEGER NOT NULL,
                    date TEXT NOT NULL,
                    created_at TEXT
                )
            ''')
            
            # ✅ SUBJECT MANAGEMENT TABULAS
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS subject_categories (
                    id SERIAL PRIMARY KEY,
                    subject_id INTEGER NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
                    name TEXT NOT NULL,
                    description TEXT,
                    color TEXT DEFAULT '#3498db',
                    created_date TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS subject_files (
                    id SERIAL PRIMARY KEY,
                    subject_id INTEGER NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
                    category_id INTEGER REFERENCES subject_categories(id) ON DELETE SET NULL,
                    filename TEXT NOT NULL,
                    original_filename TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    file_size INTEGER,
                    file_type TEXT,
                    description TEXT,
                    uploaded_by TEXT DEFAULT 'Sistēma',
                    upload_date TEXT
                )
            ''')
            
            # ✅ E-PASTA SISTĒMAS TABULAS
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
            
            # ✅ USER SETTINGS & THEMES TABULAS
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_settings (
                    id SERIAL PRIMARY KEY,
                    device_id TEXT UNIQUE NOT NULL,
                    theme TEXT DEFAULT 'default',
                    primary_color TEXT DEFAULT '#4361ee',
                    secondary_color TEXT DEFAULT '#3f37c9',
                    bg_gradient TEXT DEFAULT 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    custom_background TEXT,
                    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS app_config (
                    id SERIAL PRIMARY KEY,
                    config_key TEXT UNIQUE NOT NULL,
                    config_value TEXT,
                    description TEXT,
                    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # ✅ SESSION & ACTIVITY LOGGING
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_sessions (
                    id SERIAL PRIMARY KEY,
                    device_id TEXT NOT NULL,
                    ip_address TEXT,
                    user_agent TEXT,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # ✅ Pievieno sākotnējos datus
            # Terms
            cursor.execute('SELECT COUNT(*) FROM terms')
            terms_count = cursor.fetchone()[0]
            
            if terms_count == 0:
                cursor.execute('''
                    INSERT INTO terms (content, updated_date) 
                    VALUES (%s, %s)
                ''', ('Šeit būs lietošanas noteikumi...', datetime.now().strftime('%Y-%m-%d %H:%M')))
                print("✅ Pievienoti sākotnējie noteikumi")
            
            # App config
            cursor.execute('SELECT COUNT(*) FROM app_config WHERE config_key = %s', ('default_theme',))
            default_theme_count = cursor.fetchone()[0]
            
            if default_theme_count == 0:
                cursor.execute('''
                    INSERT INTO app_config (config_key, config_value, description) 
                    VALUES (%s, %s, %s)
                ''', ('default_theme', 'default', 'Noklusējuma tēma visiem lietotājiem'))
                print("✅ Pievienots noklusējuma tēmas config")
            
        else:
            # ======================= SQLITE =======================
            
            cursor.execute('''CREATE TABLE IF NOT EXISTS subjects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                color TEXT DEFAULT '#4361ee',
                created_date TEXT,
                description TEXT
            )''')
            
            cursor.execute('''CREATE TABLE IF NOT EXISTS tests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT NOT NULL,
                type TEXT NOT NULL,
                date TEXT NOT NULL,
                time TEXT DEFAULT '23:59',
                description TEXT,
                due_date TEXT,
                added_date TEXT
            )''')
            
            cursor.execute('''CREATE TABLE IF NOT EXISTS homework (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT NOT NULL,
                title TEXT NOT NULL,
                date TEXT NOT NULL,
                time TEXT DEFAULT '23:59',
                description TEXT,
                type TEXT DEFAULT 'Mājasdarbs',
                due_date TEXT,
                added_date TEXT
            )''')
            
            cursor.execute('''CREATE TABLE IF NOT EXISTS news (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                date TEXT NOT NULL,
                image_url TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_date TEXT,
                updated_date TEXT
            )''')
            
            cursor.execute('''CREATE TABLE IF NOT EXISTS terms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                updated_date TEXT
            )''')
            
            cursor.execute('''CREATE TABLE IF NOT EXISTS updates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                date TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                created_date TEXT,
                updated_date TEXT
            )''')
            
            cursor.execute('''CREATE TABLE IF NOT EXISTS timer_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                seconds INTEGER,
                date TEXT,
                created_at TEXT
            )''')
            
            # ✅ SUBJECT MANAGEMENT TABULAS
            cursor.execute('''CREATE TABLE IF NOT EXISTS subject_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                color TEXT DEFAULT '#3498db',
                created_date TEXT,
                FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE
            )''')
            
            cursor.execute('''CREATE TABLE IF NOT EXISTS subject_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject_id INTEGER NOT NULL,
                category_id INTEGER,
                filename TEXT NOT NULL,
                original_filename TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_size INTEGER,
                file_type TEXT,
                description TEXT,
                uploaded_by TEXT DEFAULT 'Sistēma',
                upload_date TEXT,
                FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
                FOREIGN KEY (category_id) REFERENCES subject_categories(id) ON DELETE SET NULL
            )''')
            
            # ✅ E-PASTA SISTĒMAS TABULAS
            cursor.execute('''CREATE TABLE IF NOT EXISTS email_subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                notify_1_day BOOLEAN DEFAULT 1,
                notify_3_days BOOLEAN DEFAULT 1,
                is_active BOOLEAN DEFAULT 1,
                created_date TEXT
            )''')
            
            cursor.execute('''CREATE TABLE IF NOT EXISTS email_subject_subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                subject_name TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                created_date TEXT,
                UNIQUE(email, subject_name)
            )''')
            
            cursor.execute('''CREATE TABLE IF NOT EXISTS sent_notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_email TEXT NOT NULL,
                work_id INTEGER NOT NULL,
                work_type TEXT NOT NULL,
                notification_type TEXT NOT NULL,
                sent_date TEXT,
                UNIQUE(user_email, work_id, notification_type)
            )''')
            
            # ✅ USER SETTINGS & THEMES TABULAS
            cursor.execute('''CREATE TABLE IF NOT EXISTS user_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT UNIQUE NOT NULL,
                theme TEXT DEFAULT 'default',
                primary_color TEXT DEFAULT '#4361ee',
                secondary_color TEXT DEFAULT '#3f37c9',
                bg_gradient TEXT DEFAULT 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                custom_background TEXT,
                created_date TEXT,
                updated_date TEXT
            )''')
            
            cursor.execute('''CREATE TABLE IF NOT EXISTS app_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                config_key TEXT UNIQUE NOT NULL,
                config_value TEXT,
                description TEXT,
                updated_date TEXT
            )''')
            
            # ✅ SESSION & ACTIVITY LOGGING
            cursor.execute('''CREATE TABLE IF NOT EXISTS user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT NOT NULL,
                ip_address TEXT,
                user_agent TEXT,
                last_activity TEXT,
                created_date TEXT
            )''')
            
            # ✅ Pievieno sākotnējos datus
            # Terms
            cursor.execute('SELECT COUNT(*) FROM terms')
            terms_count = cursor.fetchone()[0]
            
            if terms_count == 0:
                cursor.execute('''
                    INSERT INTO terms (content, updated_date) 
                    VALUES (?, ?)
                ''', ('Šeit būs lietošanas noteikumi...', datetime.now().strftime('%Y-%m-%d %H:%M')))
                print("✅ Pievienoti sākotnējie noteikumi")
            
            # App config
            cursor.execute('SELECT COUNT(*) FROM app_config WHERE config_key = ?', ('default_theme',))
            default_theme_count = cursor.fetchone()[0]
            
            if default_theme_count == 0:
                cursor.execute('''
                    INSERT INTO app_config (config_key, config_value, description) 
                    VALUES (?, ?, ?)
                ''', ('default_theme', 'default', 'Noklusējuma tēma visiem lietotājiem'))
                print("✅ Pievienots noklusējuma tēmas config")
        
        conn.commit()
        print("✅ Tabulas veiksmīgi pārbaudītas/izveidotas - dati SAGLABĀTI!")
        
        # ✅ PAPILDUS: Pārbauda un atjaunina esošās tabulas
        update_existing_tables(conn)
        
    except Exception as e:
        print(f"❌ Kļūda inicializējot tabulas: {e}")
        import traceback
        print(f"❌ Pilna kļūda: {traceback.format_exc()}")
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()


def update_existing_tables(conn):
    """Atjaunina esošās tabulas ar jauniem laukiem, ja nepieciešams"""
    try:
        cursor = conn.cursor()
        
        print("🔍 Pārbaudu tabulu struktūru...")
        
        if isinstance(conn, psycopg.Connection):
            # PostgreSQL - исправленные DEFAULT значения
            tables_to_check = [
                ('subjects', [
                    ('color', "TEXT DEFAULT '#4361ee'"),
                    ('description', 'TEXT')
                ]),
                ('tests', [
                    ('due_date', 'TEXT'),
                    ('time', "TEXT DEFAULT '23:59'")
                ]),
                ('homework', [
                    ('due_date', 'TEXT'),
                    ('time', "TEXT DEFAULT '23:59'"),
                    ('type', "TEXT DEFAULT 'Mājasdarbs'")
                ]),
                ('user_settings', [
                    ('primary_color', "TEXT DEFAULT '#4361ee'"),
                    ('secondary_color', "TEXT DEFAULT '#3f37c9'"),
                    ('bg_gradient', "TEXT DEFAULT 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'")
                ])
            ]
            
            for table_name, columns in tables_to_check:
                for column_name, column_type in columns:
                    cursor.execute(f"""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_name = %s AND column_name = %s
                    """, (table_name, column_name))
                    
                    if not cursor.fetchone():
                        print(f"⚠️ Pievienoju lauku {column_name} tabulai {table_name}")
                        try:
                            cursor.execute(f'ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}')
                            print(f"✅ Lauks {column_name} pievienots")
                        except Exception as e:
                            print(f"❌ Kļūda pievienojot lauku {column_name}: {e}")
                            # Mēģinām bez DEFAULT vērtības
                            try:
                                column_type_simple = column_type.split('DEFAULT')[0].strip()
                                cursor.execute(f'ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type_simple}')
                                print(f"✅ Lauks {column_name} pievienots (bez DEFAULT)")
                            except Exception as e2:
                                print(f"❌ Nevarēju pievienot lauku {column_name}: {e2}")
                        
        else:
            # SQLite - исправленные DEFAULT значения
            tables_to_check = [
                ('subjects', [
                    ('color', "TEXT DEFAULT '#4361ee'"),
                    ('description', 'TEXT')
                ]),
                ('tests', [
                    ('due_date', 'TEXT'),
                    ('time', "TEXT DEFAULT '23:59'")
                ]),
                ('homework', [
                    ('due_date', 'TEXT'),
                    ('time', "TEXT DEFAULT '23:59'"),
                    ('type', "TEXT DEFAULT 'Mājasdarbs'")
                ])
            ]
            
            for table_name, columns in tables_to_check:
                cursor.execute(f"PRAGMA table_info({table_name})")
                existing_columns = [column[1] for column in cursor.fetchall()]
                
                for column_name, column_type in columns:
                    if column_name not in existing_columns:
                        print(f"⚠️ Pievienoju lauku {column_name} tabulai {table_name}")
                        try:
                            cursor.execute(f'ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}')
                        except Exception as e:
                            print(f"❌ Kļūda pievienojot lauku {column_name}: {e}")
                            # Mēģinām bez DEFAULT
                            try:
                                column_type_simple = column_type.split('DEFAULT')[0].strip()
                                cursor.execute(f'ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type_simple}')
                            except Exception as e2:
                                print(f"❌ Nevarēju pievienot lauku {column_name}: {e2}")
        
        conn.commit()
        print("✅ Tabulu struktūra atjaunināta!")
        
    except Exception as e:
        print(f"⚠️ Kļūda atjauninot tabulas: {e}")
        import traceback
        print(f"⚠️ Pilna kļūda: {traceback.format_exc()}")
        conn.rollback()

def get_db_connection():
    """Vienkāršs datu bāzes savienojums"""
    # PostgreSQL Render
    if 'DATABASE_URL' in os.environ:
        try:
            conn = psycopg.connect(os.environ['DATABASE_URL'])
            print("✅ PostgreSQL savienojums veiksmīgs")
            return conn
        except Exception as e:
            print(f"❌ PostgreSQL kļūda: {e}")
            # Fallback uz SQLite development
            try:
                conn = sqlite3.connect('school.db')
                conn.row_factory = sqlite3.Row
                print("✅ SQLite savienojums (fallback)")
                return conn
            except Exception as e2:
                print(f"❌ SQLite kļūda: {e2}")
                raise e
    
    # SQLite lokālai izstrādei
    try:
        conn = sqlite3.connect('school.db')
        conn.row_factory = sqlite3.Row
        print("✅ SQLite savienojums (development)")
        return conn
    except Exception as e:
        print(f"❌ SQLite kļūda: {e}")
        raise e
    


def is_postgresql_connection(conn):
    """Pārbauda vai savienojums ir PostgreSQL"""
    return hasattr(conn, '__class__') and 'psycopg' in str(conn.__class__)

def send_email_notification(email, work, days_until):
    """Отправляет email уведомление АСИНХРОННО"""
    try:
        print(f"🚨 Ставлю email в очередь: {email}")
        
        subject = f"🔔 Напоминание: {work['subject']} - {work.get('type', 'Работа')}"
        
        message = f"""
        <!DOCTYPE html>
        <html>
        <body>
            <h2>📚 Classmate Напоминание</h2>
            <p><strong>{'🚨 ЗАВТРА' if days_until == 1 else '⏰ Через 3 дня'}</strong></p>
            <p><strong>Предмет:</strong> {work['subject']}</p>
            <p><strong>Тип:</strong> {work.get('type', 'Работа')}</p>
            <p><strong>Дата:</strong> {work['date']}</p>
        </body>
        </html>
        """
        
        # ✅ Используем АСИНХРОННУЮ отправку через очередь
        success = send_email_async(email, subject, message)
        
        if success:
            print(f"✅ Email добавлен в очередь: {email}")
        else:
            print(f"❌ Ошибка добавления в очередь: {email}")
        
        return success
        
    except Exception as e:
        print(f"❌ Ошибка подготовки email: {e}")
        return False

def send_email_via_smtp(to_email, subject, html_content):
    """Улучшенная отправка email с таймаутом"""
    try:
        smtp_username = os.environ.get('SMTP_USERNAME')
        smtp_password = os.environ.get('SMTP_PASSWORD')
        
        if not smtp_username or not smtp_password:
            print("❌ SMTP настройки не найдены!")
            return False
        
        print(f"🔧 Подключаюсь к SMTP серверу...")
        
        # Настройки с таймаутом
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        
        msg = MIMEMultipart()
        msg['From'] = smtp_username
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(html_content, 'html'))
        
        # Создаем соединение с таймаутом
        server = smtplib.SMTP(smtp_server, smtp_port, timeout=30)  # 30 секунд таймаут
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.send_message(msg)
        server.quit()
        
        print(f"✅ Email УСПЕШНО отправлен: {to_email}")
        return True
        
    except socket.timeout:
        print("❌ Таймаут подключения к SMTP серверу")
        return False
    except smtplib.SMTPAuthenticationError:
        print("❌ Ошибка аутентификации Gmail")
        return False
    except Exception as e:
        print(f"❌ Ошибка отправки email: {e}")
        return False

def create_email_based_system():
    """Izveido vienkāršotu epasta balstītu sistēmu"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
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
    
    # ✅ PIEVIENO ŠO TABULU
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
    
    conn.commit()
    conn.close()
    
# ✅ NOVĀC ŠO FUNKCIJU NO create_email_based_system iekšienes
def is_email_unique(email):
    """Больше не проверяем уникальность - разрешаем перезапись"""
    return True  # ✅ Всегда разрешаем

def get_user_subscriptions(email):
    """Atgriež lietotāja abonementus"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Galvenie iestatījumi
    cursor.execute('SELECT * FROM email_subscriptions WHERE email = %s', (email,))
    preferences = cursor.fetchone()
    
    # Abonētie priekšmeti
    cursor.execute('''
        SELECT subject_name FROM email_subject_subscriptions 
        WHERE email = %s AND is_active = TRUE
    ''', (email,))
    subjects = [row[0] for row in cursor.fetchall()]
    
    conn.close()
    return preferences, subjects



# Priekšmetu funkcijas
def load_subjects():
    conn = get_db_connection()
    try:
        if isinstance(conn, psycopg.Connection):
            # PostgreSQL
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM subjects ORDER BY name')
            subjects_data = cursor.fetchall()
            
            # Konvertējam tuple uz dict
            subjects = []
            for row in subjects_data:
                subjects.append({
                    'id': row[0],
                    'name': row[1],
                    'color': row[2],
                    'created_date': row[3]
                })
            return subjects
        else:
            # SQLite
            subjects = conn.execute('SELECT * FROM subjects ORDER BY name').fetchall()
            return [dict(subject) for subject in subjects]
    except Exception as e:
        print(f"❌ Kļūda ielādējot priekšmetus: {e}")
        return []
    finally:
        conn.close()

def save_subject(name, color):
    conn = get_db_connection()
    try:
        print(f"🔍 DEBUG: Saglabājam priekšmetu: {name}, {color}")
        
        c = conn.cursor()
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M')
        
        if isinstance(conn, psycopg.Connection):
            # PostgreSQL
            c.execute('INSERT INTO subjects (name, color, created_date) VALUES (%s, %s, %s)',
                     (name, color, current_time))
        else:
            # SQLite
            c.execute('INSERT INTO subjects (name, color, created_date) VALUES (?, ?, ?)',
                     (name, color, current_time))
        
        conn.commit()
        print(f"✅ Priekšmets saglabāts: {name}")
        return True
        
    except Exception as e:
        print(f"❌ Kļūda saglabājot priekšmetu: {e}")
        import traceback
        print(f"❌ Pilna kļūda: {traceback.format_exc()}")
        conn.rollback()
        return False
    finally:
        conn.close()

def delete_subject_from_db(subject_id):
    """Dzēš priekšmetu un visus tā darbus"""
    conn = get_db_connection()
    try:
        c = conn.cursor()
        
        print(f"🔍 DEBUG: Mēģinu dzēst priekšmetu ar ID: {subject_id}")
        
        # Vispirms atrod priekšmeta nosaukumu
        if 'DATABASE_URL' in os.environ:
            c.execute('SELECT name FROM subjects WHERE id = %s', (subject_id,))
        else:
            c.execute('SELECT name FROM subjects WHERE id = ?', (subject_id,))
        
        subject_result = c.fetchone()
        
        if subject_result:
            # Iegūstam priekšmeta nosaukumu atkarībā no datu bāzes tipa
            if 'DATABASE_URL' in os.environ:
                subject_name = subject_result[0]  # PostgreSQL - tuple
            else:
                subject_name = subject_result['name']  # SQLite - dict
            
            print(f"🔍 DEBUG: Priekšmeta nosaukums: {subject_name}")
            
            # Dzēš visus saistītos darbus
            if 'DATABASE_URL' in os.environ:
                # Dzēš testus
                c.execute('DELETE FROM tests WHERE subject = %s', (subject_name,))
                test_deleted = c.rowcount
                # Dzēš mājasdarbus
                c.execute('DELETE FROM homework WHERE subject = %s', (subject_name,))
                hw_deleted = c.rowcount
                # Dzēš priekšmetu
                c.execute('DELETE FROM subjects WHERE id = %s', (subject_id,))
            else:
                # Dzēš testus
                c.execute('DELETE FROM tests WHERE subject = ?', (subject_name,))
                test_deleted = c.rowcount
                # Dzēš mājasdarbus
                c.execute('DELETE FROM homework WHERE subject = ?', (subject_name,))
                hw_deleted = c.rowcount
                # Dzēš priekšmetu
                c.execute('DELETE FROM subjects WHERE id = ?', (subject_id,))
            
            conn.commit()
            print(f"✅ Priekšmets '{subject_name}' un visi tā darbi dzēsti")
            print(f"✅ Dzēsti {test_deleted} testi un {hw_deleted} mājasdarbi")
            
            # Notīram kešu
            load_tests.cache_clear()
            load_homework.cache_clear()
            
        else:
            print(f"❌ Priekšmets ar ID {subject_id} netika atrasts")
            
    except Exception as e:
        print(f"❌ Kļūda dzēšot priekšmetu: {e}")
        conn.rollback()
        raise e
    finally:
        conn.close()

# Darbu funkcijas
@lru_cache(maxsize=256)
def load_tests():
    """Кешированные тесты со временем"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        if isinstance(conn, psycopg.Connection):
            # PostgreSQL
            cursor.execute('SELECT * FROM tests ORDER BY date, time')
            tests_data = cursor.fetchall()
            
            # Конвертируем tuple в dict
            tests = []
            for row in tests_data:
                test_dict = {}
                for i, column in enumerate(cursor.description):
                    test_dict[column.name] = row[i]
                tests.append(test_dict)
        else:
            # SQLite
            cursor.execute('SELECT * FROM tests ORDER BY date, time')
            tests_data = cursor.fetchall()
            tests = [dict(test) for test in tests_data]
        
        # Добавляем days_left со временем
        for test in tests:
            time_value = test.get('time', '23:59')
            test['days_left'] = calculate_days_left(test['date'], time_value)
        
        print(f"✅ Загружено {len(tests)} тестов")
        return tests
        
    except Exception as e:
        print(f"❌ Ошибка загрузки тестов: {e}")
        return []
    finally:
        conn.close()

def save_test(subject, test_type, date, time, description, due_date=None):
    conn = get_db_connection()
    try:
        c = conn.cursor()
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M')
        
        print(f"🔍 СОХРАНЕНИЕ ТЕСТА: {subject}, {test_type}, {date}, {time}, due_date: {due_date}")
        
        if isinstance(conn, psycopg.Connection):
            c.execute('INSERT INTO tests (subject, type, date, time, description, due_date, added_date) VALUES (%s, %s, %s, %s, %s, %s, %s)',
                     (subject, test_type, date, time, description, due_date, current_time))
        else:
            c.execute('INSERT INTO tests (subject, type, date, time, description, due_date, added_date) VALUES (?, ?, ?, ?, ?, ?, ?)',
                     (subject, test_type, date, time, description, due_date, current_time))
        
        conn.commit()
        print(f"✅ Тест сохранен в БД: {subject} - {test_type}")
        
        load_tests.cache_clear()
        return True
        
    except Exception as e:
        print(f"❌ Ошибка сохранения теста: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def delete_test_from_db(test_id):
    """Dzēš testu no datu bāzes"""
    conn = get_db_connection()
    try:
        c = conn.cursor()
        
        print(f"🔍 DEBUG: Mēģinu dzēst testu ar ID: {test_id}")
        
        if 'DATABASE_URL' in os.environ:
            # PostgreSQL
            c.execute('DELETE FROM tests WHERE id = %s', (test_id,))
        else:
            # SQLite
            c.execute('DELETE FROM tests WHERE id = ?', (test_id,))
            
        conn.commit()
        print(f"✅ Tests ar ID {test_id} veiksmīgi dzēsts")
        
        # Notīram kešu
        load_tests.cache_clear()
        
    except Exception as e:
        print(f"❌ Kļūda dzēšot testu: {e}")
        conn.rollback()
        raise e
    finally:
        conn.close()
# Mājasdarbu funkcijas
@lru_cache(maxsize=256)
def load_homework():
    """Кешированные домашние задания со временем"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        if isinstance(conn, psycopg.Connection):
            # PostgreSQL
            cursor.execute('SELECT * FROM homework ORDER BY date, time')
            homework_data = cursor.fetchall()
            
            # Конвертируем tuple в dict
            homework = []
            for row in homework_data:
                hw_dict = {}
                for i, column in enumerate(cursor.description):
                    hw_dict[column.name] = row[i]
                homework.append(hw_dict)
        else:
            # SQLite
            cursor.execute('SELECT * FROM homework ORDER BY date, time')
            homework_data = cursor.fetchall()
            homework = [dict(hw) for hw in homework_data]
        
        # Добавляем days_left со временем
        for hw in homework:
            time_value = hw.get('time', '23:59')
            hw['days_left'] = calculate_days_left(hw['date'], time_value)
        
        print(f"✅ Загружено {len(homework)} домашних заданий")
        return homework
        
    except Exception as e:
        print(f"❌ Ошибка загрузки домашних заданий: {e}")
        return []
    finally:
        conn.close()

def save_homework(subject, title, date, time, description, due_date=None):
    conn = get_db_connection()
    try:
        c = conn.cursor()
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M')
        
        print(f"🔍 SAGLABĀJAM MĀJASDARBU: {subject}, {title}, {date}, {time}, due_date: {due_date}")
        
        if not time:
            time = '23:59'
        
        if isinstance(conn, psycopg.Connection):
            c.execute('''
                INSERT INTO homework (subject, title, date, time, description, due_date, type, added_date) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ''', (subject, title, date, time, description, due_date, 'Mājasdarbs', current_time))
        else:
            c.execute('''
                INSERT INTO homework (subject, title, date, time, description, due_date, type, added_date) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (subject, title, date, time, description, due_date, 'Mājasdarbs', current_time))
        
        conn.commit()
        print(f"✅ МАJASDARBS VEIKSMĪGI SAGLABĀTS: {subject} - {title}")
        
        load_homework.cache_clear()
        return True
        
    except Exception as e:
        print(f"❌ KLŪDA SAGLABĀJOT MĀJASDARBU: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def delete_homework(hw_id):
    """Dzēš mājasdarbu no datu bāzes"""
    conn = get_db_connection()
    try:
        c = conn.cursor()
        
        print(f"🔍 DEBUG: Mēģinu dzēst mājasdarbu ar ID: {hw_id}")
        
        if 'DATABASE_URL' in os.environ:
            # PostgreSQL
            c.execute('DELETE FROM homework WHERE id = %s', (hw_id,))
        else:
            # SQLite
            c.execute('DELETE FROM homework WHERE id = ?', (hw_id,))
            
        conn.commit()
        print(f"✅ Mājasdarbs ar ID {hw_id} veiksmīgi dzēsts")
        
        # Notīram kešu
        load_homework.cache_clear()
        
    except Exception as e:
        print(f"❌ Kļūda dzēšot mājasdarbu: {e}")
        conn.rollback()
        raise e
    finally:
        conn.close()

# Ziņu funkcijas
def load_news():
    conn = get_db_connection()
    try:
        if isinstance(conn, psycopg.Connection):
            # PostgreSQL
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM news ORDER BY date DESC')
            news_data = cursor.fetchall()
            
            # Konvertējam tuple uz dict
            news = []
            for row in news_data:
                news.append({
                    'id': row[0],
                    'title': row[1],
                    'content': row[2],
                    'date': row[3],
                    'image_url': row[4],
                    'is_active': row[5],
                    'created_date': row[6],
                    'updated_date': row[7]
                })
            return news
        else:
            # SQLite
            news = conn.execute('SELECT * FROM news ORDER BY date DESC').fetchall()
            return [dict(item) for item in news]
    except Exception as e:
        print(f"❌ Kļūda ielādējot ziņas: {e}")
        return []
    finally:
        conn.close()

def save_news(title, content, date, image_url, is_active):
    conn = get_db_connection()
    try:
        c = conn.cursor()
        if 'DATABASE_URL' in os.environ:
            c.execute('INSERT INTO news (title, content, date, image_url, is_active, created_date) VALUES (%s, %s, %s, %s, %s, %s)',
                     (title, content, date, image_url, is_active, datetime.now().strftime('%Y-%m-%d %H:%M')))
        else:
            c.execute('INSERT INTO news (title, content, date, image_url, is_active, created_date) VALUES (?, ?, ?, ?, ?, ?)',
                     (title, content, date, image_url, is_active, datetime.now().strftime('%Y-%m-%d %H:%M')))
        conn.commit()
    except Exception as e:
        print(f"Kļūda saglabājot ziņu: {e}")
        conn.rollback()
        raise e
    finally:
        conn.close()

def update_news(news_id, title, content, date, image_url, is_active):
    conn = get_db_connection()
    try:
        c = conn.cursor()
        if 'DATABASE_URL' in os.environ:
            c.execute('''UPDATE news SET title = %s, content = %s, date = %s, image_url = %s, is_active = %s, updated_date = %s
                        WHERE id = %s''',
                     (title, content, date, image_url, is_active, datetime.now().strftime('%Y-%m-%d %H:%M'), news_id))
        else:
            c.execute('''UPDATE news SET title = ?, content = ?, date = ?, image_url = ?, is_active = ?, updated_date = ?
                        WHERE id = ?''',
                     (title, content, date, image_url, is_active, datetime.now().strftime('%Y-%m-%d %H:%M'), news_id))
        conn.commit()
    except Exception as e:
        print(f"Kļūda atjauninot ziņu: {e}")
        conn.rollback()
        raise e
    finally:
        conn.close()

def delete_news(news_id):
    conn = get_db_connection()
    try:
        c = conn.cursor()
        if 'DATABASE_URL' in os.environ:
            c.execute('DELETE FROM news WHERE id = %s', (news_id,))
        else:
            c.execute('DELETE FROM news WHERE id = ?', (news_id,))
        conn.commit()
        print(f"✅ Ziņa ar ID {news_id} dzēsta")
    except Exception as e:
        print(f"Kļūda dzēšot ziņu: {e}")
        conn.rollback()
        raise e
    finally:
        conn.close()

# TERMS FUNKCIJAS
def load_terms():
    """Ielādē lietošanas noteikumus"""
    conn = get_db_connection()
    try:
        if isinstance(conn, psycopg.Connection):
            # PostgreSQL - atgriež tuple
            cursor = conn.cursor()
            cursor.execute('SELECT content FROM terms ORDER BY id DESC LIMIT 1')
            terms = cursor.fetchone()
            if terms:
                return terms[0]  # Tuple indekss 0
            return 'Šeit būs lietošanas noteikumi...'
        else:
            # SQLite - atgriež Row object
            terms = conn.execute('SELECT content FROM terms ORDER BY id DESC LIMIT 1').fetchone()
            if terms:
                return terms['content']
            return 'Šeit būs lietošanas noteikumi...'
    except Exception as e:
        print(f"❌ Kļūda ielādējot noteikumus: {e}")
        return 'Šeit būs lietošanas noteikumi...'
    finally:
        conn.close()

def save_terms(content):
    conn = get_db_connection()
    try:
        c = conn.cursor()
        if 'DATABASE_URL' in os.environ:
            c.execute('INSERT INTO terms (content, updated_date) VALUES (%s, %s)',
                     (content, datetime.now().strftime('%Y-%m-%d %H:%M')))
        else:
            c.execute('INSERT INTO terms (content, updated_date) VALUES (?, ?)',
                     (content, datetime.now().strftime('%Y-%m-%d %H:%M')))
        conn.commit()
    except Exception as e:
        print(f"Kļūda saglabājot noteikumus: {e}")
        conn.rollback()
        raise e
    finally:
        conn.close()

# Palīgfunkcijas
def is_host():
    return session.get('is_host', False)

def calculate_days_left(date_str, time_str='23:59', due_date_str=None):
    """Aprēķina atlikušās dienas līdz termiņam - izmanto due_date ja tas ir norādīts"""
    try:
        # Ja ir due_date, izmanto to, citādi izmanto parasto datumu
        target_date = due_date_str if due_date_str else date_str
        
        if not time_str or time_str == '':
            time_str = '23:59'
        
        datetime_str = f"{target_date} {time_str}"
        deadline = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M')
        now = datetime.now()
        
        time_left = deadline - now
        
        if time_left.total_seconds() <= 0:
            return 0
        else:
            return time_left.days
            
    except Exception as e:
        print(f"Kļūda aprēķinot laiku: {e}")
        return 999

def get_work_status(days_left, time_str='23:59'):
    """Atgriež darba statusu"""
    if days_left == 0:
        return "today"
    elif days_left < 0:
        return "overdue" 
    elif days_left == 1:
        return "tomorrow"
    elif days_left <= 7:
        return "soon"
    else:
        return "future"


# RTU SCRAPER KLASE
class RTUScraper:
    def __init__(self):
        self.base_url = "https://nodarbibas.rtu.lv"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Content-Type': 'application/json',
        })
        
        self.rtu_params = {
            'semesterId': 28,
            'programId': 1393,
            'courseId': 1,
            'semesterProgramId': 27940,
            'year': 2025,
            'month': 11
        }

    def get_student_exams(self):
        """Iegūst eksāmenus no RTU"""
        try:
            print("🔄 Savienojos ar RTU sistēmu...")
            events = self.get_semester_events()
            
            if events:
                print(f"✅ Iegūti {len(events)} notikumi no RTU")
                exams = self.extract_exams_from_events(events)
                return {
                    "success": True,
                    "exams_found": len(exams),
                    "exams": exams,
                    "note": "ĪSTIE DATI NO RTU"
                }
            else:
                print("❌ Neizdevās iegūt datus no RTU")
                return self.create_test_data()
                
        except Exception as e:
            print(f"❌ Kļūda: {e}")
            return self.create_test_data()

    def get_semester_events(self):
        """Iegūst semestra notikumus"""
        try:
            url = f"{self.base_url}/getSemesterProgEventList"
            current_year = datetime.now().year
            
            payload = {
                "semesterProgramId": self.rtu_params['semesterProgramId'],
                "year": current_year
            }
            
            response = self.session.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return data
            else:
                return None
                
        except Exception as e:
            print(f"❌ Kļūda iegūstot notikumus: {e}")
            return None

    def extract_exams_from_events(self, events_data):
        """No notikumiem izfiltrē eksāmenus"""
        exams = []
        
        if not events_data or not isinstance(events_data, list):
            return exams
        
        for event in events_data:
            event_name = event.get('nosaukums', '') or event.get('name', '') or event.get('subject', '')
            event_type = self.determine_event_type(event_name)
            
            if event_type in ['Eksāmens', 'Tests']:
                exam_data = {
                    'subject': event_name,
                    'type': event_type,
                    'date': self.extract_date(event),
                    'time': event.get('laiks') or event.get('time'),
                    'room': event.get('telpa') or event.get('room'),
                    'description': f"RTU {event_type}",
                    'original_data': event
                }
                exams.append(exam_data)
        
        return exams

    def determine_event_type(self, event_name):
        """Noteic notikuma veidu pēc nosaukuma"""
        event_lower = event_name.lower()
        
        if 'eksāmens' in event_lower or 'exam' in event_lower:
            return 'Eksāmens'
        elif 'tests' in event_lower or 'test' in event_lower:
            return 'Tests'
        elif 'laboratorijas' in event_lower or 'lab' in event_lower:
            return 'LD'
        
        return 'Cits notikums'

    def extract_date(self, event):
        """Ekstraktē datumu"""
        date_str = event.get('datums') or event.get('date') or event.get('startDate')
        if date_str:
            try:
                if 'T' in date_str:
                    dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                else:
                    dt = datetime.strptime(date_str, '%Y-%m-%d')
                return dt.strftime('%Y-%m-%d')
            except:
                print(f"⚠️ Nevarēju parsēt datumu: {date_str}")
        
        return datetime.now().strftime('%Y-%m-%d')

    def create_test_data(self):
        """Fallback testa dati"""
        test_exams = [
            {
                'subject': 'Kvalitātes vadības pamati',
                'type': 'Eksāmens',
                'date': '2025-01-15',
                'description': 'RTU Eksāmens',
                'time': '10:00',
                'room': 'A-101'
            }
        ]
        
        return {
            "success": True,
            "exams_found": len(test_exams),
            "exams": test_exams,
            "note": "TESTA DATI - API nereaģē"
        }

# .ICS IMPORTĒŠANAS FUNKCIJAS
def parse_ics_file(ics_content):
    """Parsē .ics failu un pievieno darbus"""
    tests = load_tests()
    imported_count = 0
    
    lines = ics_content.split('\n')
    current_event = {}
    
    for line in lines:
        line = line.strip()
        
        if line == 'BEGIN:VEVENT':
            current_event = {}
        elif line == 'END:VEVENT':
            if current_event:
                test = create_test_from_ics_event(current_event)
                if test and not test_exists(tests, test):
                    save_test(test['subject'], test['type'], test['date'], test.get('description', ''))
                    imported_count += 1
            current_event = {}
        elif ':' in line:
            key, value = line.split(':', 1)
            current_event[key] = value
    
    return imported_count

def create_test_from_ics_event(event):
    """Izveido testu no .ics notikuma"""
    try:
        summary = event.get('SUMMARY', '')
        date_str = event.get('DTSTART', '')
        
        # Ekstrakta datumu
        if 'T' in date_str:
            date_str = date_str.split('T')[0]
        if len(date_str) == 8:
            date_str = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
        
        # Noteic darba veidu
        test_type = determine_test_type(summary)
        subject = extract_subject(summary, test_type)
        
        if subject and date_str:
            return {
                'subject': subject,
                'type': test_type,
                'date': date_str,
                'description': event.get('DESCRIPTION', ''),
                'source': 'ics_import'
            }

    except Exception as e:
        print(f"Kļūda izveidojot testu: {e}")
    
    return None

def determine_test_type(summary):
    """Noteic darba veidu pēc nosaukuma"""
    summary_lower = summary.lower()
    
# LABOTS - noņemta liekā rinda
    type_mapping = {
        'laboratorijas': 'LD',
        'laboratory': 'LD',
        'lab': 'LD',
        'mājasdarbs': 'Mājasdarbs',
        'homework': 'Mājasdarbs',
        'housework': 'Mājasdarbs',
        'hw': 'Mājasdarbs',
        'nd': 'Mājasdarbs',
        'prezentācija': 'Prezentācija',
        'presentation': 'Prezentācija',
        'kontroldarbs': 'Kontroldarbs',
        'test': 'Tests',
        'eksāmens': 'Eksāmens',
        'exam': 'Eksāmens',
        'starpeksāmens': 'Starpeksāmens',  # ✅ LABOTS - apvienots vienā rindā
        'midterm': 'Starpeksāmens',        
        'mid-term': 'Starpeksāmens', 
    }
    
    for keyword, test_type in type_mapping.items():
        if keyword in summary_lower:
            return test_type
    
    return 'Kontroldarbs'

def extract_subject(summary, test_type):
    """Izvelk priekšmeta nosaukumu"""
    subject = summary
    
    remove_phrases = [
        'laboratorijas darbs', 'laboratory work', 'lab work', 'lab',
        'mājasdarbs', 'homework', 'housework', 'hw',
        'prezentācija', 'presentation', 
        'kontroldarbs', 'test', 'eksāmens', 'exam'
        'starpeksamens', 'midterm', 'mid-term'
    ]
    
    for phrase in remove_phrases:
        subject = re.sub(phrase, '', subject, flags=re.IGNORECASE)
    
    subject = re.sub(r'[\-\–]', '', subject)
    subject = subject.strip()
    
    return subject if subject else 'Nenosaukts priekšmets'

def test_exists(tests, new_test):
    """Pārbauda vai tests jau eksistē"""
    for test in tests:
        if (test['subject'] == new_test['subject'] and 
            test['date'] == new_test['date'] and 
            test['type'] == new_test['type']):
            return True
    return False

def convert_postgresql_to_dict(data, cursor):
    """Konvertē PostgreSQL tuple uz dictionary"""
    if not data:
        return None
    
    result = {}
    for i, column in enumerate(cursor.description):
        result[column.name] = data[i]
    return result

# ================= WEBSOCKET REAL-TIME FUNKCIJAS =================

@socketio.on('connect')
def handle_connect():
    """Jauns lietotājs pieslēdzas"""
    user_id = request.sid  # Unikāls sesijas ID
    online_users.add(user_id)
    
    # Atjaunina visiem klientiem online skaitu
    emit('online_count_update', {'count': len(online_users)}, broadcast=True)
    
    print(f"✅ Lietotājs pieslēdzies. Online: {len(online_users)}")

@socketio.on('disconnect')
def handle_disconnect():
    """Lietotājs atslēdzas"""
    user_id = request.sid
    if user_id in online_users:
        online_users.remove(user_id)
    
    # Atjaunina visiem klientiem online skaitu
    emit('online_count_update', {'count': len(online_users)}, broadcast=True)
    
    print(f"❌ Lietotājs atslēdzies. Online: {len(online_users)}")

def get_online_count():
    """Atgriež online lietotāju skaitu"""
    return len(online_users)

# ================= SUBJECT DETAILS FUNCTIONS =================

def get_subject_details(subject_name):
    """Iegūst detalizētu informāciju par priekšmetu"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        if 'DATABASE_URL' in os.environ:
            cursor.execute('SELECT * FROM subjects WHERE name = %s', (subject_name,))
        else:
            cursor.execute('SELECT * FROM subjects WHERE name = ?', (subject_name,))
        
        subject = cursor.fetchone()
        if subject:
            if isinstance(subject, tuple):  # PostgreSQL
                return {
                    'id': subject[0],
                    'name': subject[1],
                    'color': subject[2],
                    'created_date': subject[3],
                    'description': subject[4] if len(subject) > 4 else ''
                }
            else:  # SQLite
                return dict(subject)
        return None
        
    except Exception as e:
        print(f"❌ Kļūda iegūstot priekšmetu: {e}")
        return None
    finally:
        conn.close()

def get_subject_categories(subject_id):
    """Iegūst failu kategorijas priekšmetam"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        if 'DATABASE_URL' in os.environ:
            cursor.execute('''
                SELECT sc.*, COUNT(sf.id) as file_count
                FROM subject_categories sc
                LEFT JOIN subject_files sf ON sc.id = sf.category_id
                WHERE sc.subject_id = %s
                GROUP BY sc.id, sc.name, sc.description, sc.color, sc.created_date
                ORDER BY sc.name
            ''', (subject_id,))
        else:
            cursor.execute('''
                SELECT sc.*, COUNT(sf.id) as file_count
                FROM subject_categories sc
                LEFT JOIN subject_files sf ON sc.id = sf.category_id
                WHERE sc.subject_id = ?
                GROUP BY sc.id
                ORDER BY sc.name
            ''', (subject_id,))
        
        categories = cursor.fetchall()
        
        # Konvertējam uz dictionary
        category_list = []
        for cat in categories:
            if isinstance(cat, tuple):  # PostgreSQL
                category_list.append({
                    'id': cat[0],
                    'subject_id': cat[1],
                    'name': cat[2],
                    'description': cat[3],
                    'color': cat[4],
                    'created_date': cat[5],
                    'file_count': cat[6]
                })
            else:  # SQLite
                category_list.append(dict(cat))
        
        return category_list
        
    except Exception as e:
        print(f"❌ Kļūda iegūstot kategorijas: {e}")
        return []
    finally:
        conn.close()

def get_files_by_category(category_id):
    """Iegūst failus kategorijai"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        if 'DATABASE_URL' in os.environ:
            cursor.execute('SELECT * FROM subject_files WHERE category_id = %s ORDER BY upload_date DESC', (category_id,))
        else:
            cursor.execute('SELECT * FROM subject_files WHERE category_id = ? ORDER BY upload_date DESC', (category_id,))
        
        files = cursor.fetchall()
        
        # Konvertējam uz dictionary
        file_list = []
        for file in files:
            if isinstance(file, tuple):  # PostgreSQL
                file_list.append({
                    'id': file[0],
                    'subject_id': file[1],
                    'category_id': file[2],
                    'filename': file[3],
                    'original_filename': file[4],
                    'file_path': file[5],
                    'file_size': file[6],
                    'file_type': file[7],
                    'description': file[8],
                    'uploaded_by': file[9],
                    'upload_date': file[10]
                })
            else:  # SQLite
                file_list.append(dict(file))
        
        return file_list
        
    except Exception as e:
        print(f"❌ Kļūda iegūstot failus: {e}")
        return []
    finally:
        conn.close()

def create_subject_category(subject_id, name, description, color):
    """Izveido jaunu kategoriju priekšmetam"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M')
        
        if 'DATABASE_URL' in os.environ:
            cursor.execute('''
                INSERT INTO subject_categories (subject_id, name, description, color, created_date)
                VALUES (%s, %s, %s, %s, %s)
            ''', (subject_id, name, description, color, current_time))
        else:
            cursor.execute('''
                INSERT INTO subject_categories (subject_id, name, description, color, created_date)
                VALUES (?, ?, ?, ?, ?)
            ''', (subject_id, name, description, color, current_time))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ Kļūda izveidojot kategoriju: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def get_subject_with_stats(subject_name):
    """Iegūst priekšmetu ar visu statistiku - Sinhronizēta ar galveno lapu"""
    tests = load_tests_optimized()
    homework_list = load_homework_optimized()
    
    subject_work = []
    
    # Iegūstam visus darbus šim priekšmetam
    for test in tests:
        if test['subject'] == subject_name:
            test_copy = test.copy()
            test_copy['source'] = 'test'
            # ✅ Tāda pati days_left loģika kā galvenajā lapā
            test_copy['days_left'] = calculate_days_left(test['date'], test.get('time', '23:59'), test.get('due_date'))
            subject_work.append(test_copy)
    
    for hw in homework_list:
        if hw['subject'] == subject_name:
            hw_copy = hw.copy()
            hw_copy['source'] = 'homework'
            # ✅ Tāda pati days_left loģika kā galvenajā lapā
            hw_copy['days_left'] = calculate_days_left(hw['date'], hw.get('time', '23:59'), hw.get('due_date'))
            subject_work.append(hw_copy)
    
    # Sakārtojam pēc datuma
    subject_work.sort(key=lambda x: x['date'])
    
    # Iegūstam priekšmeta detaļas
    subject_details = get_subject_details(subject_name)
    
    return subject_details, subject_work

def get_user_settings(device_id):
    """Iegūst lietotāja iestatījumus pēc device_id"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        if 'DATABASE_URL' in os.environ:
            cursor.execute('''
                SELECT theme, custom_background, updated_date 
                FROM user_settings 
                WHERE device_id = %s
            ''', (device_id,))
        else:
            cursor.execute('''
                SELECT theme, custom_background, updated_date 
                FROM user_settings 
                WHERE device_id = ?
            ''', (device_id,))
        
        result = cursor.fetchone()
        
        if result:
            if isinstance(result, tuple):  # PostgreSQL
                return {
                    'theme': result[0],
                    'custom_background': result[1],
                    'updated_date': result[2]
                }
            else:  # SQLite
                return dict(result)
        
        return None
        
    except Exception as e:
        print(f"❌ Kļūda iegūstot lietotāja iestatījumus: {e}")
        return None
    finally:
        conn.close()

def get_user_device_id():
    """Ģenerē unikālu device_id lietotājam"""
    # Izmantojam IP + User-Agent kombināciju
    ip_address = request.remote_addr
    user_agent = request.headers.get('User-Agent', '')
    
    # Izveidojam hash no šīs kombinācijas
    import hashlib
    device_string = f"{ip_address}_{user_agent}"
    device_hash = hashlib.md5(device_string.encode()).hexdigest()
    
    # Saglabājam sesijā
    if 'device_id' not in session:
        session['device_id'] = device_hash
    
    return device_hash

def get_default_theme():
    """Iegūst noklusējuma tēmu no config"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        if 'DATABASE_URL' in os.environ:
            cursor.execute('SELECT config_value FROM app_config WHERE config_key = %s', ('default_theme',))
        else:
            cursor.execute('SELECT config_value FROM app_config WHERE config_key = ?', ('default_theme',))
        
        result = cursor.fetchone()
        
        if result:
            if isinstance(result, tuple):
                return result[0] or 'default'
            else:
                return result['config_value'] or 'default'
        
        return 'default'
        
    except Exception as e:
        print(f"❌ Kļūda iegūstot noklusējuma tēmu: {e}")
        return 'default'
    finally:
        conn.close()

def fix_work_structure(data):
    """Исправляет структуру work_by_subject, если она неправильная"""
    print(f"🔧 Исправление структуры данных. Тип входных данных: {type(data)}")
    
    if not data:
        print("   Данных нет, возвращаю пустой словарь")
        return {}
    
    # Если это уже словарь, проверяем его структуру
    if isinstance(data, dict):
        fixed = {}
        for subject, works in data.items():
            if isinstance(works, (list, tuple)):
                # Преобразуем все элементы в словари
                fixed_works = []
                for work in works:
                    if isinstance(work, dict):
                        fixed_works.append(work)
                    elif hasattr(work, '_asdict'):  # Для namedtuple
                        fixed_works.append(work._asdict())
                    elif isinstance(work, tuple):
                        # Пытаемся преобразовать tuple в dict
                        try:
                            # Предполагаем, что это результат PostgreSQL запроса
                            work_dict = {
                                'id': work[0] if len(work) > 0 else None,
                                'subject': work[1] if len(work) > 1 else None,
                                'type': work[2] if len(work) > 2 else None,
                                'date': work[3] if len(work) > 3 else None,
                                'time': work[4] if len(work) > 4 else '23:59',
                                'description': work[5] if len(work) > 5 else None,
                                'due_date': work[6] if len(work) > 6 else None,
                                'added_date': work[7] if len(work) > 7 else None
                            }
                            # Убираем None значения
                            work_dict = {k: v for k, v in work_dict.items() if v is not None}
                            fixed_works.append(work_dict)
                        except:
                            print(f"   Не могу преобразовать tuple: {work}")
                    else:
                        print(f"   Неизвестный тип work: {type(work)}")
                
                fixed[subject] = fixed_works
            else:
                print(f"   Работы для предмета {subject} не список: {type(works)}")
                fixed[subject] = []
        
        print(f"   Исправлено {len(fixed)} предметов")
        return fixed
    
    # Если это список
    elif isinstance(data, (list, tuple)):
        print(f"   Преобразую список из {len(data)} элементов в словарь")
        fixed = {}
        
        for item in data:
            # Пытаемся получить предмет
            subject = None
            work_dict = {}
            
            if isinstance(item, dict):
                subject = item.get('subject')
                work_dict = item
            elif isinstance(item, tuple):
                # Пытаемся найти subject в tuple
                try:
                    # Предполагаем, что subject на второй позиции (индекс 1)
                    if len(item) > 1:
                        subject = item[1]
                        work_dict = {
                            'id': item[0] if len(item) > 0 else None,
                            'subject': item[1] if len(item) > 1 else None,
                            'type': item[2] if len(item) > 2 else None,
                            'date': item[3] if len(item) > 3 else None,
                            'time': item[4] if len(item) > 4 else '23:59',
                            'description': item[5] if len(item) > 5 else None,
                            'due_date': item[6] if len(item) > 6 else None,
                            'added_date': item[7] if len(item) > 7 else None
                        }
                except:
                    print(f"   Не могу обработать tuple: {item}")
            
            if subject:
                if subject not in fixed:
                    fixed[subject] = []
                fixed[subject].append(work_dict)
        
        print(f"   Создано {len(fixed)} предметов из списка")
        return fixed
    
    print(f"   Неизвестный тип данных: {type(data)}")
    return {}

def safe_get_work_by_subject():
    """Безопасная функция группировки работ по предметам"""
    try:
        tests = load_tests()
        homework_list = load_homework()
        subjects = load_subjects()
        
        work_by_subject = {}
        
        # Преобразуем все работы в словари
        all_works = []
        
        # Тесты
        for test in tests:
            if isinstance(test, dict):
                test_dict = test.copy()
                test_dict['source'] = 'test'
                if 'type' not in test_dict:
                    test_dict['type'] = 'Tests'
                all_works.append(test_dict)
            elif hasattr(test, '__dict__'):
                # Если это объект Row
                test_dict = dict(test)
                test_dict['source'] = 'test'
                all_works.append(test_dict)
        
        # Домашние задания
        for hw in homework_list:
            if isinstance(hw, dict):
                hw_dict = hw.copy()
                hw_dict['source'] = 'homework'
                if 'type' not in hw_dict:
                    hw_dict['type'] = 'Mājasdarbs'
                all_works.append(hw_dict)
            elif hasattr(hw, '__dict__'):
                # Если это объект Row
                hw_dict = dict(hw)
                hw_dict['source'] = 'homework'
                all_works.append(hw_dict)
        
        # Группируем по предметам
        for work in all_works:
            subject = work.get('subject')
            if subject:
                if subject not in work_by_subject:
                    work_by_subject[subject] = []
                
                # Добавляем days_left если нет
                if 'days_left' not in work:
                    work['days_left'] = calculate_days_left(
                        work.get('date', ''),
                        work.get('time', '23:59'),
                        work.get('due_date')
                    )
                
                work_by_subject[subject].append(work)
        
        return work_by_subject
        
    except Exception as e:
        print(f"❌ Error in safe_get_work_by_subject: {e}")
        return {}
# ================= ROUTES =================

# ✅ PUBLISKIE ROUTE (bez paroles)


@app.route('/static/css/themes/<theme_name>.css')
def serve_theme_css(theme_name):
    """Serve theme CSS files"""
    theme_path = f'static/css/themes/{theme_name}.css'
    if os.path.exists(theme_path):
        return send_file(theme_path)
    else:
        # Fallback to default
        return send_file('static/css/themes/default.css')

@app.route('/')
def index():
    """Главная страница - УПРОЩЕННАЯ"""
    subjects = load_subjects_cached()
    news_list = load_news()
    
    # Получаем данные
    tests = load_tests()
    homework_list = load_homework()
    
    # Создаем безопасный work_by_subject
    work_by_subject = {}
    
    # Обрабатываем все работы и превращаем в словари
    all_work = []
    
    # Тесты
    for test in tests:
        if isinstance(test, dict):
            all_work.append(test)
        elif hasattr(test, '_asdict'):  # PostgreSQL namedtuple
            all_work.append(test._asdict())
        else:
            # Пытаемся создать dict из любого объекта
            try:
                all_work.append(dict(test))
            except:
                print(f"⚠️ Не могу преобразовать test: {type(test)}")
    
    # Домашние задания
    for hw in homework_list:
        if isinstance(hw, dict):
            all_work.append(hw)
        elif hasattr(hw, '_asdict'):
            all_work.append(hw._asdict())
        else:
            try:
                all_work.append(dict(hw))
            except:
                print(f"⚠️ Не могу преобразовать hw: {type(hw)}")
    
    # Группируем по предметам
    for work in all_work:
        if isinstance(work, dict):
            subject = work.get('subject')
            if subject:
                if subject not in work_by_subject:
                    work_by_subject[subject] = []
                work_by_subject[subject].append(work)
    
    print(f"✅ Subjects: {len(subjects)}, Work groups: {len(work_by_subject)}")
    
    # Активные новости
    active_news = [news for news in news_list if news.get('is_active', True)]
    active_news.sort(key=lambda x: x['date'], reverse=True)
    latest_news = active_news[:3]
    
    return render_template('index.html', 
                         terms_content=load_terms_cached(),
                         work_by_subject=work_by_subject,
                         subjects=subjects,
                         news=latest_news,
                         is_host=is_host(), 
                         now=datetime.now())

@app.route('/api/set_theme', methods=['POST'])
def api_set_theme():
    """Сохраняет тему пользователя"""
    try:
        data = request.get_json()
        theme = data.get('theme', 'default')
        
        # Сохраняем в сессии
        session['theme'] = theme
        
        # Сохраняем в базе для устройства (по IP или user_id)
        device_id = request.remote_addr  # Или создайте уникальный ID устройства
        save_user_theme(device_id, theme)
        
        return jsonify({'success': True, 'theme': theme})
        
    except Exception as e:
        print(f"❌ Ошибка сохранения темы: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/save_custom_theme', methods=['POST'])
def api_save_custom_theme():
    """Сохраняет кастомные настройки темы"""
    if not is_host():  # Или для всех пользователей
        return jsonify({'success': False, 'error': 'Нет прав'})
    
    try:
        data = request.get_json()
        device_id = request.remote_addr
        
        # Сохраняем в базе
        save_custom_theme(device_id, data)
        
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"❌ Ошибка сохранения кастомной темы: {e}")
        return jsonify({'success': False, 'error': str(e)})

def save_user_theme(device_id, theme):
    """Saglabā lietotāja tēmu datu bāzē"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Pārbaudam vai lietotājs jau eksistē
        existing_settings = get_user_settings(device_id)
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if existing_settings:
            # Atjauninam esošo ierakstu
            if 'DATABASE_URL' in os.environ:
                cursor.execute('''
                    UPDATE user_settings 
                    SET theme = %s, updated_date = %s 
                    WHERE device_id = %s
                ''', (theme, current_time, device_id))
            else:
                cursor.execute('''
                    UPDATE user_settings 
                    SET theme = ?, updated_date = ? 
                    WHERE device_id = ?
                ''', (theme, current_time, device_id))
        else:
            # Izveidojam jaunu ierakstu
            if 'DATABASE_URL' in os.environ:
                cursor.execute('''
                    INSERT INTO user_settings (device_id, theme, created_date, updated_date)
                    VALUES (%s, %s, %s, %s)
                ''', (device_id, theme, current_time, current_time))
            else:
                cursor.execute('''
                    INSERT INTO user_settings (device_id, theme, created_date, updated_date)
                    VALUES (?, ?, ?, ?)
                ''', (device_id, theme, current_time, current_time))
        
        conn.commit()
        print(f"✅ Tēma saglabāta priekš device_id: {device_id}")
        
    except Exception as e:
        print(f"❌ Kļūda saglabājot tēmu: {e}")
        conn.rollback()
    finally:
        conn.close()

def save_custom_theme(device_id, settings):
    """Saglabā pielāgotos iestatījumus"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        settings_json = json.dumps(settings)
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        existing_settings = get_user_settings(device_id)
        
        if existing_settings:
            # Atjauninam
            if 'DATABASE_URL' in os.environ:
                cursor.execute('''
                    UPDATE user_settings 
                    SET custom_background = %s, updated_date = %s 
                    WHERE device_id = %s
                ''', (settings_json, current_time, device_id))
            else:
                cursor.execute('''
                    UPDATE user_settings 
                    SET custom_background = ?, updated_date = ? 
                    WHERE device_id = ?
                ''', (settings_json, current_time, device_id))
        else:
            # Izveidojam jaunu
            if 'DATABASE_URL' in os.environ:
                cursor.execute('''
                    INSERT INTO user_settings (device_id, custom_background, created_date, updated_date)
                    VALUES (%s, %s, %s, %s)
                ''', (device_id, settings_json, current_time, current_time))
            else:
                cursor.execute('''
                    INSERT INTO user_settings (device_id, custom_background, created_date, updated_date)
                    VALUES (?, ?, ?, ?)
                ''', (device_id, settings_json, current_time, current_time))
        
        conn.commit()
        print(f"✅ Pielāgotie iestatījumi saglabāti: {device_id}")
        
    except Exception as e:
        print(f"❌ Kļūda saglabājot pielāgotos iestatījumus: {e}")
        conn.rollback()
    finally:
        conn.close()

@app.before_request
def load_user_settings():
    """Ielādē lietotāja iestatījumus katram pieprasījumam"""
    device_id = get_user_device_id()
    
    # Iegūstam iestatījumus no datu bāzes
    settings = get_user_settings(device_id)
    
    if settings:
        # Pielietojam tēmu no iestatījumiem
        session['theme'] = settings.get('theme', get_default_theme())
        
        # Saglabājam pielāgotos iestatījumus
        if 'custom_background' in settings and settings['custom_background']:
            try:
                g.custom_theme = json.loads(settings['custom_background'])
            except:
                g.custom_theme = None
        else:
            g.custom_theme = None
    else:
        # Noklusējuma iestatījumi
        session['theme'] = get_default_theme()
        g.custom_theme = None
    
    # Pievienojam globālajam kontekstam
    g.device_id = device_id
    g.user_settings = settings or {}

@app.route('/api/subject/<subject_name>/upload_file', methods=['POST'])
def upload_subject_file(subject_name):
    """Загружает файл для предмета"""
    if not is_host():
        return jsonify({'success': False, 'error': 'Нет прав'})
    
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'Файл не выбран'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'Файл не выбран'})
        
        if file and allowed_file(file.filename):
            # Сохраняем файл
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(file_path)
            
            # Получаем размер файла
            file_size = os.path.getsize(file_path)
            
            # Определяем тип файла
            file_type = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
            
            # Сохраняем в базу данных
            conn = get_db_connection()
            cursor = conn.cursor()
            
            subject_details = get_subject_details(subject_name)
            if not subject_details:
                return jsonify({'success': False, 'error': 'Предмет не найден'})
            
            category_id = request.form.get('category_id')
            description = request.form.get('description', '')
            
            if 'DATABASE_URL' in os.environ:
                cursor.execute('''
                    INSERT INTO subject_files 
                    (subject_id, category_id, filename, original_filename, file_path, file_size, file_type, description, uploaded_by, upload_date)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ''', (
                    subject_details['id'],
                    category_id if category_id else None,
                    unique_filename,
                    filename,
                    f"/static/uploads/{unique_filename}",
                    file_size,
                    file_type,
                    description,
                    'Хост',
                    datetime.now().strftime('%Y-%m-%d %H:%M')
                ))
            else:
                cursor.execute('''
                    INSERT INTO subject_files 
                    (subject_id, category_id, filename, original_filename, file_path, file_size, file_type, description, uploaded_by, upload_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    subject_details['id'],
                    category_id if category_id else None,
                    unique_filename,
                    filename,
                    f"/static/uploads/{unique_filename}",
                    file_size,
                    file_type,
                    description,
                    'Хост',
                    datetime.now().strftime('%Y-%m-%d %H:%M')
                ))
            
            conn.commit()
            conn.close()
            
            return jsonify({
                'success': True,
                'message': 'Файл успешно загружен',
                'file_path': f"/static/uploads/{unique_filename}"
            })
        
        return jsonify({'success': False, 'error': 'Неподдерживаемый формат файла'})
        
    except Exception as e:
        print(f"❌ Ошибка загрузки файла: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/file/<int:file_id>/delete', methods=['POST'])
def delete_subject_file(file_id):
    """Удаляет файл"""
    if not is_host():
        return jsonify({'success': False, 'error': 'Нет прав'})
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Получаем информацию о файле
        if 'DATABASE_URL' in os.environ:
            cursor.execute('SELECT file_path FROM subject_files WHERE id = %s', (file_id,))
        else:
            cursor.execute('SELECT file_path FROM subject_files WHERE id = ?', (file_id,))
        
        file_info = cursor.fetchone()
        
        if file_info:
            file_path = file_info[0] if isinstance(file_info, tuple) else file_info['file_path']
            
            # Удаляем физический файл
            local_path = file_path.replace('/static/', '')
            if os.path.exists(local_path):
                os.remove(local_path)
            
            # Удаляем запись из базы данных
            if 'DATABASE_URL' in os.environ:
                cursor.execute('DELETE FROM subject_files WHERE id = %s', (file_id,))
            else:
                cursor.execute('DELETE FROM subject_files WHERE id = ?', (file_id,))
            
            conn.commit()
        
        conn.close()
        
        return jsonify({'success': True, 'message': 'Файл удален'})
        
    except Exception as e:
        print(f"❌ Ошибка удаления файла: {e}")
        return jsonify({'success': False, 'error': str(e)})

# ОБНОВИТЕ ФУНКЦИЮ subject_tests В APP.PY:

@app.before_request
def load_user_theme():
    """Ielādē lietotāja izvēlēto tēmu"""
    # Pārbauda vai lietotājam ir saglabāta tēma
    theme = session.get('theme', 'default')
    g.theme = theme

@app.route('/api/set_theme', methods=['POST'])
def set_theme():
    """Saglabā lietotāja izvēlēto tēmu"""
    try:
        data = request.get_json()
        theme = data.get('theme', 'default')
        
        # Saglabā sesijā (pagaidu)
        session['theme'] = theme
        
        # Saglabā datu bāzē ilgtermiņam (ja vēlaties)
        # Vai izmantojiet localStorage puses
        print(f"✅ Lietotājs nomainīja tēmu uz: {theme}")
        
        return jsonify({'success': True, 'theme': theme})
        
    except Exception as e:
        print(f"❌ Kļūda saglabājot tēmu: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/subject/<subject_name>')
def subject_details_page(subject_name):  # ✅ MAINĀM NOSAUKUMU UZ UNIKĀLU
    """Priekšmeta lapa - pilnībā sinhronizēta ar galveno lapu (JAUNĀ VERSIJA)"""
    print(f"🔍 Ielādēju priekšmeta lapu: {subject_name}")
    
    terms_content = load_terms_cached()
    subjects = load_subjects_cached()
    
    # ✅ IZMANTOJAM TIEŠI TĀDU PĀSI FUNKCIJU KĀ GALVENAJĀ LAPĀ
    subject_details, subject_work = get_subject_with_stats(subject_name)
    
    print(f"🔍 Priekšmetam '{subject_name}' atrasti {len(subject_work)} darbi")
    
    # Iegūstam kategorijas un failus
    if subject_details:
        file_categories = get_subject_categories(subject_details['id'])
        files_by_category = {}
        total_files = 0
        
        for category in file_categories:
            category_files = get_files_by_category(category['id'])
            files_by_category[category['id']] = category_files
            total_files += len(category_files)
    else:
        file_categories = []
        files_by_category = {}
        total_files = 0
    
    return render_template('subject.html', 
                         terms_content=terms_content,
                         subject_name=subject_name,
                         subject_details=subject_details,
                         tests=subject_work,  # ✅ SINHRONIZĒTI DATI
                         subjects=subjects,
                         file_categories=file_categories,
                         files_by_category=files_by_category,
                         total_files=total_files,
                         get_work_status=get_work_status,
                         is_host=is_host())

@app.route('/all')
def all_tests():
    """Visi darbi - VISI var skatīties"""
    terms_content = load_terms()
    tests = load_tests()
    homework_list = load_homework()
    subjects = load_subjects()
    now = datetime.now()
    
    all_work = tests + homework_list
    for work in all_work:
        work['days_left'] = calculate_days_left(work['date'])
    
    return render_template('all.html', 
                         terms_content=terms_content,
                         tests=all_work, 
                         subjects=subjects,
                         is_host=is_host(), 
                         now=now)


@app.route('/homework')
def homework():
    """Mājasdarbi - VISI var skatīties"""
    terms_content = load_terms()
    homework_list = load_homework()
    now = datetime.now()
    
    for hw in homework_list:
        hw['days_left'] = calculate_days_left(hw['date'])
    
    return render_template('homework.html', 
                         terms_content=terms_content,
                         homework=homework_list,
                         is_host=is_host(), 
                         now=now)

# TERMS ROUTE
@app.route('/update_terms', methods=['POST'])
def update_terms():
    """Atjaunina lietošanas noteikumus"""
    if not is_host():
        return jsonify({'success': False, 'error': 'Nav tiesību'})
    
    data = request.get_json()
    save_terms(data.get('terms_content', ''))
    return jsonify({'success': True})

# 🔐 AIZSARGĀTIE ROUTE (ar paroli)
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Ieeja rediģēšanas režīmā"""
    if request.method == 'POST':
        if request.form.get('password') == HOST_PASSWORD:
            session['is_host'] = True
            return redirect('/')
        return render_template('login.html', error="Nepareiza parole!")
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Iziet no rediģēšanas režīma"""
    session.pop('is_host', None)
    return redirect('/')

@app.route('/add', methods=['GET', 'POST'])
def add_test():
    if not is_host():
        return redirect('/login')
    
    terms_content = load_terms()
    subjects = load_subjects()
    
    if request.method == 'POST':
        time_value = request.form.get('time', '23:59')  # ✅ Noklusējums 23:59
        due_date = request.form.get('due_date')
        save_test(
            request.form.get('subject'),
            request.form.get('type'), 
            request.form.get('date'),
            time_value,  # ✅ PIEVIENOTS
            request.form.get('description', ''),
            due_date
        )
        return redirect('/')
    
    min_date = datetime.now().strftime('%Y-%m-%d')
    return render_template('add.html', 
                         terms_content=terms_content,
                         min_date=min_date, 
                         subjects=subjects)

@app.route('/add_subject', methods=['GET', 'POST'])
def add_subject():
    """Pievienot priekšmetu - AIZSARGĀTS"""
    if not is_host():
        return redirect('/login')
    
    terms_content = load_terms()
    
    if request.method == 'POST':
        subject_name = request.form.get('subject_name')
        color = request.form.get('color', '#3498db')
        
        if subject_name and save_subject(subject_name, color):
            return redirect('/')
    
    return render_template('add_subject.html', terms_content=terms_content)

@app.route('/add_homework', methods=['GET', 'POST'])
def add_homework():
    if not is_host():
        return redirect('/login')
    
    terms_content = load_terms()
    subjects = load_subjects()
    
    if request.method == 'POST':
        time_value = request.form.get('time', '23:59')  # ✅ Noklusējums 23:59
        due_date = request.form.get('due_date') 
        save_homework(
            request.form.get('subject'),
            request.form.get('title'),
            request.form.get('date'), 
            time_value,  # ✅ PIEVIENOTS
            request.form.get('description', ''),
            due_date
        )
        return redirect('/homework')
    
    min_date = datetime.now().strftime('%Y-%m-%d')
    return render_template('add_homework.html', 
                         terms_content=terms_content,
                         min_date=min_date, 
                         subjects=subjects)

@app.route('/delete/<int:test_id>')
def delete_test(test_id):
    """Dzēš testu - AIZSARGĀTS"""
    if not is_host():
        return redirect('/login')
    
    try:
        delete_test_from_db(test_id)
        return redirect('/all')
    except Exception as e:
        return f"Kļūda dzēšot testu: {e}", 500

@app.route('/delete_homework/<int:hw_id>')
def delete_homework_route(hw_id):
    """Dzēš mājasdarbu - AIZSARGĀTS"""
    if not is_host():
        return redirect('/login')
    
    try:
        delete_homework(hw_id)
        return redirect('/homework')
    except Exception as e:
        return f"Kļūda dzēšot mājasdarbu: {e}", 500

@app.route('/delete_subject/<int:subject_id>')
def delete_subject(subject_id):
    """Dzēš priekšmetu - AIZSARGĀTS"""
    if not is_host():
        return redirect('/login')
    
    try:
        delete_subject_from_db(subject_id)
        return redirect('/')
    except Exception as e:
        return f"Kļūda dzēšot priekšmetu: {e}", 500

@app.route('/news', methods=['GET', 'POST'])
def manage_news():
    """Pārvaldīt ziņas - AIZSARGĀTS"""
    if not is_host():
        return redirect('/login')
    
    terms_content = load_terms()
    
    if request.method == 'POST':
        image_url = ''
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4().hex}_{filename}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                file.save(file_path)
                image_url = f"/static/uploads/{unique_filename}"
        
        save_news(
            request.form.get('title'),
            request.form.get('content'),
            request.form.get('date'),
            image_url,
            request.form.get('is_active') == 'on'
        )
        return redirect('/news')
    
    news_list = load_news()
    min_date = datetime.now().strftime('%Y-%m-%d')
    return render_template('news.html', 
                         terms_content=terms_content,
                         news=news_list, 
                         min_date=min_date)

@app.route('/delete_news/<int:news_id>')
def delete_news_route(news_id):
    """Dzēst ziņu - AIZSARGĀTS"""
    if not is_host():
        return redirect('/login')
    
    delete_news(news_id)
    return redirect('/news')

@app.route('/edit_news/<int:news_id>', methods=['GET', 'POST'])
def edit_news(news_id):
    """Rediģēt ziņu - AIZSARGĀTS"""
    if not is_host():
        return redirect('/login')
    
    terms_content = load_terms()
    news_list = load_news()
    news_item = next((news for news in news_list if news['id'] == news_id), None)
    
    if not news_item:
        return redirect('/news')
    
    if request.method == 'POST':
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '' and allowed_file(file.filename):
                if news_item.get('image_url'):
                    old_image_path = news_item['image_url'].replace('/static/', '')
                    if os.path.exists(old_image_path):
                        os.remove(old_image_path)
                
                filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4().hex}_{filename}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                file.save(file_path)
                news_item['image_url'] = f"/static/uploads/{unique_filename}"
        
        update_news(
            news_id,
            request.form.get('title'),
            request.form.get('content'),
            request.form.get('date'),
            news_item.get('image_url', ''),
            request.form.get('is_active') == 'on'
        )
        return redirect('/news')
    
    min_date = datetime.now().strftime('%Y-%m-%d')
    return render_template('edit_news.html', 
                         terms_content=terms_content,
                         news=news_item, 
                         min_date=min_date)
# ================= OPTIMIZĒTĀS FUNKCIJAS =================

def load_all_work():
    """Ielādē VISUS darbus vienā - LABOTS"""
    conn = get_db_connection()
    
    # Ielādē testus
    tests = conn.execute('SELECT * FROM tests').fetchall()
    test_list = [dict(test) for test in tests]
    for test in test_list:
        test['source'] = 'test'  # Pievieno source identifikatoru
    
    # Ielādē mājasdarbus
    homework_list = conn.execute('SELECT * FROM homework').fetchall()
    homework_list = [dict(hw) for hw in homework_list]
    for hw in homework_list:
        hw['source'] = 'homework'  # Pievieno source identifikatoru
        hw['type'] = 'Mājasdarbs'  # Pārliecinās, ka tips ir Mājasdarbs
    
    conn.close()
    
    all_work = test_list + homework_list
    
    # Pievieno days_left katram darbam
    for work in all_work:
        work['days_left'] = calculate_days_left(work['date'])
    
    return all_work

def get_work_by_subject_optimized():
    """Optimizēta funkcija priekšmetu darbu grupēšanai - FIXED"""
    tests = load_tests_optimized()
    homework_list = load_homework_optimized()
    subjects = load_subjects_cached()
    
    work_by_subject = {}
    
    print(f"🔍 DEBUG get_work_by_subject_optimized:")
    print(f"   Tests: {len(tests)} items, type: {type(tests)}")
    print(f"   Homework: {len(homework_list)} items, type: {type(homework_list)}")
    
    if tests and isinstance(tests[0], dict):
        print(f"   First test keys: {list(tests[0].keys())}")
    
    # Grupējam darbus pa priekšmetiem
    for subject in subjects:
        subject_name = subject['name']
        subject_work = []
        
        # Pievienojam testus - ПРОВЕРЯЕМ что это словари
        for test in tests:
            if isinstance(test, dict) and test.get('subject') == subject_name:
                test_copy = test.copy()
                if 'days_left' not in test_copy:
                    test_copy['days_left'] = calculate_days_left(
                        test_copy.get('date', ''),
                        test_copy.get('time', '23:59'),
                        test_copy.get('due_date')
                    )
                test_copy['source'] = 'test'
                subject_work.append(test_copy)
            elif hasattr(test, 'subject') and test.subject == subject_name:
                # Если это объект Row, конвертируем в dict
                test_dict = dict(test)
                if 'days_left' not in test_dict:
                    test_dict['days_left'] = calculate_days_left(
                        test_dict.get('date', ''),
                        test_dict.get('time', '23:59'),
                        test_dict.get('due_date')
                    )
                test_dict['source'] = 'test'
                subject_work.append(test_dict)
        
        # Продолжаем для homework...
        
        if subject_work:
            subject_work.sort(key=lambda x: x.get('date', ''))
            work_by_subject[subject_name] = subject_work
    
    return work_by_subject
# ================= LABOTIE CALENDAR ROUTES =================

@app.route('/calendar/<string:work_type>/<int:work_id>')
def download_calendar(work_type, work_id):
    """Lejupielādēt kalendāru - LABOTS"""
    try:
        print(f"🔍 DEBUG: Sākam kalendāra ģenerēšanu - work_type: {work_type}, work_id: {work_id}")
        
        # Ielādē atsevišķi testus un mājasdarbus
        if work_type == 'test':
            tests = load_tests()
            print(f"🔍 DEBUG: Ielādēti {len(tests)} testi")
            work = next((t for t in tests if t['id'] == work_id), None)
        else:
            homework_list = load_homework()
            print(f"🔍 DEBUG: Ielādēti {len(homework_list)} mājasdarbi")
            work = next((hw for hw in homework_list if hw['id'] == work_id), None)
        
        print(f"🔍 DEBUG: Atrastais darbs: {work}")
        
        if not work:
            print("❌ DEBUG: Darbs nav atrasts")
            return "Darbs nav atrasts", 404
        
        # Noteic darba veidu
        actual_work_type = 'homework' if work_type == 'homework' else 'test'
        
        event_id = f"{actual_work_type}_{work['id']}@classmate-system"
        start_date = work['date']
        
        print(f"🔍 DEBUG: Veidojam kalendāru - subject: {work['subject']}, date: {start_date}")
        
        ical_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Classmate System//Test Calendar//EN
BEGIN:VEVENT
UID:{event_id}
DTSTAMP:{datetime.now().strftime('%Y%m%dT%H%M%SZ')}
DTSTART;VALUE=DATE:{start_date.replace('-', '')}
DTEND;VALUE=DATE:{start_date.replace('-', '')}
SUMMARY:{work['subject']} - {work['type']}
DESCRIPTION:{work.get('description', 'Darbs')}
LOCATION:Skola
STATUS:CONFIRMED
END:VEVENT
END:VCALENDAR"""
        
        filename = f"{work['subject']}_{work['date']}.ics"
        
        print(f"🔍 DEBUG: Kalendāra saturs izveidots, faila nosaukums: {filename}")
        
        # ✅ LABOTS - izveido atbalsi ar pareizo MIME type
        response = make_response(ical_content)
        response.headers['Content-Type'] = 'text/calendar'
        response.headers['Content-Disposition'] = f'attachment; filename={filename}'
        
        print("✅ DEBUG: Kalendārs veiksmīgi izveidots")
        return response
        
    except Exception as e:
        print(f"❌ Calendar error: {e}")
        import traceback
        print(f"❌ Full traceback: {traceback.format_exc()}")
        return "Kļūda ģenerējot kalendāru", 500

@app.route('/calendar/all')
def download_all_calendar():
    """Lejupielādēt visu kalendāru - LABOTS"""
    try:
        print("🔍 DEBUG: Sākam VISU kalendāra ģenerēšanu")
        
        # Izmantojam vienkāršāku pieeju
        tests = load_tests()
        homework_list = load_homework()
        all_work = tests + homework_list
        
        print(f"🔍 DEBUG: Kopā atrasti {len(all_work)} darbi")
        
        upcoming_work = [w for w in all_work if calculate_days_left(w['date']) >= 0]
        
        print(f"🔍 DEBUG: Tuvojošies darbi: {len(upcoming_work)}")
        
        ical_events = []
        ical_events.append("BEGIN:VCALENDAR")
        ical_events.append("VERSION:2.0")
        ical_events.append("PRODID:-//Classmate System//All Tests//EN")
        
        for work in upcoming_work:
            work_type = 'homework' if work in homework_list else 'test'
            event_id = f"{work_type}_{work['id']}@classmate-system"
            start_date = work['date']
            
            ical_events.extend([
                "BEGIN:VEVENT",
                f"UID:{event_id}",
                f"DTSTAMP:{datetime.now().strftime('%Y%m%dT%H%M%SZ')}",
                f"DTSTART;VALUE=DATE:{start_date.replace('-', '')}",
                f"DTEND;VALUE=DATE:{start_date.replace('-', '')}",
                f"SUMMARY:{work['subject']} - {work['type']}",
                f"DESCRIPTION:{work.get('description', 'Darbs')}",
                "LOCATION:Skola",
                "STATUS:CONFIRMED",
                "END:VEVENT"
            ])
        
        ical_events.append("END:VCALENDAR")
        ical_content = "\r\n".join(ical_events)
        
        print(f"🔍 DEBUG: Visu kalendāra saturs izveidots")
        
        # ✅ LABOTS - izveido atbalsi
        response = make_response(ical_content)
        response.headers['Content-Type'] = 'text/calendar'
        response.headers['Content-Disposition'] = 'attachment; filename=all_tests.ics'
        
        print("✅ DEBUG: Visu kalendārs veiksmīgi izveidots")
        return response
        
    except Exception as e:
        print(f"❌ All calendar error: {e}")
        import traceback
        print(f"❌ Full traceback: {traceback.format_exc()}")
        return "Kļūda ģenerējot kalendāru", 500
    
@app.route('/db_test')
def db_test():
    """Universāls datu bāzes tests"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # Noteic datu bāzes tipu
        using_postgresql = 'DATABASE_URL' in os.environ
        
        if using_postgresql:
            # PostgreSQL tests
            c.execute('SELECT version()')
            version_info = c.fetchone()
            db_type = "PostgreSQL"
            db_version = version_info['version']
        else:
            # SQLite tests  
            c.execute('SELECT sqlite_version()')
            version_info = c.fetchone()
            db_type = "SQLite"
            db_version = version_info[0] if isinstance(version_info, tuple) else version_info['sqlite_version()']
        
        # Izveido testa tabulu (universāls)
        create_table_sql = '''
            CREATE TABLE IF NOT EXISTS test_table (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        '''
        c.execute(create_table_sql)
        
        # Ievieto testa datus (universāls)
        insert_sql = 'INSERT INTO test_table (message) VALUES (?)'
        c.execute(insert_sql, (f'Test from {db_type} - ' + datetime.now().strftime('%Y-%m-%d %H:%M:%S'),))
        
        # Izvelk datus
        c.execute('SELECT * FROM test_table ORDER BY created_at DESC LIMIT 5')
        results = c.fetchall()
        
        conn.commit()
        conn.close()
        
        return jsonify({
            "status": "SUCCESS",
            "database_type": db_type,
            "database_version": db_version,
            "using_postgresql": using_postgresql,
            "test_data": [dict(row) for row in results],
            "message": "Datu bāze darbojas pareizi!"
        })
        
    except Exception as e:
        return jsonify({
            "status": "ERROR",
            "error": str(e),
            "using_postgresql": 'DATABASE_URL' in os.environ,
            "solution": "Izmantojiet SQLite sintaksi (?) vai izveidojiet PostgreSQL datubāzi"
        }), 500
# 📤 IMPORTĒŠANA (aizsargāta)
@app.route('/import_ics', methods=['GET', 'POST'])
def import_ics():
    """Importēt no .ics faila - AIZSARGĀTS"""
    if not is_host():
        return redirect('/login')
    
    terms_content = load_terms()
        
    if request.method == 'POST':
        if 'ics_file' not in request.files:
            return render_template('import_ics.html', terms_content=terms_content, error="Nav izvēlēts fails!")
        
        ics_file = request.files['ics_file']
        if ics_file.filename == '':
            return render_template('import_ics.html', terms_content=terms_content, error="Nav izvēlēts fails!")
        
        if ics_file and ics_file.filename.endswith('.ics'):
            ics_content = ics_file.read().decode('utf-8')
            imported_count = parse_ics_file(ics_content)
            return render_template('import_ics.html', terms_content=terms_content, success=f"Importēti {imported_count} darbi!")
        else:
            return render_template('import_ics.html', terms_content=terms_content, error="Nav .ics fails!")
    
    return render_template('import_ics.html', terms_content=terms_content)

@app.route('/import_rtu_exams', methods=['GET', 'POST'])
def import_rtu_exams():
    """Importēt no RTU - AIZSARGĀTS"""
    if not is_host():
        return redirect('/login')
    
    terms_content = load_terms()
    
    if request.method == 'POST':
        scraper = RTUScraper()
        result = scraper.get_student_exams()
        
        if result.get('success'):
            exams = result['exams']
            imported_count = 0
            existing_tests = load_tests()
            
            for exam in exams:
                if not test_exists(existing_tests, exam):
                    save_test(exam['subject'], exam['type'], exam['date'], exam['description'])
                    imported_count += 1
            
            if imported_count > 0:
                return render_template('import_rtu.html',
                                    terms_content=terms_content,
                                    success=f"✅ Importēti {imported_count} eksāmeni no RTU!",
                                    exams=exams)
            else:
                return render_template('import_rtu.html',
                                    terms_content=terms_content,
                                    info="ℹ️ Visi eksāmeni jau ir sistēmā")
        else:
            return render_template('import_rtu.html',
                                terms_content=terms_content,
                                error=f"❌ {result.get('error', 'Nezināma kļūda')}")
    
    return render_template('import_rtu.html', terms_content=terms_content)
# ================= TIMER API ROUTES =================

# Timer datu bāzes inicializācija
def init_timer_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS timer_sessions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id TEXT,
                  seconds INTEGER,
                  date TEXT,
                  created_at TEXT)''')
    conn.commit()
    conn.close()

init_timer_db()

@app.route('/api/timer/stats')
def get_timer_stats():
    """Iegūst taimera statistiku pašreizējam lietotājam"""
    try:
        # Izveido unikālu lietotāja ID (var uzlabot ar reālu auth)
        user_id = request.remote_addr  # Vienkāršs veids - IP adrese
        today = datetime.now().strftime('%Y-%m-%d')
        
        conn = get_db_connection()
        
        # Šodienas laiks
        today_result = conn.execute(
            'SELECT SUM(seconds) as total FROM timer_sessions WHERE user_id = ? AND date = ?',
            (user_id, today)
        ).fetchone()
        today_seconds = today_result['total'] or 0
        
        # Kopējais laiks
        total_result = conn.execute(
            'SELECT SUM(seconds) as total FROM timer_sessions WHERE user_id = ?',
            (user_id,)
        ).fetchone()
        total_seconds = total_result['total'] or 0
        
        conn.close()
        
        return jsonify({
            'success': True,
            'stats': {
                'today_seconds': today_seconds,
                'total_seconds': total_seconds,
                'user_id': user_id[:8]  # Partiāls ID priekš debug
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/timer/save', methods=['POST'])
def save_timer_session():
    """Saglabā taimera sesiju"""
    try:
        data = request.get_json()
        seconds = data.get('seconds', 0)
        user_id = request.remote_addr
        today = datetime.now().strftime('%Y-%m-%d')
        
        conn = get_db_connection()
        
        # Pārbauda vai šodien jau ir sesija
        existing = conn.execute(
            'SELECT id, seconds FROM timer_sessions WHERE user_id = ? AND date = ?',
            (user_id, today)
        ).fetchone()
        
        if existing:
            # Atjaunina esošo
            conn.execute(
                'UPDATE timer_sessions SET seconds = ? WHERE id = ?',
                (seconds, existing['id'])
            )
        else:
            # Jauna sesija
            conn.execute(
                'INSERT INTO timer_sessions (user_id, seconds, date, created_at) VALUES (?, ?, ?, ?)',
                (user_id, seconds, today, datetime.now().strftime('%Y-%m-%d %H:%M'))
            )
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'saved_seconds': seconds})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/check_env')
def check_env():
    """Pārbauda environment variables"""
    database_url_exists = 'DATABASE_URL' in os.environ
    database_url_value = os.environ.get('DATABASE_URL', 'NOT SET')
    
    # Drošībai parādām tikai daļu no DATABASE_URL
    if database_url_exists:
        # Parādām tikai sākumu un beigas (slēpjam sensitīvo info)
        db_url = database_url_value
        masked_url = f"{db_url[:20]}...{db_url[-20:]}" if len(db_url) > 40 else "***"
    else:
        masked_url = "NOT SET"
    
    return f"""
    <html>
    <head><title>Environment Check</title></head>
    <body style="font-family: Arial, sans-serif; padding: 20px;">
        <h1>🔧 Environment Variables Check</h1>
        
        <div style="background: {'#d4edda' if database_url_exists else '#f8d7da'}; 
                    padding: 15px; border-radius: 5px; margin: 10px 0;">
            <h3>DATABASE_URL: {'✅ SET' if database_url_exists else '❌ NOT SET'}</h3>
            <p><strong>Value:</strong> {masked_url}</p>
        </div>
        
        <div style="background: #d1ecf1; padding: 15px; border-radius: 5px;">
            <h3>Other Environment Info:</h3>
            <p><strong>Python Version:</strong> {os.environ.get('PYTHON_VERSION', 'Not set')}</p>
            <p><strong>RENDER:</strong> {'✅ True' if 'RENDER' in os.environ else '❌ False'}</p>
            <p><strong>Current Database:</strong> {'PostgreSQL' if database_url_exists else 'SQLite'}</p>
        </div>
        
        <div style="margin-top: 20px;">
            <h3>📋 Next Steps:</h3>
            <ul>
                {'<li>✅ DATABASE_URL ir iestatīts! Render automātiski redeploy</li>' if database_url_exists else 
                '<li>❌ DATABASE_URL nav iestatīts! Izveidojiet PostgreSQL datubāzi</li>'}
                <li>Pārbaudiet Render Dashboard → Environment tab</li>
                <li>Ja nepieciešams, manuāli restartējiet deploy</li>
            </ul>
        </div>
    </body>
    </html>
    """
# ================= UPDATE LOG ROUTES =================

@app.route('/api/get_user_settings', methods=['GET'])
def api_get_user_settings():
    """Atgriež lietotāja iestatījumus"""
    try:
        device_id = get_user_device_id()
        settings = get_user_settings(device_id)
        
        if settings:
            return jsonify({
                'success': True,
                'settings': settings
            })
        else:
            return jsonify({
                'success': True,
                'settings': {
                    'theme': 'default',
                    'device_id': device_id,
                    'is_new': True
                }
            })
            
    except Exception as e:
        print(f"❌ Kļūda iegūstot iestatījumus: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/delete_user_settings', methods=['POST'])
def api_delete_user_settings():
    """Dzēš lietotāja iestatījumus (reset)"""
    if not is_host():
        return jsonify({'success': False, 'error': 'Nav tiesību'})
    
    try:
        device_id = get_user_device_id()
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if 'DATABASE_URL' in os.environ:
            cursor.execute('DELETE FROM user_settings WHERE device_id = %s', (device_id,))
        else:
            cursor.execute('DELETE FROM user_settings WHERE device_id = ?', (device_id,))
        
        conn.commit()
        conn.close()
        
        # Notīram sesiju
        session.pop('theme', None)
        
        return jsonify({'success': True, 'message': 'Iestatījumi dzēsti'})
        
    except Exception as e:
        print(f"❌ Kļūda dzēšot iestatījumus: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/set_default_theme', methods=['POST'])
def api_set_default_theme():
    """Iestata noklusējuma tēmu visiem lietotājiem (tikai host)"""
    if not is_host():
        return jsonify({'success': False, 'error': 'Nav tiesību'})
    
    try:
        data = request.get_json()
        default_theme = data.get('theme', 'default')
        
        # Saglabājam kā globālu noklusējuma tēmu
        # Varētu saglabāt atsevišķā tabulā vai config failā
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Izveidojam/atjauninām config tabulu
        if 'DATABASE_URL' in os.environ:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS app_config (
                    id SERIAL PRIMARY KEY,
                    config_key TEXT UNIQUE NOT NULL,
                    config_value TEXT,
                    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                INSERT INTO app_config (config_key, config_value) 
                VALUES (%s, %s)
                ON CONFLICT (config_key) 
                DO UPDATE SET config_value = EXCLUDED.config_value
            ''', ('default_theme', default_theme))
        else:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS app_config (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    config_key TEXT UNIQUE NOT NULL,
                    config_value TEXT,
                    updated_date TEXT
                )
            ''')
            
            cursor.execute('''
                INSERT OR REPLACE INTO app_config (config_key, config_value, updated_date)
                VALUES (?, ?, ?)
            ''', ('default_theme', default_theme, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True, 
            'message': f'Noklusējuma tēma iestatīta uz: {default_theme}'
        })
        
    except Exception as e:
        print(f"❌ Kļūda iestatot noklusējuma tēmu: {e}")
        return jsonify({'success': False, 'error': str(e)})

def load_updates():
    """Ielādē visus update ierakstus"""
    conn = get_db_connection()
    try:
        if isinstance(conn, psycopg.Connection):
            # PostgreSQL
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM updates ORDER BY date DESC')
            updates_data = cursor.fetchall()
            
            # Konvertējam tuple uz dict
            updates = []
            for row in updates_data:
                updates.append({
                    'id': row[0],
                    'title': row[1],
                    'content': row[2],
                    'date': row[3],
                    'is_active': row[4],
                    'created_date': row[5],
                    'updated_date': row[6] if len(row) > 6 else None
                })
            return updates
        else:
            # SQLite
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM updates ORDER BY date DESC')
            updates_data = cursor.fetchall()
            return [dict(update) for update in updates_data]
    except Exception as e:
        print(f"❌ Kļūda ielādējot updates: {e}")
        return []
    finally:
        conn.close()

def save_update(title, content, date, is_active):
    conn = get_db_connection()
    try:
        c = conn.cursor()
        if 'DATABASE_URL' in os.environ:
            c.execute('INSERT INTO updates (title, content, date, is_active, created_date) VALUES (%s, %s, %s, %s, %s)',
                     (title, content, date, is_active, datetime.now().strftime('%Y-%m-%d %H:%M')))
        else:
            c.execute('INSERT INTO updates (title, content, date, is_active, created_date) VALUES (?, ?, ?, ?, ?)',
                     (title, content, date, is_active, datetime.now().strftime('%Y-%m-%d %H:%M')))
        conn.commit()
    except Exception as e:
        print(f"Kļūda saglabājot update: {e}")
        conn.rollback()
        raise e
    finally:
        conn.close()

def update_update(update_id, title, content, date, is_active):
    conn = get_db_connection()
    try:
        c = conn.cursor()
        if 'DATABASE_URL' in os.environ:
            c.execute('''UPDATE updates SET title = %s, content = %s, date = %s, is_active = %s, updated_date = %s
                        WHERE id = %s''',
                     (title, content, date, is_active, datetime.now().strftime('%Y-%m-%d %H:%M'), update_id))
        else:
            c.execute('''UPDATE updates SET title = ?, content = ?, date = ?, is_active = ?, updated_date = ?
                        WHERE id = ?''',
                     (title, content, date, is_active, datetime.now().strftime('%Y-%m-%d %H:%M'), update_id))
        conn.commit()
    except Exception as e:
        print(f"Kļūda atjauninot update: {e}")
        conn.rollback()
        raise e
    finally:
        conn.close()

def delete_update(update_id):
    conn = get_db_connection()
    try:
        c = conn.cursor()
        if 'DATABASE_URL' in os.environ:
            c.execute('DELETE FROM updates WHERE id = %s', (update_id,))
        else:
            c.execute('DELETE FROM updates WHERE id = ?', (update_id,))
        conn.commit()
        print(f"✅ Update ar ID {update_id} dzēsts")
    except Exception as e:
        print(f"Kļūda dzēšot update: {e}")
        conn.rollback()
        raise e
    finally:
        conn.close()

@app.route('/updates_log')
def updates_log():
    """Update logs - PUBLISKS (visi var skatīties)"""
    terms_content = load_terms()
    updates_list = load_updates()
    active_updates = [update for update in updates_list if update.get('is_active', True)]
    return render_template('updates_log.html', 
                         terms_content=terms_content,
                         updates=active_updates)

@app.route('/updates', methods=['GET', 'POST'])
def manage_updates():
    """Update log pārvaldība - AIZSARGĀTS (tikai host)"""
    if not is_host():
        return redirect('/login')
    
    terms_content = load_terms()
    
    if request.method == 'POST':
        save_update(
            request.form.get('title'),
            request.form.get('content'),
            request.form.get('date'),
            request.form.get('is_active') == 'on'
        )
        return redirect('/updates')
    
    updates_list = load_updates()
    min_date = datetime.now().strftime('%Y-%m-%d')
    return render_template('updates.html', 
                         terms_content=terms_content,
                         updates=updates_list, 
                         min_date=min_date)

@app.route('/edit_update/<int:update_id>', methods=['GET', 'POST'])
def edit_update(update_id):
    """Rediģēt update ierakstu - AIZSARGĀTS"""
    if not is_host():
        return redirect('/login')
    
    terms_content = load_terms()
    updates_list = load_updates()
    update_item = next((update for update in updates_list if update['id'] == update_id), None)
    
    if not update_item:
        return redirect('/updates')
    
    if request.method == 'POST':
        update_update(
            update_id,
            request.form.get('title'),
            request.form.get('content'),
            request.form.get('date'),
            request.form.get('is_active') == 'on'
        )
        return redirect('/updates')
    
    min_date = datetime.now().strftime('%Y-%m-%d')
    return render_template('edit_update.html', 
                         terms_content=terms_content,
                         update=update_item, 
                         min_date=min_date)

@app.route('/delete_update/<int:update_id>')
def delete_update_route(update_id):
    """Dzēš update ierakstu - AIZSARGĀTS"""
    if not is_host():
        return redirect('/login')
    
    delete_update(update_id)
    return redirect('/updates')

@app.route('/api/next_work')
def api_next_work():
    """Atgriež nākamo darbu ar dienu skaitu - LABOTS"""
    try:
        print("🔍 DEBUG: Sākam /api/next_work apstrādi...")
        
        # Ielādē visus darbus
        tests = load_tests()
        homework_list = load_homework()
        all_work = tests + homework_list
        
        print(f"🔍 DEBUG: Kopā darbi: {len(all_work)}")
        print(f"🔍 DEBUG: Testi: {len(tests)}")
        print(f"🔍 DEBUG: Mājasdarbi: {len(homework_list)}")
        
        if not all_work:
            print("🔍 DEBUG: Nav darbu")
            return jsonify({
                'success': True,
                'next_work': None,
                'message': 'Nav darbu'
            })
        
        # Atrod nākamo darbu (tuvāko pēc datuma)
        upcoming_work = []
        today = datetime.now().date()
        
        for work in all_work:
            try:
                # Pārveido datumu no string uz date objektu
                work_date = datetime.strptime(work['date'], '%Y-%m-%d').date()
                days_left = (work_date - today).days
                
                print(f"🔍 DEBUG: {work.get('subject')} - {work['date']} - days_left: {days_left}")
                
                if days_left >= 0:  # Tikai nākotnes darbi
                    work_copy = work.copy()
                    work_copy['days_left'] = days_left
                    upcoming_work.append(work_copy)
                    
            except Exception as e:
                print(f"❌ DEBUG: Kļūda apstrādājot darbu {work}: {e}")
                continue
        
        print(f"🔍 DEBUG: Tuvojošies darbi: {len(upcoming_work)}")
        
        if not upcoming_work:
            print("🔍 DEBUG: Nav tuvojošos darbu")
            return jsonify({
                'success': True,
                'next_work': None,
                'message': 'Nav tuvojošos darbu'
            })
        
        # Sakārto pēc dienu skaita (visuvairāk tuvākais)
        upcoming_work.sort(key=lambda x: x['days_left'])
        next_work = upcoming_work[0]
        
        print(f"🔍 DEBUG: Nākamais darbs: {next_work}")
        
        return jsonify({
            'success': True,
            'next_work': next_work,
            'total_upcoming': len(upcoming_work)
        })
        
    except Exception as e:
        print(f"❌ DEBUG: Kļūda /api/next_work: {e}")
        import traceback
        print(f"❌ DEBUG: Pilna kļūda: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
        
@app.route('/test_db')
def test_db():
    """Testē datu bāzes savienojumu"""
    try:
        conn = get_db_connection()
        
        # Noteic datu bāzes tipu
        if hasattr(conn, '__class__') and 'psycopg' in str(conn.__class__):
            db_type = "PostgreSQL"
            # Testējam PostgreSQL
            cur = conn.cursor()
            cur.execute("SELECT version();")
            version_result = cur.fetchone()
            version = version_result[0] if version_result else "Unknown"
        else:
            db_type = "SQLite" 
            # Testējam SQLite
            cur = conn.cursor()
            cur.execute("SELECT sqlite_version();")
            version_result = cur.fetchone()
            version = version_result[0] if version_result else "Unknown"
        
        conn.close()
        
        return jsonify({
            "status": "success",
            "database": db_type,
            "version": version,
            "using_postgresql": db_type == "PostgreSQL"
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500
        
@app.route('/test_time')
def test_time():
    """Testē vai time kolonnas strādā"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Testējam tests tabulu
        cursor.execute("INSERT INTO tests (subject, type, date, time, description, added_date) VALUES (%s, %s, %s, %s, %s, %s)",
                     ('Testa priekšmets', 'Tests', '2025-11-22', '14:30', 'Testa apraksts', datetime.now().strftime('%Y-%m-%d %H:%M')))
        
        # Testējam homework tabulu  
        cursor.execute("INSERT INTO homework (subject, title, date, time, description, type, added_date) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                     ('Testa priekšmets', 'Testa mājasdarbs', '2025-11-23', '16:45', 'Testa apraksts', 'Mājasdarbs', datetime.now().strftime('%Y-%m-%d %H:%M')))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            "status": "success",
            "message": "Time kolonnas strādā!",
            "test_data_added": True
        })
        
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500
    
@app.route('/debug_data')
def debug_data():
    """Показывает все данные из базы для отладки"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Получаем все предметы
        cursor.execute('SELECT * FROM subjects')
        subjects = cursor.fetchall()
        
        # Получаем все тесты
        cursor.execute('SELECT * FROM tests')
        tests = cursor.fetchall()
        
        # Получаем все домашние задания
        cursor.execute('SELECT * FROM homework')
        homework = cursor.fetchall()
        
        conn.close()
        
        # Конвертируем в читаемый формат
        def format_data(data):
            if isinstance(data, list) and data and isinstance(data[0], tuple):
                return [dict(zip([desc[0] for desc in cursor.description], row)) for row in data]
            return data
        
        return jsonify({
            "subjects": format_data(subjects),
            "tests": format_data(tests), 
            "homework": format_data(homework),
            "counts": {
                "subjects": len(subjects),
                "tests": len(tests),
                "homework": len(homework)
            }
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/notifications', methods=['GET', 'POST'])
def notifications():
    """Epasta balstīta paziņojumu sistēma"""
    terms_content = load_terms()
    subjects = load_subjects()
    message = None
    error = None
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        
        # Validācija
        if not email or '@' not in email:
            error = "Lūdzu ievadi derīgu e-pasta adresi!"
        elif not is_email_unique(email):
            error = "Šis e-pasts jau ir reģistrēts! Ievadi citu e-pastu."
        else:
            # Saglabājam iestatījumus
            try:
                save_email_subscription(email, request.form)
                message = f"✅ Veiksmīgi reģistrēts! Paziņojumi tiks sūtīti uz: {email}"
            except Exception as e:
                error = f"Kļūda saglabājot iestatījumus: {str(e)}"
    
    return render_template('notifications.html',
                         terms_content=terms_content,
                         subjects=subjects,
                         message=message,
                         error=error)

def save_email_subscription(email, form_data):
    """СОХРАНЯЕТ или ПЕРЕЗАПИСЫВАЕТ настройки email подписки"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        notify_1_day = 'notify_1_day' in form_data
        notify_3_days = 'notify_3_days' in form_data
        
        # ✅ ПЕРЕЗАПИСЫВАЕМ существующие настройки
        cursor.execute('''
            INSERT INTO email_subscriptions (email, notify_1_day, notify_3_days, is_active)
            VALUES (%s, %s, %s, TRUE)
            ON CONFLICT (email) 
            DO UPDATE SET 
                notify_1_day = EXCLUDED.notify_1_day,
                notify_3_days = EXCLUDED.notify_3_days,
                is_active = TRUE,
                created_date = CURRENT_TIMESTAMP
        ''', (email, notify_1_day, notify_3_days))
        
        # ✅ ОБНОВЛЯЕМ подписки на предметы
        subjects = load_subjects()
        for subject in subjects:
            if form_data.get(f'subject_{subject["name"]}'):
                cursor.execute('''
                    INSERT INTO email_subject_subscriptions (email, subject_name, is_active)
                    VALUES (%s, %s, TRUE)
                    ON CONFLICT (email, subject_name) 
                    DO UPDATE SET is_active = TRUE
                ''', (email, subject["name"]))
            else:
                # Отключаем если не выбрано
                cursor.execute('''
                    UPDATE email_subject_subscriptions 
                    SET is_active = FALSE 
                    WHERE email = %s AND subject_name = %s
                ''', (email, subject["name"]))
        
        conn.commit()
        print(f"✅ Настройки email {email} обновлены!")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Ошибка сохранения настроек {email}: {e}")
        raise e
    finally:
        conn.close()


    
@app.route('/unsubscribe/<email>')
def unsubscribe(email):
    """Lai lietotāji varētu atsaukt abonementu"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE email_subscriptions 
        SET is_active = FALSE 
        WHERE email = %s
    ''', (email,))
    
    conn.commit()
    conn.close()
    
    return "✅ Abonements atcelts! Vairs nesaņemsi e-pasta atgādinājumus."


@app.route('/test_email')
def test_email():
    """Ātrs e-pasta tests bez timeout"""
    if not is_host():
        return redirect('/login')
    
    test_email = "test@example.com"
    subject = "Classmate Testa E-pasts"
    html_content = """
    <html>
    <body>
        <h1>✅ Classmate Tests</h1>
        <p>Šis ir testa e-pasts no jūsu sistēmas.</p>
        <p>Ja saņemat šo e-pastu, sistēma strādā!</p>
    </body>
    </html>
    """
    
    try:
        print("🚨 Sāku ātro e-pasta testu...")
        
        # Izmanto asinhrono sūtīšanu
        success = send_email_async(test_email, subject, html_content)
        
        return f"""
        <html>
        <body style="font-family: Arial; padding: 20px;">
            <h2>{"✅ Tests veiksmīgs!" if success else "❌ Tests neveiksmīgs!"}</h2>
            <p>E-pasts {"ievietots sūtīšanas rindā" if success else "nav ievietots rindā"}</p>
            <p><strong>Adrese:</strong> {test_email}</p>
            
            <div style="background: #d1ecf1; padding: 15px; margin: 10px 0; border-radius: 5px;">
                <h4>ℹ️ Sūtīšanas process:</h4>
                <p>1. E-pasts ievietots rindā ✅</p>
                <p>2. Fona process to nosūtīs ātrākajā brīdī</p>
                <p>3. Pārbaudi Render logus rezultātiem</p>
            </div>
            
            <br>
            <a href="/debug_email" style="background: #007bff; color: white; padding: 10px 15px; text-decoration: none; border-radius: 5px;">🔧 Iestatījumi</a>
            <a href="/" style="background: #6c757d; color: white; padding: 10px 15px; text-decoration: none; border-radius: 5px; margin-left: 10px;">← Atpakaļ</a>
        </body>
        </html>
        """
            
    except Exception as e:
        return f"""
        <html>
        <body style="font-family: Arial; padding: 20px;">
            <h2>💥 Kļūda testējot!</h2>
            <p><strong>Kļūda:</strong> {str(e)}</p>
            <br>
            <a href="/">← Atpakaļ uz sākumu</a>
        </body>
        </html>
        """

@app.route('/email_logs')
def view_email_logs():
    """Skatīt nosūtīto e-pastu vēsturi"""
    if not is_host():
        return redirect('/login')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Iegūstam nosūtīto e-pastu vēsturi
    cursor.execute('''
        SELECT * FROM sent_notifications 
        ORDER BY sent_date DESC 
        LIMIT 50
    ''')
    sent_emails = cursor.fetchall()
    
    # Iegūstam e-pastu abonementus
    cursor.execute('''
        SELECT es.email, es.notify_1_day, es.notify_3_days, es.created_date,
               COUNT(ess.subject_name) as subject_count
        FROM email_subscriptions es
        LEFT JOIN email_subject_subscriptions ess ON es.email = ess.email AND ess.is_active = TRUE
        WHERE es.is_active = TRUE
        GROUP BY es.email, es.notify_1_day, es.notify_3_days, es.created_date
        ORDER BY es.created_date DESC
    ''')
    subscribers = cursor.fetchall()
    
    conn.close()
    
    return render_template('email_logs.html',
                         sent_emails=sent_emails,
                         subscribers=subscribers,
                         terms_content=load_terms())


    
@app.route('/debug_email')
def debug_email():
    """Pārbauda e-pasta iestatījumus"""
    if not is_host():
        return redirect('/login')
    
    smtp_username = os.environ.get('SMTP_USERNAME')
    smtp_password = os.environ.get('SMTP_PASSWORD')
    smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = os.environ.get('SMTP_PORT', '587')
    
    return f"""
    <html>
    <body style="font-family: Arial; padding: 20px;">
        <h2>🔧 E-pasta iestatījumu pārbaude</h2>
        
        <div style="background: {'#d4edda' if smtp_username and smtp_password else '#f8d7da'}; padding: 15px; margin: 10px 0; border-radius: 5px;">
            <h3>SMTP Iestatījumi: {'✅ IESTATĪTI' if smtp_username and smtp_password else '❌ NAV IESTATĪTI'}</h3>
            <p><strong>SMTP_USERNAME:</strong> {smtp_username if smtp_username else 'NOT SET'}</p>
            <p><strong>SMTP_PASSWORD:</strong> {'***' + smtp_password[-3:] if smtp_password else 'NOT SET'}</p>
            <p><strong>SMTP_SERVER:</strong> {smtp_server}</p>
            <p><strong>SMTP_PORT:</strong> {smtp_port}</p>
        </div>
        
        <div style="background: #fff3cd; padding: 15px; margin: 10px 0; border-radius: 5px;">
            <h4>ℹ️ Kā iestatīt e-pastu:</h4>
            <ol>
                <li>Ielogojies Render dashboard</li>
                <li>Izvēlies savu app</li>
                <li>Dodies uz "Environment" tab</li>
                <li>Pievieno šos mainīgos:
                    <ul>
                        <li><code>SMTP_USERNAME</code> - tavs Gmail</li>
                        <li><code>SMTP_PASSWORD</code> - Gmail app password</li>
                    </ul>
                </li>
            </ol>
        </div>
        
        <div style="margin-top: 20px;">
            <a href="/test_email" style="background: #007bff; color: white; padding: 10px 15px; text-decoration: none; border-radius: 5px;">📧 Testēt e-pastu</a>
            <a href="/" style="background: #6c757d; color: white; padding: 10px 15px; text-decoration: none; border-radius: 5px; margin-left: 10px;">← Atpakaļ</a>
        </div>
    </body>
    </html>
    """


@app.route('/test_notifications_now')
def test_notifications_now():
    """Принудительно запускает проверку уведомлений"""
    if not is_host():
        return redirect('/login')
    
    try:
        print("🚨 РУЧНОЙ ЗАПУСК ПРОВЕРКИ УВЕДОМЛЕНИЙ")
        check_upcoming_work_simple()
        
        return """
        <html>
        <body style="font-family: Arial; padding: 20px;">
            <h2>✅ Проверка уведомлений запущена!</h2>
            <p>Проверьте логи Render для результатов.</p>
            <a href="/debug_email">🔧 Настройки email</a> | 
            <a href="/">🏠 На главную</a>
        </body>
        </html>
        """
    except Exception as e:
        return f"Ошибка: {str(e)}"

@app.route('/debug_dates')
def debug_dates():
    """Показывает даты для отладки"""
    if not is_host():
        return redirect('/login')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Показываем ближайшие работы
    if 'DATABASE_URL' in os.environ:
        cursor.execute("""
            SELECT 'test' as type, subject, date, date::DATE as parsed_date 
            FROM tests 
            WHERE date::DATE BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '7 days'
            UNION ALL
            SELECT 'homework' as type, subject, date, date::DATE as parsed_date 
            FROM homework 
            WHERE date::DATE BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '7 days'
            ORDER BY parsed_date
        """)
    else:
        cursor.execute("""
            SELECT 'test' as type, subject, date
            FROM tests 
            WHERE date BETWEEN DATE('now') AND DATE('now', '+7 days')
            UNION ALL
            SELECT 'homework' as type, subject, date
            FROM homework 
            WHERE date BETWEEN DATE('now') AND DATE('now', '+7 days')
            ORDER BY date
        """)
    
    upcoming_work = cursor.fetchall()
    conn.close()
    
    result = "<h2>📅 Ближайшие работы (7 дней):</h2>"
    for work in upcoming_work:
        result += f"<p>{work[1]} - {work[2]} ({work[0]})</p>"
    
    result += f"<p>Всего: {len(upcoming_work)} работ</p>"
    result += '<a href="/test_notifications_now">🔔 Тест уведомлений</a>'
    
    return result

def calculate_days_left_with_due_date(date_str, time_str='23:59', due_date_str=None):
    """Aprēķina atlikušās dienas - atbalsta due_date"""
    try:
        # Ja ir due_date, izmanto to
        target_date_str = due_date_str if due_date_str else date_str
        
        if not time_str or time_str == '':
            time_str = '23:59'
        
        datetime_str = f"{target_date_str} {time_str}"
        deadline = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M')
        now = datetime.now()
        
        time_left = deadline - now
        
        if time_left.total_seconds() <= 0:
            return 0
        else:
            return time_left.days
            
    except Exception as e:
        print(f"Kļūda aprēķinot laiku: {e}")
        return 999
# ================= SUBJECT MANAGEMENT ROUTES =================

@app.route('/api/subject/<int:subject_id>/add_category', methods=['POST'])
def add_subject_category(subject_id):
    """Pievienot jaunu kategoriju priekšmetam"""
    if not is_host():
        return jsonify({'success': False, 'error': 'Nav tiesību'})
    
    try:
        data = request.get_json()
        name = data.get('name')
        description = data.get('description', '')
        color = data.get('color', '#3498db')
        
        if not name:
            return jsonify({'success': False, 'error': 'Nosaukums ir obligāts'})
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if 'DATABASE_URL' in os.environ:
            cursor.execute('''
                INSERT INTO subject_categories (subject_id, name, description, color, created_date)
                VALUES (%s, %s, %s, %s, %s)
            ''', (subject_id, name, description, color, datetime.now().strftime('%Y-%m-%d %H:%M')))
        else:
            cursor.execute('''
                INSERT INTO subject_categories (subject_id, name, description, color, created_date)
                VALUES (?, ?, ?, ?, ?)
            ''', (subject_id, name, description, color, datetime.now().strftime('%Y-%m-%d %H:%M')))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Kategorija veiksmīgi pievienota'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/subject/<int:subject_id>/update', methods=['POST'])
def update_subject(subject_id):
    """Atjauno priekšmeta informāciju"""
    if not is_host():
        return jsonify({'success': False, 'error': 'Nav tiesību'})
    
    try:
        data = request.get_json()
        name = data.get('name')
        color = data.get('color')
        description = data.get('description', '')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if 'DATABASE_URL' in os.environ:
            cursor.execute('''
                UPDATE subjects 
                SET name = %s, color = %s, description = %s 
                WHERE id = %s
            ''', (name, color, description, subject_id))
        else:
            cursor.execute('''
                UPDATE subjects 
                SET name = ?, color = ?, description = ? 
                WHERE id = ?
            ''', (name, color, description, subject_id))
        
        conn.commit()
        conn.close()
        
        # Notīram kešu
        load_subjects_cached.cache_clear()
        
        return jsonify({'success': True, 'message': 'Priekšmets atjaunināts'})
        
    except Exception as e:
        print(f"❌ Kļūda atjauninot priekšmetu: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/category/<int:category_id>/delete', methods=['POST'])
def delete_subject_category(category_id):
    """Dzēst kategoriju"""
    if not is_host():
        return jsonify({'success': False, 'error': 'Nav tiesību'})
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Vispirms dzēšam visus failus kategorijā
        if 'DATABASE_URL' in os.environ:
            cursor.execute('DELETE FROM subject_files WHERE category_id = %s', (category_id,))
            cursor.execute('DELETE FROM subject_categories WHERE id = %s', (category_id,))
        else:
            cursor.execute('DELETE FROM subject_files WHERE category_id = ?', (category_id,))
            cursor.execute('DELETE FROM subject_categories WHERE id = ?', (category_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Kategorija veiksmīgi dzēsta'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/subject/<int:subject_id>/update_description', methods=['POST'])
def update_subject_description(subject_id):
    """Atjaunināt priekšmeta aprakstu"""
    if not is_host():
        return jsonify({'success': False, 'error': 'Nav tiesību'})
    
    try:
        data = request.get_json()
        description = data.get('description', '')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if 'DATABASE_URL' in os.environ:
            cursor.execute('UPDATE subjects SET description = %s WHERE id = %s', (description, subject_id))
        else:
            cursor.execute('UPDATE subjects SET description = ? WHERE id = ?', (description, subject_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Apraksts veiksmīgi atjaunināts'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# ================= INITIALIZATION =================
init_tables_if_not_exists()
create_email_based_system()
# Atjauno tabulas ar due_date lauku
update_tables_with_due_date()

# Port konfigurācija Render
port = int(os.environ.get("PORT", 5000))

if __name__ == '__main__':
    print(f"🌐 Startēju serveri uz port: {port}")
    socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)