"""
Utils package initialization
"""

from .decorators import (
    host_required,
    login_required,
    anonymous_required,
    rate_limit,
    validate_json,
    log_activity,
    cache_response,
    require_fields,
    register_context_processors
)

from .validators import (
    validate_email,
    validate_date,
    validate_time,
    validate_subject_name,
    validate_color,
    validate_password,
    validate_url,
    validate_homework_data,
    validate_test_data,
    validate_news_data,
    validate_subject_data,
    sanitize_html,
    validate_file_upload
)

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

from .calendar_utils import (
    generate_ics_event,
    generate_calendar_for_tests,
    generate_calendar_for_homework,
    generate_calendar_for_all_work,
    parse_ics_file,
    create_reminder_event,
    generate_weekly_calendar
)

__all__ = [
    # Decorators
    'host_required',
    'login_required',
    'anonymous_required',
    'rate_limit',
    'validate_json',
    'log_activity',
    'cache_response',
    'require_fields',
    'register_context_processors',
    
    # Validators
    'validate_email',
    'validate_date',
    'validate_time',
    'validate_subject_name',
    'validate_color',
    'validate_password',
    'validate_url',
    'validate_homework_data',
    'validate_test_data',
    'validate_news_data',
    'validate_subject_data',
    'sanitize_html',
    'validate_file_upload',
    
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
    
    # Calendar utils
    'generate_ics_event',
    'generate_calendar_for_tests',
    'generate_calendar_for_homework',
    'generate_calendar_for_all_work',
    'parse_ics_file',
    'create_reminder_event',
    'generate_weekly_calendar'
]