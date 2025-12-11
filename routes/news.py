"""
Маршруты для работы с новостями
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from werkzeug.utils import secure_filename
import os
from datetime import datetime

from models.news import News
from utils.decorators import host_required
from utils.validators import validate_news_data
from utils.helpers import allowed_file, sanitize_filename

news_bp = Blueprint('news', __name__)


@news_bp.route('/')
def index():
    """Страница всех новостей"""
    # Получаем параметры пагинации
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # Получаем все активные новости
    all_news = News.get_active()
    
    # Простая пагинация
    total = len(all_news)
    start = (page - 1) * per_page
    end = start + per_page
    news_page = all_news[start:end]
    
    has_next = end < total
    has_prev = page > 1
    
    return render_template(
        'pages/news.html',
        news=news_page,
        page=page,
        per_page=per_page,
        total=total,
        has_next=has_next,
        has_prev=has_prev
    )


@news_bp.route('/<int:news_id>')
def detail(news_id):
    """Детальная страница новости"""
    news_item = News.get_by_id(news_id)
    
    if not news_item:
        flash('❌ Ziņa nav atrasta', 'danger')
        return redirect(url_for('news.index'))
    
    # Получаем похожие новости (последние 3)
    related_news = News.get_active(limit=3)
    related_news = [n for n in related_news if n.id != news_id][:3]
    
    return render_template(
        'pages/news_detail.html',
        news=news_item,
        related_news=related_news
    )


@news_bp.route('/add', methods=['GET', 'POST'])
@host_required
def add():
    """Добавить новость"""
    if request.method == 'POST':
        # Получаем данные из формы
        data = {
            'title': request.form.get('title', '').strip(),
            'content': request.form.get('content', '').strip(),
            'date': request.form.get('date', datetime.now().strftime('%Y-%m-%d')).strip(),
            'image_url': ''
        }
        
        # Обработка изображения
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '' and allowed_file(file.filename, {'png', 'jpg', 'jpeg', 'gif', 'webp'}):
                filename = sanitize_filename(file.filename)
                upload_folder = os.path.join('static', 'uploads', 'news')
                os.makedirs(upload_folder, exist_ok=True)
                
                filepath = os.path.join(upload_folder, filename)
                file.save(filepath)
                
                data['image_url'] = f'/static/uploads/news/{filename}'
        
        # Валидация
        is_valid, errors = validate_news_data(data)
        
        if not is_valid:
            for field, error in errors.items():
                flash(f'❌ {error}', 'danger')
            return redirect(url_for('news.add'))
        
        # Создаем новость
        news_item = News(
            title=data['title'],
            content=data['content'],
            date=data['date'],
            image_url=data['image_url']
        )
        
        if news_item.save():
            flash(f'✅ Ziņa "{news_item.title}" pievienota!', 'success')
            return redirect(url_for('news.index'))
        else:
            flash('❌ Kļūda pievienojot ziņu', 'danger')
    
    # GET запрос - показываем форму
    return render_template(
        'forms/add_news.html',
        today=datetime.now().strftime('%Y-%m-%d')
    )


@news_bp.route('/<int:news_id>/edit', methods=['GET', 'POST'])
@host_required
def edit(news_id):
    """Редактировать новость"""
    news_item = News.get_by_id(news_id)
    
    if not news_item:
        flash('❌ Ziņa nav atrasta', 'danger')
        return redirect(url_for('news.index'))
    
    if request.method == 'POST':
        # Обновляем данные
        data = {
            'title': request.form.get('title', '').strip(),
            'content': request.form.get('content', '').strip(),
            'date': request.form.get('date', '').strip(),
            'image_url': news_item.image_url
        }
        
        # Обработка нового изображения
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '' and allowed_file(file.filename, {'png', 'jpg', 'jpeg', 'gif', 'webp'}):
                # Удаляем старое изображение если оно есть
                if news_item.image_url:
                    old_path = news_item.image_url.lstrip('/')
                    if os.path.exists(old_path):
                        try:
                            os.remove(old_path)
                        except:
                            pass
                
                # Сохраняем новое
                filename = sanitize_filename(file.filename)
                upload_folder = os.path.join('static', 'uploads', 'news')
                os.makedirs(upload_folder, exist_ok=True)
                
                filepath = os.path.join(upload_folder, filename)
                file.save(filepath)
                
                data['image_url'] = f'/static/uploads/news/{filename}'
        
        # Валидация
        is_valid, errors = validate_news_data(data)
        
        if not is_valid:
            for field, error in errors.items():
                flash(f'❌ {error}', 'danger')
            return redirect(url_for('news.edit', news_id=news_id))
        
        # Обновляем объект
        news_item.title = data['title']
        news_item.content = data['content']
        news_item.date = data['date']
        news_item.image_url = data['image_url']
        news_item.updated_date = datetime.now().strftime('%Y-%m-%d %H:%M')
        
        if news_item.save():
            flash(f'✅ Ziņa "{news_item.title}" atjaunināta!', 'success')
            return redirect(url_for('news.detail', news_id=news_id))
        else:
            flash('❌ Kļūda atjauninot ziņu', 'danger')
    
    # GET запрос - показываем форму
    return render_template(
        'forms/edit_news.html',
        news=news_item
    )


@news_bp.route('/<int:news_id>/delete', methods=['POST'])
@host_required
def delete(news_id):
    """Удалить новость"""
    news_item = News.get_by_id(news_id)
    
    if not news_item:
        flash('❌ Ziņa nav atrasta', 'danger')
        return redirect(url_for('news.index'))
    
    title = news_item.title
    
    # Удаляем изображение если есть
    if news_item.image_url:
        image_path = news_item.image_url.lstrip('/')
        if os.path.exists(image_path):
            try:
                os.remove(image_path)
            except Exception as e:
                print(f"❌ Ошибка удаления изображения: {e}")
    
    if news_item.delete():
        flash(f'✅ Ziņa "{title}" dzēsta!', 'success')
    else:
        flash('❌ Kļūda dzēšot ziņu', 'danger')
    
    return redirect(url_for('news.index'))


@news_bp.route('/<int:news_id>/toggle-active', methods=['POST'])
@host_required
def toggle_active(news_id):
    """Включить/выключить новость"""
    news_item = News.get_by_id(news_id)
    
    if not news_item:
        return jsonify({'success': False, 'error': 'Ziņa nav atrasta'}), 404
    
    news_item.is_active = not news_item.is_active
    
    if news_item.save():
        status = 'aktīva' if news_item.is_active else 'neaktīva'
        return jsonify({
            'success': True,
            'is_active': news_item.is_active,
            'message': f'Ziņa tagad ir {status}'
        })
    else:
        return jsonify({'success': False, 'error': 'Kļūda atjauninot ziņu'}), 500


@news_bp.route('/latest')
def latest():
    """Последние новости (API)"""
    limit = request.args.get('limit', 5, type=int)
    
    news_list = News.get_active(limit=limit)
    
    return jsonify({
        'news': [n.to_dict() for n in news_list],
        'count': len(news_list)
    })


@news_bp.route('/search')
def search():
    """Поиск новостей"""
    query = request.args.get('q', '').strip()
    
    if not query:
        return redirect(url_for('news.index'))
    
    results = News.search(query)
    
    return render_template(
        'pages/news_search.html',
        results=results,
        query=query,
        count=len(results)
    )


@news_bp.route('/archive')
def archive():
    """Архив новостей по датам"""
    all_news = News.get_all()
    
    # Группируем по годам и месяцам
    from collections import defaultdict
    archive_data = defaultdict(lambda: defaultdict(list))
    
    for news_item in all_news:
        try:
            date = datetime.strptime(news_item.date, '%Y-%m-%d')
            year = date.year
            month = date.strftime('%m')
            archive_data[year][month].append(news_item)
        except:
            pass
    
    # Сортируем по годам (новые первыми)
    sorted_archive = dict(sorted(archive_data.items(), reverse=True))
    
    return render_template(
        'pages/news_archive.html',
        archive=sorted_archive
    )


@news_bp.route('/feed.rss')
def rss_feed():
    """RSS лента новостей"""
    news_list = News.get_active(limit=20)
    
    from flask import make_response
    
    # Генерируем RSS XML
    rss = '<?xml version="1.0" encoding="UTF-8"?>\n'
    rss += '<rss version="2.0">\n'
    rss += '  <channel>\n'
    rss += '    <title>Classmate - Ziņas</title>\n'
    rss += '    <link>http://example.com/news</link>\n'
    rss += '    <description>Jaunākās ziņas no Classmate</description>\n'
    
    for news_item in news_list:
        rss += '    <item>\n'
        rss += f'      <title>{news_item.title}</title>\n'
        rss += f'      <link>http://example.com/news/{news_item.id}</link>\n'
        rss += f'      <description><![CDATA[{news_item.content[:200]}...]]></description>\n'
        rss += f'      <pubDate>{news_item.date}</pubDate>\n'
        rss += '    </item>\n'
    
    rss += '  </channel>\n'
    rss += '</rss>'
    
    response = make_response(rss)
    response.headers['Content-Type'] = 'application/rss+xml'
    
    return response