from database import SessionLocal, User

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