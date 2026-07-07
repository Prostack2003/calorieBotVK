from .navigation import get_main_keyboard, get_cancel_keyboard
from .registration import get_gender_keyboard, get_activity_keyboard, get_goal_keyboard
from .products import get_product_selection_keyboard, get_source_selection_keyboard
from .analytics import get_stats_navigation_keyboard, get_delete_keyboard
from .profile import (
    get_settings_keyboard, get_settings_keyboard_v2,
    get_confirm_reset_keyboard, get_user_products_keyboard,
    get_confirm_delete_product_keyboard
)
from .confirmation import get_confirm_kbju_keyboard


__all__ = [
    'get_main_keyboard',
    'get_cancel_keyboard',
    'get_gender_keyboard',
    'get_activity_keyboard',
    'get_goal_keyboard',
    'get_product_selection_keyboard',
    'get_source_selection_keyboard',
    'get_stats_navigation_keyboard',
    'get_delete_keyboard',
    'get_settings_keyboard',
    'get_settings_keyboard_v2',
    'get_confirm_reset_keyboard',
    'get_user_products_keyboard',
    'get_confirm_delete_product_keyboard',
    'get_confirm_kbju_keyboard'
]