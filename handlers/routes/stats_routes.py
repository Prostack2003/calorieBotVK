from datetime import datetime, date
from config import user_states
from utils.messenger import send_message
from keyboards.keyboards import get_main_keyboard, get_cancel_keyboard
from handlers.routes.utils import require_profile, send_result, parse_date


def handle_stats_payload(user_id, peer_id, cmd, payload_data):
    """Обработка payload-команд статистики. Возвращает True если обработано."""

    if cmd == 'stats':
        if not require_profile(user_id, peer_id):
            return True
        from handlers.stats import get_daily_stats
        send_result(peer_id, get_daily_stats(user_id))
        return True

    if cmd == 'stats_date':
        if not require_profile(user_id, peer_id):
            return True
        try:
            target_date = datetime.strptime(payload_data['date'], '%Y-%m-%d').date()
            from handlers.stats import get_daily_stats
            send_result(peer_id, get_daily_stats(user_id, target_date))
        except ValueError:
            send_message(peer_id, "❌ Неверный формат даты.", get_main_keyboard())
        return True

    if cmd == 'show_delete':
        if not require_profile(user_id, peer_id):
            return True
        try:
            target_date = datetime.strptime(payload_data['date'], '%Y-%m-%d').date()
            from handlers.stats import get_daily_logs_for_deletion
            send_result(peer_id, get_daily_logs_for_deletion(user_id, target_date))
        except ValueError:
            send_message(peer_id, "❌ Неверный формат даты.", get_main_keyboard())
        return True

    if cmd == 'delete_by_id':
        from handlers.food import delete_log_by_id
        delete_log_by_id(user_id, peer_id, payload_data['log_id'])
        return True

    if cmd == 'export_pdf':
        if not require_profile(user_id, peer_id):
            return True
        try:
            date_start = datetime.strptime(payload_data['date_start'], '%Y-%m-%d').date()
            date_end = datetime.strptime(payload_data['date_end'], '%Y-%m-%d').date()
            from handlers.export import generate_user_report_pdf
            from utils.messenger import send_document

            filepath = generate_user_report_pdf(user_id, date_start, date_end)

            if filepath:
                period_text = date_start.strftime('%d.%m.%Y')
                if date_start != date_end:
                    period_text += f' — {date_end.strftime("%d.%m.%Y")}'
                send_document(peer_id, filepath, f"📄 Отчёт за {period_text}")
                send_message(peer_id, "✅ PDF отправлен!", get_main_keyboard())
            else:
                send_message(peer_id, "❌ Нет данных за этот период.", get_main_keyboard())
        except Exception as e:
            from utils.logger import logger
            logger.error(f"Ошибка экспорта PDF: {e}", exc_info=True)
            send_message(peer_id, "❌ Ошибка создания отчёта.", get_main_keyboard())
        return True

    if cmd == 'export_pdf_period':
        if not require_profile(user_id, peer_id):
            return True
        user_states[user_id] = {'state': 'export_pdf_start'}
        send_message(
            peer_id,
            "📅 Введите начальную дату периода в формате ДД.ММ или ДД.ММ.ГГГГ\n"
            "(например: 01.07 или 01.07.2026)",
            get_cancel_keyboard()
        )
        return True

    if cmd == 'week':
        from handlers.admin import get_weekly_stats
        send_result(peer_id, get_weekly_stats())
        return True

    if cmd == 'admin_day_detail':
        from handlers.admin import get_admin_day_detail
        send_result(peer_id, get_admin_day_detail(payload_data['user_id'], payload_data['date']))
        return True

    return False


def handle_stats_text(user_id, peer_id, text):
    """Обработка текстовых состояний статистики. Возвращает True если обработано."""
    if user_id not in user_states:
        return False

    state = user_states[user_id]['state']

    if state == 'export_pdf_start':
        d = parse_date(text)
        if d is None:
            send_message(peer_id, "❌ Неверный формат. Используйте ДД.ММ или ДД.ММ.ГГГГ", get_cancel_keyboard())
            return True
        if d > date.today():
            send_message(peer_id, "❌ Начальная дата не может быть в будущем.", get_cancel_keyboard())
            return True
        user_states[user_id]['date_start'] = d
        user_states[user_id]['state'] = 'export_pdf_end'
        send_message(
            peer_id,
            f"✅ Начальная дата: {d.strftime('%d.%m.%Y')}\n\n"
            "Теперь введите конечную дату периода (ДД.ММ или ДД.ММ.ГГГГ):",
            get_cancel_keyboard()
        )
        return True

    if state == 'export_pdf_end':
        d = parse_date(text)
        if d is None:
            send_message(peer_id, "❌ Неверный формат. Используйте ДД.ММ или ДД.ММ.ГГГГ", get_cancel_keyboard())
            return True
        if d > date.today():
            send_message(peer_id, "❌ Конечная дата не может быть в будущем.", get_cancel_keyboard())
            return True

        date_start = user_states[user_id]['date_start']
        date_end = d
        if date_start > date_end:
            date_start, date_end = date_end, date_start

        from handlers.export import generate_user_report_pdf
        from utils.messenger import send_document

        filepath = generate_user_report_pdf(user_id, date_start, date_end)
        del user_states[user_id]

        if filepath:
            period_text = f"{date_start.strftime('%d.%m.%Y')} — {date_end.strftime('%d.%m.%Y')}"
            send_document(peer_id, filepath, f"📄 Отчёт за {period_text}")
            send_message(peer_id, "✅ PDF отправлен!", get_main_keyboard())
        else:
            send_message(peer_id, "❌ Нет данных за этот период.", get_main_keyboard())
        return True

    return False