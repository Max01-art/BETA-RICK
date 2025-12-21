"""
Утилиты для кеширования данных
"""
from datetime import datetime, timedelta


class SimpleCache:
    """Простой кэш с временными метками"""
    
    def __init__(self, duration=30):
        self._cache = {}
        self._timestamps = {}
        self.duration = duration  # seconds
    
    def get(self, key):
        """Получить значение из кэша"""
        if key in self._cache:
            if datetime.now() - self._timestamps[key] < timedelta(seconds=self.duration):
                return self._cache[key]
        return None
    
    def set(self, key, value):
        """Сохранить значение в кэш"""
        self._cache[key] = value
        self._timestamps[key] = datetime.now()
    
    def clear(self, key=None):
        """Очистить кэш"""
        if key:
            self._cache.pop(key, None)
            self._timestamps.pop(key, None)
        else:
            self._cache.clear()
            self._timestamps.clear()
    
    def clear_all(self):
        """Полная очистка кэша"""
        self.clear()


# Глобальный экземпляр кэша
cache = SimpleCache(duration=30)