import json
from datetime import date, timedelta


def get_stats_navigation_keyboard(current_date, has_logs=True):
    """Клавиатура навигации по датам в статистике"""
    yesterday = current_date - timedelta(days=1)
    tomorrow = current_date + timedelta(days=1)
    today = date.today()

    buttons = []

    nav_row = [
        {
            "action": {
                "type": "text",
                "label": "⬅️ Вчера",
                "payload": json.dumps({"cmd": "stats_date", "date": yesterday.strftime('%Y-%m-%d')})
            },
            "color": "secondary"
        },
        {
            "action": {
                "type": "text",
                "label": "📅 Сегодня" if current_date != today else "✅ Сегодня",
                "payload": json.dumps({"cmd": "stats_date", "date": today.strftime('%Y-%m-%d')})
            },
            "color": "primary" if current_date == today else "secondary"
        },
        {
            "action": {
                "type": "text",
                "label": "Завтра ➡️",
                "payload": json.dumps({"cmd": "stats_date", "date": tomorrow.strftime('%Y-%m-%d')})
            },
            "color": "secondary"
        }
    ]
    buttons.append(nav_row)

    if has_logs and current_date <= today:
        buttons.append([{
            "action": {
                "type": "text",
                "label": "🗑 Удалить запись",
                "payload": json.dumps({"cmd": "show_delete", "date": current_date.strftime('%Y-%m-%d')})
            },
            "color": "negative"
        }])

    if has_logs:
        export_row = [
            {
                "action": {
                    "type": "text",
                    "label": "📥 PDF за день",
                    "payload": json.dumps({
                        "cmd": "export_pdf",
                        "date_start": current_date.strftime('%Y-%m-%d'),
                        "date_end": current_date.strftime('%Y-%m-%d')
                    })
                },
                "color": "primary"
            },
            {
                "action": {
                    "type": "text",
                    "label": "📥 PDF за период",
                    "payload": "{\"cmd\":\"export_pdf_period\"}"
                },
                "color": "primary"
            }
        ]
        buttons.append(export_row)

    buttons.append([{
        "action": {
            "type": "text",
            "label": "❌ Отмена",
            "payload": "{\"cmd\":\"cancel\"}"
        },
        "color": "negative"
    }])

    return json.dumps({"one_time": True, "buttons": buttons}, ensure_ascii=False)


def get_delete_keyboard(logs):
    """Клавиатура удаления записей из дневника"""
    buttons = []
    for log in logs:
        short_name = log.product_name[:30] if len(log.product_name) > 30 else log.product_name
        label = f"{short_name} ({log.weight}г)"
        if len(label) > 40:
            label = label[:37] + "..."
        
        buttons.append([{
            "action": {
                "type": "text",
                "label": label,
                "payload": json.dumps({"cmd": "delete_by_id", "log_id": log.id})
            },
            "color": "negative"
        }])
    
    buttons.append([{
        "action": {"type": "text", "label": "◀️ Назад", "payload": "{\"cmd\":\"stats\"}"},
        "color": "secondary"
    }])
    
    return json.dumps({"one_time": True, "buttons": buttons}, ensure_ascii=False)