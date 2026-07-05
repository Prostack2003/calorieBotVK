import json
from datetime import date, timedelta
from database import SessionLocal, User, DailyLog

def get_stats_navigation_keyboard(current_date, has_logs=True):
    """Клавиатура навигации по датам"""
    yesterday = current_date - timedelta(days=1)
    tomorrow = current_date + timedelta(days=1)
    today = date.today()
    
    buttons = []
    
    # Кнопки навигации
    nav_row = [
        {"action": {"type": "text", "label": "◀️ Вчера", "payload": json.dumps({"cmd": "stats_date", "date": yesterday.strftime('%Y-%m-%d')})}, "color": "secondary"},
        {"action": {"type": "text", "label": "📅 Сегодня" if current_date != today else "✅ Сегодня", "payload": json.dumps({"cmd": "stats_date", "date": today.strftime('%Y-%m-%d')})}, "color": "primary" if current_date == today else "secondary"},
        {"action": {"type": "text", "label": "Завтра ▶️", "payload": json.dumps({"cmd": "stats_date", "date": tomorrow.strftime('%Y-%m-%d')})}, "color": "secondary"}
    ]
    buttons.append(nav_row)
    
    # Кнопка удаления (только если есть записи и это не будущее)
    if has_logs and current_date <= today:
        buttons.append([{"action": {"type": "text", "label": "🗑 Удалить запись", "payload": json.dumps({"cmd": "show_delete", "date": current_date.strftime('%Y-%m-%d')})}, "color": "negative"}])
    
    buttons.append([{"action": {"type": "text", "label": "В главное меню", "payload": "{\"cmd\":\"main_menu\"}"}, "color": "secondary"}])
    
    return json.dumps({"one_time": True, "buttons": buttons}, ensure_ascii=False)

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
            msg = f"📅 {target_date.strftime('%d.%m.%Y')}\n\nНичего не добавлено в этот день. 🍽"
            keyboard = get_stats_navigation_keyboard(target_date, has_logs=False)
            return msg, keyboard
        
        total_c = round(sum(l.calories for l in logs), 1)
        total_p = round(sum(l.proteins for l in logs), 1)
        total_f = round(sum(l.fats for l in logs), 1)
        total_carb = round(sum(l.carbs for l in logs), 1)
        
        msg = f"📊 Статистика за {target_date.strftime('%d.%m.%Y')}:\n\n"
        msg += f"🔥 Ккал: {total_c} | 🥩 Б: {total_p} | 🥑 Ж: {total_f} | 🍞 У: {total_carb}\n\n"
        
        msg += " Добавлено:\n"
        for i, log in enumerate(logs, 1):
            msg += f"{i}. {log.product_name} - {log.weight}г ({round(log.calories, 1)} ккал)\n"
        
        msg += f"\nВсего приёмов пищи: {len(logs)}"
        
        if user and user.daily_calories:
            remaining = round(user.daily_calories - total_c)
            percent = min(100, round((total_c / user.daily_calories) * 100))
            
            msg += f"\n\n🎯 Цель: {round(user.daily_calories)} ккал"
            msg += f"\n📈 Выполнено: {percent}%"
            msg += f"\n{'✅' if remaining >= 0 else '⚠️'} Осталось: {abs(remaining)} ккал"
            
            if user.daily_proteins:
                p_pct = min(100, round((total_p / user.daily_proteins) * 100))
                f_pct = min(100, round((total_f / user.daily_fats) * 100))
                c_pct = min(100, round((total_carb / user.daily_carbs) * 100))
                msg += f"\n\n🥩 Белки: {p_pct}% ({total_p}/{round(user.daily_proteins, 1)}г)"
                msg += f"\n🥑 Жиры: {f_pct}% ({total_f}/{round(user.daily_fats, 1)}г)"
                msg += f"\n🍞 Углеводы: {c_pct}% ({total_carb}/{round(user.daily_carbs, 1)}г)"
        
        keyboard = get_stats_navigation_keyboard(target_date, has_logs=True)
        
        return msg, keyboard
    finally:
        session.close()

def get_or_create_user(user_id):
    session = SessionLocal()
    try:
        user = session.query(User).filter_by(vk_id=user_id).first()
        if not user:
            user = User(vk_id=user_id)
            session.add(user)
            session.commit()
        
        return {
            'vk_id': user.vk_id,
            'name': user.name,
            'gender': user.gender,
            'age': user.age,
            'height': user.height,
            'weight': user.weight,
            'activity': user.activity,
            'goal': user.goal,
            'daily_calories': user.daily_calories,
            'daily_proteins': user.daily_proteins,
            'daily_fats': user.daily_fats,
            'daily_carbs': user.daily_carbs,
            'onboarded': user.onboarded
        }
    finally:
        session.close()

def get_daily_logs_for_deletion(user_id, target_date):
    """Получить записи за дату для удаления"""
    session = SessionLocal()
    try:
        logs = session.query(DailyLog).filter_by(
            user_id=user_id, 
            date=target_date
        ).order_by(DailyLog.created_at).all()
        
        if not logs:
            msg = f" {target_date.strftime('%d.%m.%Y')}\n\nНет записей для удаления."
            keyboard = get_stats_navigation_keyboard(target_date, has_logs=False)
            return msg, keyboard
        
        msg = f"📅 {target_date.strftime('%d.%m.%Y')}\n\nВыберите запись для удаления:\n\n"
        for i, log in enumerate(logs, 1):
            msg += f"{i}. {log.product_name} - {log.weight}г ({round(log.calories, 1)} ккал)\n"
        
        # Создаём клавиатуру с кнопками удаления
        buttons = []
        for log in logs:
            short_name = log.product_name[:30] if len(log.product_name) > 30 else log.product_name
            label = f"{short_name} ({log.weight}г)"
            if len(label) > 40:
                label = label[:37] + "..."
            buttons.append([{"action": {"type": "text", "label": label, "payload": json.dumps({"cmd": "delete_by_id", "log_id": log.id})}, "color": "negative"}])
        
        buttons.append([{"action": {"type": "text", "label": "◀️ Назад к статистике", "payload": json.dumps({"cmd": "stats_date", "date": target_date.strftime('%Y-%m-%d')})}, "color": "secondary"}])
        
        keyboard = json.dumps({"one_time": True, "buttons": buttons}, ensure_ascii=False)
        
        return msg, keyboard
    finally:
        session.close()