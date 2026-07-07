import json
from database import SessionLocal, UserProduct, DailyLog
from utils.messenger import send_message
from keyboards import (
    get_main_keyboard,
    get_user_products_keyboard,
    get_confirm_delete_product_keyboard
)


def get_user_products_list(user_id):
    """Получить список продуктов пользователя с клавиатурой"""
    session = SessionLocal()
    try:
        products = session.query(UserProduct).filter_by(user_id=user_id).order_by(UserProduct.name).all()

        if not products:
            msg = "📦 У вас пока нет своих продуктов.\n\nДобавить можно через поиск продукта — если бот не найдёт его в базе, предложит добавить свой."
            keyboard = json.dumps({
                "one_time": True,
                "buttons": [[{
                    "action": {"type": "text", "label": "◀️ Назад к настройкам", "payload": "{\"cmd\":\"settings\"}"},
                    "color": "secondary"
                }]]
            }, ensure_ascii=False)
            return msg, keyboard

        msg = f"📦 Ваши продукты ({len(products)} шт.):\n\n"
        msg += "Нажмите на продукт, чтобы удалить его."

        keyboard = get_user_products_keyboard(products)

        return msg, keyboard
    finally:
        session.close()


def delete_user_product(user_id, peer_id, product_id):
    """Показать подтверждение удаления продукта"""
    session = SessionLocal()
    try:
        product = session.query(UserProduct).filter_by(id=product_id, user_id=user_id).first()

        if not product:
            send_message(peer_id, "❌ Продукт не найден.", get_main_keyboard())
            return

        # Считаем, сколько раз продукт использовался в дневнике
        usage_count = session.query(DailyLog).filter_by(
            user_id=user_id,
            product_name=product.name
        ).count()

        keyboard = get_confirm_delete_product_keyboard(product.id, product.name)

        msg = f"⚠️ Удалить продукт \"{product.name}\"?\n\n"
        msg += f"📊 КБЖУ на 100г:\n"
        msg += f"🔥 {product.calories} ккал | Б:{product.proteins} Ж:{product.fats} У:{product.carbs}\n\n"

        if usage_count > 0:
            msg += f"ℹ️ Этот продукт использовался в дневнике {usage_count} раз(а).\n"
            msg += "Записи в дневнике сохранятся — это ваша история питания.\n\n"
        else:
            msg += "Этот продукт ещё не использовался в дневнике.\n\n"

        msg += "Удалить только из списка продуктов?"

        send_message(peer_id, msg, keyboard)
    finally:
        session.close()


def confirm_delete_user_product(user_id, peer_id, product_id):
    """Подтверждённое удаление продукта"""
    session = SessionLocal()
    try:
        product = session.query(UserProduct).filter_by(id=product_id, user_id=user_id).first()

        if not product:
            send_message(peer_id, "❌ Продукт не найден.", get_main_keyboard())
            return

        product_name = product.name
        session.delete(product)
        session.commit()

        send_message(peer_id, f"✅ Продукт \"{product_name}\" удалён.", get_main_keyboard())
    except Exception as e:
        session.rollback()
        send_message(peer_id, "❌ Ошибка удаления.", get_main_keyboard())
    finally:
        session.close()