from config import user_states
from utils.messenger import send_message
from keyboards import get_cancel_keyboard
from .log import save_log


def handle_weight(user_id, peer_id, text):
    """Обработка ввода веса продукта"""
    if user_id not in user_states:
        return
    
    try:
        weight = float(text.strip())
        
        if weight <= 0:
            send_message(peer_id, "❌ Вес должен быть больше нуля. Введите число (например: 150)", get_cancel_keyboard())
            return
        
        if weight > 10000:
            send_message(
                peer_id, 
                "❌ Слишком большой вес! Максимум 10000г (10кг).\n"
                "Если вы действительно съели столько, разделите на несколько порций.",
                get_cancel_keyboard()
            )
            return
        
        target_date = user_states[user_id].get('add_date')
        save_log(user_id, peer_id, user_states[user_id]['product'], weight, target_date)
        
    except ValueError:
        send_message(peer_id, "❌ Введите число (например: 150)", get_cancel_keyboard())