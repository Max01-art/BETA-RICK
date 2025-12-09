"""
Utils package - вспомогательные функции
"""
from .helpers import (
    calculate_days_left,
    get_work_status,
    get_status_color,
    format_date,
    format_time,
    get_work_by_subject,
    allowed_file,
    sanitize_filename,
    get_file_size_human,
    is_mobile_device,
    generate_device_id,
    paginate_list,
    group_by_date
)

from .decorators import (
    host_required,
    login_required,
    ajax_required,
    cache_response,
    register_context_processors,
    log_request,
    measure_time,
    handle_errors
)

__all__ = [
    # Helpers
    'calculate_days_left',
    'get_work_status',
    'get_status_color',
    'format_date',
    'format_time',
    'get_work_by_subject',
    'allowed_file',
    'sanitize_filename',
    'get_file_size_human',
    'is_mobile_device',
    'generate_device_id',
    'paginate_list',
    'group_by_date',
    
    # Decorators
    'host_required',
    'login_required',
    'ajax_required',
    'cache_response',
    'register_context_processors',
    'log_request',
    'measure_time',
    'handle_errors'
]