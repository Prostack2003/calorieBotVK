from datetime import date
from database import SessionLocal, User, DailyLog

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
        msg += f"👥 Всего пользователей: {len(users)}\n"
        msg += f"🍽 Активных сегодня: {len(logs_by_user)}\n"
        msg += f" Всего записей: {len(today_logs)}\n\n"
        
        if not logs_by_user:
            msg += "Сегодня никто ничего не ел 😴"
            return msg, None
        
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
                msg += f" {total_c} / {round(user.daily_calories)} ккал ({percent}%)\n"
            else:
                msg += f"🔥 {total_c} ккал (цель не задана)\n"
            
            msg += f" Б: {total_p} | 🥑 Ж: {total_f} | 🍞 У: {total_carb}\n"
            msg += f"🍽 Приёмов пищи: {len(logs)}\n"
            msg += "━━━━━━━━━━━━━━━━━━━━━\n"
        
        return msg, None
    finally:
        session.close()