import json
from datetime import date, timedelta
from database import SessionLocal, User, DailyLog


def get_daily_stats(user_id, target_date=None):
    """Статистика за выбранную дату (по умолчанию — сегодня)"""
    if target_date is None:
        target_date = date.today()
    
    session = SessionLocal()
    try:
        user = session.query(User).filter_by(vk_id=user_id).first()
        logs = session.query(DailyLog).filter_by(
            user_id=user_id, 
            date=target_date
        ).order_by(DailyLog.created_at).all()
        
        if not logs:
            msg = f"📅 {target_date.strftime('%d.%m.%Y')}\n\n"
            msg += "━━━━━━━━━━━━━━━━━━━━━\n\n"
            msg += "🍽 Ничего не добавлено в этот день.\n\n"
            msg += "━━━━━━━━━━━━━━━━━━━━━"
            keyboard = get_stats_navigation_keyboard(target_date, has_logs=False)
            return msg, keyboard
        
        total_c = round(sum(l.calories for l in logs), 1)
        total_p = round(sum(l.proteins for l in logs), 1)
        total_f = round(sum(l.fats for l in logs), 1)
        total_carb = round(sum(l.carbs for l in logs), 1)
        
        # Структурированное форматирование
        msg = f"📊 Статистика за {target_date.strftime('%d.%m.%Y')}\n\n"
        msg += "━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        # Блок 1: Итоги дня
        msg += f"🔥 Калории: {total_c} ккал\n"
        msg += f"🥩 Белки: {total_p}г\n"
        msg += f"🥑 Жиры: {total_f}г\n"
        msg += f"🍞 Углеводы: {total_carb}г\n\n"
        
        # Блок 2: Прогресс к цели
        if user and user.daily_calories:
            remaining = round(user.daily_calories - total_c)
            percent = min(100, round((total_c / user.daily_calories) * 100))
            
            msg += "━━━━━━━━━━━━━━━━━━━━━\n\n"
            msg += f"🎯 Цель: {round(user.daily_calories)} ккал\n"
            msg += f"📈 Выполнено: {percent}%\n"
            
            if remaining >= 0:
                msg += f"✅ Осталось: {remaining} ккал\n"
            else:
                msg += f"⚠️ Превышение: {abs(remaining)} ккал\n"
            
            if user.daily_proteins:
                p_pct = min(100, round((total_p / user.daily_proteins) * 100))
                f_pct = min(100, round((total_f / user.daily_fats) * 100))
                c_pct = min(100, round((total_carb / user.daily_carbs) * 100))
                
                msg += f"\n🥩 Белки: {p_pct}% ({total_p}/{round(user.daily_proteins, 1)}г)\n"
                msg += f"🥑 Жиры: {f_pct}% ({total_f}/{round(user.daily_fats, 1)}г)\n"
                msg += f"🍞 Углеводы: {c_pct}% ({total_carb}/{round(user.daily_carbs, 1)}г)\n"
        
            # Блок 3: Список продуктов (стабильная двухстрочная структура)
                msg += "\n━━━━━━━━━━━━━━━━━━━━━\n\n"
                msg += f"📝 Добавлено ({len(logs)} приёмов):\n\n"
                
                for i, log in enumerate(logs, 1):
                    name = log.product_name
                    # Обрезаем длинные названия до 35 символов
                    if len(name) > 35:
                        name = name[:32] + "..."
                    
                    # Строка 1: номер и название
                    msg += f"{i}. {name}\n"
                    # Строка 2: вес и калории с отступом
                    msg += f"   ⚖️ {log.weight}г • 🔥 {round(log.calories, 1)} ккал\n"
                
                msg += "\n━━━━━━━━━━━━━━━━━━━━━"
        
        keyboard = get_stats_navigation_keyboard(target_date, has_logs=True)
        
        return msg, keyboard
    finally:
        session.close()


def get_daily_logs_for_deletion(user_id, target_date):
    """Показать нумерованный список записей для удаления"""
    session = SessionLocal()
    try:
        logs = session.query(DailyLog).filter_by(
            user_id=user_id,
            date=target_date
        ).order_by(DailyLog.created_at).all()

        if not logs:
            return "🍽 Нет записей для удаления за этот день.", None

        # Формируем нумерованный список
        msg = f" Записи за {target_date.strftime('%d.%m.%Y')}:\n\n"
        
        for i, log in enumerate(logs, 1):
            # Обрезаем длинные названия
            name = log.product_name
            if len(name) > 30:
                name = name[:27] + "..."
            
            msg += f"{i}. {name} — {log.weight}г ({round(log.calories, 1)} ккал)\n"
        
        msg += f"\n✏️ Напишите номер записи для удаления (1-{len(logs)})"
        msg += "\nили «назад» для отмены."

        # Возвращаем без клавиатуры — пользователь будет вводить номер
        return msg, None
    finally:
        session.close()

