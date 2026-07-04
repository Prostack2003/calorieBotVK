from datetime import date
from config import ADMIN_ID
from database import SessionLocal, User, DailyLog

def is_admin(user_id):
    if not ADMIN_ID:
        return False
    return str(user_id) == str(ADMIN_ID)

def get_all_users_stats():
    session = SessionLocal()
    try:
        users = session.query(User).filter_by(onboarded=True).all()
        today_logs = session.query(DailyLog).filter_by(date=date.today()).all()
        
        logs_by_user = {}
        for log in today_logs:
            if log.user_id not in logs_by_user:
                logs_by_user[log.user_id] = []
            logs_by_user[log.user_id].append(log)
        
        msg = f"📊 Общая статистика за {date.today()}\n\n"
        msg += f" Всего пользователей: {len(users)}\n"
        msg += f"🍽 Активных сегодня: {len(logs_by_user)}\n"
        msg += f"📝 Всего записей: {len(today_logs)}\n\n"
        
        if not logs_by_user:
            msg += "Сегодня никто ничего не ел 😴"
            return msg
        
        msg += "━━━━━━━━━━━━━━━━━━━━━\n"
        
        for uid, logs in logs_by_user.items():
            user = session.query(User).filter_by(vk_id=uid).first()
            user_name = user.name if user and user.name else f"ID: {uid}"
            
            total_c = round(sum(l.calories for l in logs), 1)
            total_p = round(sum(l.proteins for l in logs), 1)
            total_f = round(sum(l.fats for l in logs), 1)
            total_carb = round(sum(l.carbs for l in logs), 1)
            
            msg += f"\n👤 {user_name}\n"
            
            if user and user.daily_calories:
                percent = round((total_c / user.daily_calories) * 100)
                msg += f"🔥 {total_c} / {round(user.daily_calories)} ккал ({percent}%)\n"
            else:
                msg += f"🔥 {total_c} ккал (цель не задана)\n"
            
            msg += f"🥩 Б: {total_p} | 🥑 Ж: {total_f} |  У: {total_carb}\n"
            msg += f"🍽 Приёмов пищи: {len(logs)}\n"
            msg += "━━━━━━━━━━━━━━━━━━━━━\n"
        
        return msg
    finally:
        session.close()

def get_user_report(target_user_id):
    session = SessionLocal()
    try:
        user = session.query(User).filter_by(vk_id=target_user_id).first()
        
        if not user:
            return f"❌ Пользователь с ID {target_user_id} не найден в базе."
        
        user_name = user.name if user.name else f"ID: {target_user_id}"
        
        logs = session.query(DailyLog).filter_by(user_id=target_user_id, date=date.today()).order_by(DailyLog.created_at).all()
        
        msg = f"📋 Отчёт: {user_name} (ID: {target_user_id})\n"
        msg += f"📅 Дата: {date.today()}\n\n"
        
        if user.onboarded:
            goal_text = {'lose': 'Похудение', 'maintain': 'Поддержание', 'gain': 'Набор массы'}.get(user.goal, user.goal)
            msg += f"👤 Профиль:\n"
            msg += f"• Пол: {'Мужской' if user.gender == 'male' else 'Женский'}\n"
            msg += f"• Возраст: {user.age}\n"
            msg += f"• Рост/Вес: {user.height}см / {user.weight}кг\n"
            msg += f"• Цель: {goal_text}\n"
            msg += f"• Норма: {round(user.daily_calories)} ккал\n\n"
        
        if not logs:
            msg += "😴 Сегодня ничего не ел"
            return msg
        
        total_c = round(sum(l.calories for l in logs), 1)
        total_p = round(sum(l.proteins for l in logs), 1)
        total_f = round(sum(l.fats for l in logs), 1)
        total_carb = round(sum(l.carbs for l in logs), 1)
        
        msg += f"📊 Итог за день:\n"
        msg += f"🔥 Ккал: {total_c}\n"
        msg += f"🥩 Белки: {total_p}\n"
        msg += f"🥑 Жиры: {total_f}\n"
        msg += f"🍞 Углеводы: {total_carb}\n\n"
        
        if user.daily_calories:
            percent = round((total_c / user.daily_calories) * 100)
            remaining = round(user.daily_calories - total_c)
            msg += f"🎯 Цель: {round(user.daily_calories)} ккал\n"
            msg += f" Выполнено: {percent}%\n"
            msg += f"{'✅' if remaining >= 0 else '⚠️'} Осталось: {abs(remaining)} ккал\n\n"
        
        msg += f"📝 Список продуктов ({len(logs)} шт.):\n"
        for i, log in enumerate(logs, 1):
            msg += f"{i}. {log.product_name} - {log.weight}г\n"
            msg += f"   {round(log.calories, 1)} ккал | Б:{round(log.proteins, 1)} Ж:{round(log.fats, 1)} У:{round(log.carbs, 1)}\n"
        
        return msg
    finally:
        session.close()

def get_users_list():
    session = SessionLocal()
    try:
        users = session.query(User).order_by(User.created_at.desc()).all()
        
        if not users:
            return "😴 В базе нет пользователей."
        
        msg = f"👥 Все пользователи ({len(users)}):\n\n"
        
        for i, user in enumerate(users, 1):
            name = user.name if user.name else "Без имени"
            status = "✅" if user.onboarded else ""
            msg += f"{i}. {name} (ID: {user.vk_id}) {status}\n"
            
            if user.onboarded and user.daily_calories:
                msg += f"   🎯 {round(user.daily_calories)} ккал/день\n"
        
        msg += "\n💡 Для детального отчёта:\n/report <ID>"
        
        return msg
    finally:
        session.close()