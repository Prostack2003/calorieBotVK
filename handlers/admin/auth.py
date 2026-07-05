from config import ADMIN_ID

def is_admin(user_id):
    if not ADMIN_ID:
        return False
    return str(user_id) == str(ADMIN_ID)