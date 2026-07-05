import json
from datetime import date, timedelta, datetime
from database import SessionLocal, User, DailyLog

def get_weekly_stats():
    session = SessionLocal()
    try:
        today = date.today()
        week_ago = today - timedelta(days=6)
        
        users = session.query(User).filter_by(onboarded=True).all()
        logs = session.query(DailyLog).filter(
            DailyLog.date >= week_ago,
            DailyLog.date <= today
        ).all()
        
        stats = {}
        for log in logs:
            if log.user_id not in stats:
                stats[log.user_id] = {}
            if log.date not in stats[log.user_id]:
                stats[log.user_id][log.date] = {'c': 0, 'p': 0, 'f': 0, 'u': 0}
            
            stats[log.user_id][log.date]['c'] += log.calories
            stats[log.user_id][log.date]['p'] += log.proteins
            stats[log.user_id][log.date]['f'] += log.fats
            stats[log.user_id][log.date]['u'] += log.carbs
        
        msg = f"📊 Отчет за неделю ({week_ago.strftime('%d.%m')} - {today.strftime('%d.%m')})\n\n"
        
        if not stats:
            msg += "😴 За эту неделю никто ничего не ел."
            return msg, None
        
        keyboard_buttons = []
        
        for uid, daily_stats in stats.items():
            user = session.query(User).filter_by(vk_id=uid).first()
            user_name = user.name if user and user.name else f"ID: {uid}"
            
            msg += f"👤 {user_name}\n"
            
            week_c = 0
            
            for d in sorted(daily_stats.keys()):
                s = daily_stats[d]
                c = round(s['c'], 1)
                week_c += c
                
                day_mark = "✅" if d == today else "📅"
                msg += f"{day_mark} {d.strftime('%d.%m')}: {c} ккал\n"
                
                label = f"{d.strftime('%d.%m')} | {round(c, 0)} ккал ({user_name[:10]})"
                if len(label) > 40:
                    label = label[:37] + "..."
                
                payload = json.dumps({
                    "cmd": "admin_day_detail", 
                    "user_id": uid, 
                    "date": d.strftime('%Y-%m-%d')
                })
                keyboard_buttons.append([{"action": {"type": "text", "label": label, "payload": payload}, "color": "secondary"}])
            
            avg_c = round(week_c / 7, 1)
            msg += f"📈 Итого: {round(week_c, 1)} ккал (среднее: {avg_c}/день)\n"
            msg += "━━━━━━━━━━━━━━━━━━━━━\n"
        
        keyboard_buttons.append([{"action": {"type": "text", "label": "В главное меню", "payload": "{\"cmd\":\"main_menu\"}"}, "color": "primary"}])
        
        keyboard = json.dumps({"one_time": True, "buttons": keyboard_buttons}, ensure_ascii=False)
        
        return msg, keyboard
    finally:
        session.close()

def get_admin_day_detail(target_user_id, date_str):
    session = SessionLocal()
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        user = session.query(User).filter_by(vk_id=target_user_id).first()
        
        if not user:
            return "❌ Пользователь не найден.", None
        
        user_name = user.name if user.name else f"ID: {target_user_id}"
        
        logs = session.query(DailyLog).filter_by(
            user_id=target_user_id, 
            date=target_date
        ).order_by(DailyLog.created_at).all()
        
        msg = f"📋 {user_name} за {target_date.strftime('%d.%m.%Y')}:\n\n"
        
        if not logs:
            msg += "Пусто."
            keyboard = json.dumps({"one_time": True, "buttons": [[{"action": {"type": "text", "label": "◀️ К недельному отчету", "payload": "{\"cmd\":\"week\"}"}, "color": "secondary"}]]}, ensure_ascii=False)
            return msg, keyboard
        
        total_c = round(sum(l.calories for l in logs), 1)
        total_p = round(sum(l.proteins for l in logs), 1)
        total_f = round(sum(l.fats for l in logs), 1)
        total_carb = round(sum(l.carbs for l in logs), 1)
        
        msg += f"🔥 Ккал: {total_c}\n"
        msg += f"🥩 Б: {total_p} | 🥑 Ж: {total_f} | 🍞 У: {total_carb}\n\n"
        msg += f" Список ({len(logs)} шт.):\n"
        
        for i, log in enumerate(logs, 1):
            msg += f"{i}. {log.product_name} - {log.weight}г ({round(log.calories, 1)} ккал)\n"
        
        keyboard = json.dumps({"one_time": True, "buttons": [[{"action": {"type": "text", "label": "◀️ К недельному отчету", "payload": "{\"cmd\":\"week\"}"}, "color": "secondary"}]]}, ensure_ascii=False)
        
        return msg, keyboard
    finally:
        session.close()