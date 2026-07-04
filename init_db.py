import csv
import os
from database import engine, Base, GlobalProduct
from sqlalchemy.orm import Session

def init_database():
    """Инициализация базы данных и загрузка продуктов из CSV"""
    print("🔄 Создание таблиц в базе данных...")
    Base.metadata.create_all(bind=engine)
    print("✅ Таблицы созданы")
    
    # Загрузка продуктов из CSV
    csv_path = os.path.join(os.path.dirname(__file__), 'data', 'products.csv')
    
    if not os.path.exists(csv_path):
        print(f"❌ Файл {csv_path} не найден")
        return
    
    print(f"📂 Загрузка продуктов из {csv_path}...")
    
    with Session(engine) as session:
        # Проверяем, есть ли уже продукты
        existing_count = session.query(GlobalProduct).count()
        if existing_count > 0:
            print(f"⚠️ В базе уже есть {existing_count} продуктов. Пропускаем загрузку.")
            return
        
        # Загружаем из CSV
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            products = []
            
            for row in reader:
                product = GlobalProduct(
                    name=row['name'],
                    calories=float(row['calories']),
                    proteins=float(row['proteins']),
                    fats=float(row['fats']),
                    carbs=float(row['carbs'])
                )
                products.append(product)
            
            session.add_all(products)
            session.commit()
            
        print(f"✅ Загружено {len(products)} продуктов в базу данных")

if __name__ == "__main__":
    init_database()