from datetime import date
from database import SessionLocal, User, DailyLog
from keyboards.keyboards import get_main_keyboard, get_delete_keyboard

def get_daily_stats(user_id):
    session = SessionLocal()
    try:
        user = session.query(User).filter_by(vk_id=user_id).first()
        logs = session.query(DailyLog).filter_by(user_id=user_id, date=date.today()).order_by(DailyLog.created_at).all()
        
        if not logs:
            return "Сегодня пока ничего не добавлено. "
        
        total_c = round(sum(l.calories for l in logs), 1)
        total_p = round(sum(l.proteins for l in logs), 1)
        total_f = round(sum(l.fats for l in logs), 1)
        total_carb = round(sum(l.carbs for l in logs), 1)
        
        msg = f" Статистика за сегодня:\n\n"
        msg += f"🔥 Ккал: {total_c} | 🥩 Б: {total_p} | 🥑 Ж: {total_f} | 🍞 У: {total_carb}\n\n"
        
        msg += "📝 Добавлено:\n"
        for i, log in enumerate(logs, 1):
            msg += f"{i}. {log.product_name} - {log.weight}г ({round(log.calories, 1)} ккал)\n"
        
        msg += f"\nВсего приёмов пищи: {len(logs)}"
        
        if user and user.daily_calories:
            remaining = round(user.daily_calories - total_c)
            percent = min(100, round((total_c / user.daily_calories) * 100))
            
            msg += f"\n\n🎯 Цель: {round(user.daily_calories)} ккал"
            msg += f"\n Выполнено: {percent}%"
            msg += f"\n{'✅' if remaining >= 0 else '⚠️'} Осталось: {abs(remaining)} ккал"
            
            if user.daily_proteins:
                p_pct = min(100, round((total_p / user.daily_proteins) * 100))
                f_pct = min(100, round((total_f / user.daily_fats) * 100))
                c_pct = min(100, round((total_carb / user.daily_carbs) * 100))
                msg += f"\n\n🥩 Белки: {p_pct}% ({total_p}/{round(user.daily_proteins, 1)}г)"
                msg += f"\n Жиры: {f_pct}% ({total_f}/{round(user.daily_fats, 1)}г)"
                msg += f"\n🍞 Углеводы: {c_pct}% ({total_carb}/{round(user.daily_carbs, 1)}г)"
        
        keyboard = get_delete_keyboard(logs)
        
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