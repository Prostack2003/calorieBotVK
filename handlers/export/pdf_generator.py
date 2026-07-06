import os
from datetime import datetime, date
from fpdf import FPDF
from database import SessionLocal, User, DailyLog
from utils.logger import logger


class PDFReport(FPDF):
    """Кастомный класс PDF с улучшенным форматированием"""
    
    def __init__(self):
        super().__init__()
        self.add_font('DejaVu', '', 'fonts/DejaVuSans.ttf', uni=True)
        self.add_font('DejaVu', 'B', 'fonts/DejaVuSans-Bold.ttf', uni=True)
        self.set_auto_page_break(auto=True, margin=15)
    
    def header(self):
        # Заголовок с линией
        self.set_font('DejaVu', 'B', 18)
        self.set_text_color(40, 40, 40)
        self.cell(0, 12, 'Calorie Bot', 0, 1, 'C')
        
        self.set_font('DejaVu', '', 11)
        self.set_text_color(100, 100, 100)
        self.cell(0, 6, 'Отчёт по питанию', 0, 1, 'C')
        
        # Разделительная линия
        self.set_draw_color(200, 200, 200)
        self.set_line_width(0.5)
        self.line(10, self.get_y() + 2, 200, self.get_y() + 2)
        self.ln(8)
    
    def footer(self):
        self.set_y(-15)
        self.set_font('DejaVu', '', 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f'Страница {self.page_no()}', 0, 0, 'C')
    
    def section_title(self, title):
        """Заголовок секции с фоном"""
        self.ln(4)
        self.set_fill_color(240, 240, 240)
        self.set_font('DejaVu', 'B', 12)
        self.set_text_color(40, 40, 40)
        self.cell(0, 8, f'  {title}', 0, 1, 'L', fill=True)
        self.ln(3)
    
    def info_row(self, label, value, bold_value=False):
        """Строка информации: метка + значение"""
        self.set_font('DejaVu', '', 10)
        self.set_text_color(80, 80, 80)
        self.cell(50, 6, label, 0, 0)
        
        if bold_value:
            self.set_font('DejaVu', 'B', 10)
            self.set_text_color(40, 40, 40)
        else:
            self.set_font('DejaVu', '', 10)
            self.set_text_color(60, 60, 60)
        
        self.cell(0, 6, str(value), 0, 1)
    
    def table_header(self, columns, widths):
        """Заголовок таблицы"""
        self.set_fill_color(230, 230, 230)
        self.set_font('DejaVu', 'B', 9)
        self.set_text_color(40, 40, 40)
        
        for i, col in enumerate(columns):
            self.cell(widths[i], 7, col, 1, 0, 'C', fill=True)
        self.ln()
    
    def table_row(self, data, widths, fill=False):
        """Строка таблицы"""
        if fill:
            self.set_fill_color(250, 250, 250)
        
        self.set_font('DejaVu', '', 9)
        self.set_text_color(60, 60, 60)
        
        for i, cell in enumerate(data):
            align = 'L' if i == 0 else 'C'
            self.cell(widths[i], 6, str(cell), 1, 0, align, fill=fill)
        self.ln()


