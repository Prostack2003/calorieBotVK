from datetime import date
from database import SessionLocal, User, DailyLog

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
        msg += f" Ккал: {total_c}\n"
        msg += f"🥩 Белки: {total_p}\n"
        msg += f" Жиры: {total_f}\n"
        msg += f"🍞 Углеводы: {total_carb}\n\n"
        
        if user.daily_calories:
            percent = round((total_c / user.daily_calories) * 100)
            remaining = round(user.daily_calories - total_c)
            msg += f"🎯 Цель: {round(user.daily_calories)} ккал\n"
            msg += f"📈 Выполнено: {percent}%\n"
            msg += f"{'✅' if remaining >= 0 else '⚠️'} Осталось: {abs(remaining)} ккал\n\n"
        
        msg += f"📝 Список продуктов ({len(logs)} шт.):\n"
        for i, log in enumerate(logs, 1):
            msg += f"{i}. {log.product_name} - {log.weight}г\n"
            msg += f"   {round(log.calories, 1)} ккал | Б:{round(log.proteins, 1)} Ж:{round(log.fats, 1)} У:{round(log.carbs, 1)}\n"
        
        return msg
    finally:
        session.close()