def get_delete_keyboard(logs):
    """Клавиатура удаления записей из дневника"""
    buttons = []
    for log in logs:
        short_name = log.product_name[:30] if len(log.product_name) > 30 else log.product_name
        label = f"{short_name} ({log.weight}г)"
        if len(label) > 40:
            label = label[:37] + "..."
        
        buttons.append([{
            "action": {
                "type": "text", 
                "label": label, 
                "payload": json.dumps({"cmd": "delete_by_id", "log_id": log.id})
            }, 
            "color": "negative"
        }])
    
    buttons.append([{
        "action": {"type": "text", "label": "◀️ Назад", "payload": "{\"cmd\":\"stats\"}"}, 
        "color": "secondary"
    }])
    
    return json.dumps({"one_time": True, "buttons": buttons}, ensure_ascii=False)


def get_stats_navigation_keyboard(current_date, has_logs=True):
    """Клавиатура навигации по датам в статистике"""
    yesterday = current_date - timedelta(days=1)
    tomorrow = current_date + timedelta(days=1)
    today = date.today()
    
    buttons = []
    
    # Ряд 1: Навигация по датам
    nav_row = [
        {
            "action": {
                "type": "text", 
                "label": "⬅️ Вчера", 
                "payload": json.dumps({"cmd": "stats_date", "date": yesterday.strftime('%Y-%m-%d')})
            }, 
            "color": "secondary"
        },
        {
            "action": {
                "type": "text", 
                "label": "📅 Сегодня" if current_date != today else "✅ Сегодня", 
                "payload": json.dumps({"cmd": "stats_date", "date": today.strftime('%Y-%m-%d')})
            }, 
            "color": "primary" if current_date == today else "secondary"
        },
        {
            "action": {
                "type": "text", 
                "label": "Завтра ➡️", 
                "payload": json.dumps({"cmd": "stats_date", "date": tomorrow.strftime('%Y-%m-%d')})
            }, 
            "color": "secondary"
        }
    ]
    buttons.append(nav_row)
    
    # Ряд 2: Удаление записи (если есть логи и дата не в будущем)
    if has_logs and current_date <= today:
        buttons.append([{
            "action": {
                "type": "text", 
                "label": "🗑 Удалить запись", 
                "payload": json.dumps({"cmd": "show_delete", "date": current_date.strftime('%Y-%m-%d')})
            }, 
            "color": "negative"
        }])
    
    # Ряд 3: Экспорт PDF (если есть логи)
    if has_logs:
        export_row = [
            {
                "action": {
                    "type": "text", 
                    "label": "📥 PDF за день", 
                    "payload": json.dumps({
                        "cmd": "export_pdf", 
                        "date_start": current_date.strftime('%Y-%m-%d'), 
                        "date_end": current_date.strftime('%Y-%m-%d')
                    })
                }, 
                "color": "primary"
            },
            {
                "action": {
                    "type": "text", 
                    "label": "📥 PDF за период", 
                    "payload": "{\"cmd\":\"export_pdf_period\"}"
                }, 
                "color": "primary"
            }
        ]
        buttons.append(export_row)
    
    # Ряд 4: Отмена
    buttons.append([{
        "action": {
            "type": "text", 
            "label": "❌ Отмена", 
            "payload": "{\"cmd\":\"cancel\"}"
        }, 
        "color": "negative"
    }])
    
    return json.dumps({"one_time": True, "buttons": buttons}, ensure_ascii=False)

def delete_log_by_number(user_id, peer_id, number_str, target_date):
    """Удалить запись по номеру из списка"""
    try:
        number = int(number_str)
    except ValueError:
        from utils.messenger import send_message
        from keyboards import get_main_keyboard
        send_message(peer_id, "❌ Напишите число (номер записи) или «назад».", get_main_keyboard())
        return False

    session = SessionLocal()
    try:
        logs = session.query(DailyLog).filter_by(
            user_id=user_id,
            date=target_date
        ).order_by(DailyLog.created_at).all()

        if not logs:
            from utils.messenger import send_message
            from keyboards import get_main_keyboard
            send_message(peer_id, "🍽 Записей больше нет.", get_main_keyboard())
            return False

        if number < 1 or number > len(logs):
            from utils.messenger import send_message
            from keyboards import get_main_keyboard
            send_message(
                peer_id,
                f" Номер должен быть от 1 до {len(logs)}.\n\n"
                "Или напишите «назад» для отмены.",
                get_main_keyboard()
            )
            return False

        # Удаляем запись
        log_to_delete = logs[number - 1]
        session.delete(log_to_delete)
        session.commit()

        from utils.logger import logger
        logger.info(f"🗑️ Удалена запись #{number}: {log_to_delete.product_name} ({log_to_delete.weight}г)")

        return True

    except Exception as e:
        session.rollback()
        from utils.logger import logger
        logger.error(f"❌ Ошибка удаления записи: {e}", exc_info=True)
        from utils.messenger import send_message
        from keyboards import get_main_keyboard
        send_message(peer_id, "❌ Ошибка удаления.", get_main_keyboard())
        return False
    finally:
        session.close()