def generate_user_report_pdf(user_id, date_start=None, date_end=None):
    """Генерация PDF-отчёта для пользователя"""
    
    if date_start is None:
        date_start = date.today()
    if date_end is None:
        date_end = date_start
    
    session = SessionLocal()
    try:
        user = session.query(User).filter_by(vk_id=user_id).first()
        if not user:
            return None
        
        logs = session.query(DailyLog).filter(
            DailyLog.user_id == user_id,
            DailyLog.date >= date_start,
            DailyLog.date <= date_end
        ).order_by(DailyLog.date, DailyLog.created_at).all()
        
        if not logs:
            return None
        
        # Создаём PDF
        pdf = PDFReport()
        pdf.add_page()
        
        # === Информация о пользователе ===
        pdf.set_font('DejaVu', 'B', 11)
        pdf.set_text_color(40, 40, 40)
        user_name = user.name if user.name else "Без имени"
        pdf.cell(0, 6, f'Пользователь: {user_name}', 0, 1)
        
        pdf.set_font('DejaVu', '', 10)
        pdf.set_text_color(80, 80, 80)
        
        period_text = date_start.strftime("%d.%m.%Y")
        if date_start != date_end:
            period_text += f' — {date_end.strftime("%d.%m.%Y")}'
        
        pdf.cell(0, 6, f'Период: {period_text}', 0, 1)
        pdf.cell(0, 6, f'Сгенерировано: {datetime.now().strftime("%d.%m.%Y %H:%M")}', 0, 1)
        pdf.ln(5)
        
        # === Профиль ===
        pdf.section_title('ПРОФИЛЬ')
        
        goal_text = {'lose': 'Похудение', 'maintain': 'Поддержание', 'gain': 'Набор массы'}.get(user.goal, user.goal)
        gender_text = 'Мужской' if user.gender == 'male' else 'Женский'
        
        pdf.info_row('Пол:', gender_text)
        pdf.info_row('Возраст:', f'{user.age} лет')
        pdf.info_row('Рост:', f'{user.height} см')
        pdf.info_row('Вес:', f'{user.weight} кг')
        pdf.info_row('Цель:', goal_text, bold_value=True)
        pdf.info_row('Норма:', f'{round(user.daily_calories)} ккал/день', bold_value=True)
        
        # === Итоги периода ===
        pdf.section_title('ИТОГИ ПЕРИОДА')
        
        total_c = round(sum(l.calories for l in logs), 1)
        total_p = round(sum(l.proteins for l in logs), 1)
        total_f = round(sum(l.fats for l in logs), 1)
        total_carb = round(sum(l.carbs for l in logs), 1)
        
        num_days = (date_end - date_start).days + 1
        avg_c = round(total_c / num_days, 1)
        avg_p = round(total_p / num_days, 1)
        avg_f = round(total_f / num_days, 1)
        avg_carb = round(total_carb / num_days, 1)
        
        days_active = len(set(l.date for l in logs))
        
        pdf.set_font('DejaVu', 'B', 10)
        pdf.set_text_color(60, 60, 60)
        pdf.cell(0, 6, 'Среднее в день:', 0, 1)
        
        pdf.set_font('DejaVu', '', 10)
        pdf.set_text_color(80, 80, 80)
        pdf.cell(10, 6, '', 0, 0)  # Отступ
        pdf.cell(40, 6, 'Калории:', 0, 0)
        pdf.set_font('DejaVu', 'B', 10)
        pdf.set_text_color(40, 40, 40)
        pdf.cell(0, 6, f'{avg_c} ккал', 0, 1)
        
        pdf.set_font('DejaVu', '', 10)
        pdf.set_text_color(80, 80, 80)
        pdf.cell(10, 6, '', 0, 0)
        pdf.cell(40, 6, 'Белки:', 0, 0)
        pdf.set_font('DejaVu', 'B', 10)
        pdf.set_text_color(40, 40, 40)
        pdf.cell(0, 6, f'{avg_p}г', 0, 1)
        
        pdf.set_font('DejaVu', '', 10)
        pdf.set_text_color(80, 80, 80)
        pdf.cell(10, 6, '', 0, 0)
        pdf.cell(40, 6, 'Жиры:', 0, 0)
        pdf.set_font('DejaVu', 'B', 10)
        pdf.set_text_color(40, 40, 40)
        pdf.cell(0, 6, f'{avg_f}г', 0, 1)
        
        pdf.set_font('DejaVu', '', 10)
        pdf.set_text_color(80, 80, 80)
        pdf.cell(10, 6, '', 0, 0)
        pdf.cell(40, 6, 'Углеводы:', 0, 0)
        pdf.set_font('DejaVu', 'B', 10)
        pdf.set_text_color(40, 40, 40)
        pdf.cell(0, 6, f'{avg_carb}г', 0, 1)
        
        pdf.ln(3)
        pdf.set_font('DejaVu', '', 10)
        pdf.set_text_color(80, 80, 80)
        pdf.cell(10, 6, '', 0, 0)
        pdf.cell(0, 6, f'Всего приёмов пищи: {len(logs)}', 0, 1)
        pdf.cell(10, 6, '', 0, 0)
        pdf.cell(0, 6, f'Дней активности: {days_active} из {num_days}', 0, 1)
        
        # === Детализация по дням ===
        pdf.section_title('ДЕТАЛИЗАЦИЯ ПО ДНЯМ')
        
        days = {}
        for log in logs:
            if log.date not in days:
                days[log.date] = []
            days[log.date].append(log)
        
        for d in sorted(days.keys()):
            day_logs = days[d]
            day_c = round(sum(l.calories for l in day_logs), 1)
            
            # Заголовок дня
            pdf.ln(2)
            pdf.set_font('DejaVu', 'B', 10)
            pdf.set_text_color(40, 40, 40)
            pdf.cell(0, 6, f'{d.strftime("%d.%m.%Y")} — Итого: {day_c} ккал', 0, 1)
            
            # Таблица продуктов
            widths = [90, 30, 40, 30]
            pdf.table_header(['Продукт', 'Вес', 'Калории', 'БЖУ'], widths)
            
            for i, log in enumerate(day_logs):
                kbju = f'{round(log.proteins)}/{round(log.fats)}/{round(log.carbs)}'
                data = [
                    log.product_name[:40],  # Обрезаем длинные названия
                    f'{log.weight}г',
                    f'{round(log.calories, 1)}',
                    kbju
                ]
                pdf.table_row(data, widths, fill=(i % 2 == 0))
            
            pdf.ln(3)
        
        # Сохраняем PDF
        filename = f"report_{user_id}_{date_start.strftime('%Y%m%d')}_{date_end.strftime('%Y%m%d')}.pdf"
        filepath = os.path.join('exports', filename)
        
        if not os.path.exists('exports'):
            os.makedirs('exports')
        
        pdf.output(filepath)
        logger.info(f"✅ PDF отчёт сгенерирован: {filepath}")
        
        return filepath
        
    except Exception as e:
        logger.error(f"❌ Ошибка генерации PDF: {e}", exc_info=True)
        return None
    finally:
        session.close()


def generate_admin_report_pdf(target_user_id, date_start=None, date_end=None):
    """Генерация PDF-отчёта для админа"""
    return generate_user_report_pdf(target_user_id, date_start, date_end)