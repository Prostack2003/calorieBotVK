from utils.messenger import send_message
from keyboards.keyboards import get_main_keyboard
from handlers.routes.utils import send_result
from handlers.admin import (
    is_admin, get_all_users_stats, get_user_report,
    get_users_list, get_weekly_stats
)


def handle_admin_text(user_id, peer_id, text):
    """Обработка текстовых команд админа. Возвращает True если обработано."""
    if not is_admin(user_id):
        return False

    if text.lower() == '/stats':
        send_result(peer_id, get_all_users_stats())
        return True

    if text.lower() == '/week':
        send_result(peer_id, get_weekly_stats())
        return True

    if text.lower() == '/users':
        send_message(peer_id, get_users_list(), get_main_keyboard())
        return True

    if text.lower().startswith('/report'):
        parts = text.split()
        if len(parts) < 2:
            send_message(peer_id, "Используйте: /report <ID>\nНапример: /report 734594067", get_main_keyboard())
        else:
            try:
                send_message(peer_id, get_user_report(int(parts[1])), get_main_keyboard())
            except ValueError:
                send_message(peer_id, "❌ ID должен быть числом.", get_main_keyboard())
        return True

    if text.lower().startswith('/pdf'):
        return handle_pdf_command(peer_id, text)

    if text.lower() == '/admin':
        send_message(peer_id,
            "🔐 Админ-панель:\n\n"
            "/stats - Статистика за сегодня\n"
            "/week - Отчет за последние 7 дней\n"
            "/users - Список всех пользователей\n"
            "/report <ID> - Детальный отчёт\n"
            "/pdf <ID> [дата] [дата] - Экспорт PDF\n"
            "/admin - Эта справка",
            get_main_keyboard())
        return True

    return False


def handle_pdf_command(peer_id, text):
    """Обработка команды /pdf"""
    from datetime import datetime, date
    from handlers.export import generate_admin_report_pdf
    from utils.messenger import send_document
    from utils.logger import logger

    parts = text.split()
    if len(parts) < 2:
        send_message(peer_id,
            "Используйте:\n"
            "/pdf <ID> — отчёт за сегодня\n"
            "/pdf <ID> 01.07 — отчёт за конкретный день\n"
            "/pdf <ID> 01.07 15.07 — отчёт за период\n\n"
            "Например: /pdf 734594067 01.07 15.07",
            get_main_keyboard())
        return True

    try:
        target_user_id = int(parts[1])

        if len(parts) == 2:
            filepath = generate_admin_report_pdf(target_user_id)
            period_text = date.today().strftime('%d.%m.%Y')
        elif len(parts) == 3:
            d = datetime.strptime(parts[2], '%d.%m').date()
            if d.year == 1900:
                d = d.replace(year=date.today().year)
            filepath = generate_admin_report_pdf(target_user_id, d, d)
            period_text = d.strftime('%d.%m.%Y')
        elif len(parts) >= 4:
            d1 = datetime.strptime(parts[2], '%d.%m').date()
            d2 = datetime.strptime(parts[3], '%d.%m').date()
            if d1.year == 1900:
                d1 = d1.replace(year=date.today().year)
            if d2.year == 1900:
                d2 = d2.replace(year=date.today().year)
            if d1 > d2:
                d1, d2 = d2, d1
            filepath = generate_admin_report_pdf(target_user_id, d1, d2)
            period_text = f"{d1.strftime('%d.%m.%Y')} — {d2.strftime('%d.%m.%Y')}"
        else:
            filepath = None
            period_text = ""

        if filepath:
            send_document(peer_id, filepath, f"📄 Отчёт по пользователю {target_user_id} за {period_text}")
            send_message(peer_id, "✅ PDF отправлен!", get_main_keyboard())
        else:
            send_message(peer_id, "❌ Не удалось создать отчёт или нет данных.", get_main_keyboard())
    except ValueError:
        send_message(peer_id, "❌ Неверный формат. Используйте: /pdf <ID> [ДД.ММ] [ДД.ММ]", get_main_keyboard())
    except Exception as e:
        logger.error(f"Ошибка экспорта PDF админом: {e}", exc_info=True)
        send_message(peer_id, "❌ Ошибка создания отчёта.", get_main_keyboard())
    return True