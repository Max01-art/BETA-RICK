"""
Routes package initialization
"""

from .main import main_bp
from .subjects import subjects_bp
from .tests import tests_bp
from .homework import homework_bp
from .news import news_bp
from .auth import auth_bp
from .notifications import notifications_bp
from .api import api_bp
from .import_routes import import_routes_bp

__all__ = [
    'main_bp',
    'subjects_bp',
    'tests_bp',
    'homework_bp',
    'news_bp',
    'auth_bp',
    'notifications_bp',
    'api_bp',
    'import_routes_bp'
]