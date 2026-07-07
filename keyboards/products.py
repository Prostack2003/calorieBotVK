import json


def get_product_selection_keyboard(products):
    """Клавиатура выбора продукта из списка"""
    buttons = []
    for i, product in enumerate(products):
        short_name = product['name'][:30] if len(product['name']) > 30 else product['name']
        label = f"{i+1}. {short_name}"
        
        if len(label) > 40:
            label = label[:37] + "..."
        
        buttons.append([{
            "action": {
                "type": "text", 
                "label": label, 
                "payload": json.dumps({"cmd": "select", "product": product['name']})
            }, 
            "color": "secondary"
        }])
    
    buttons.append([{
        "action": {"type": "text", "label": "Отмена", "payload": "{\"cmd\":\"cancel\"}"}, 
        "color": "negative"
    }])
    
    return json.dumps({"one_time": True, "buttons": buttons}, ensure_ascii=False)