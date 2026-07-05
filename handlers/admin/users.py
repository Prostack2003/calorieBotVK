from database import SessionLocal, User

def get_users_list():
    session = SessionLocal()
    try:
        users = session.query(User).order_by(User.created_at.desc()).all()
        
        if not users:
            return "😴 В базе нет пользователей."
        
        msg = f"👥 Все пользователи ({len(users)}):\n\n"
        
        for i, user in enumerate(users, 1):
            name = user.name if user.name else "Без имени"
            status = "✅" if user.onboarded else "⏳"
            msg += f"{i}. {name} (ID: {user.vk_id}) {status}\n"
            
            if user.onboarded and user.daily_calories:
                msg += f"   🎯 {round(user.daily_calories)} ккал/день\n"
        
        msg += "\n💡 Для детального отчёта:\n/report <ID>"
        
        return msg
    finally:
        session.close()