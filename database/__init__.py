from .database import engine, SessionLocal, Base
from .models import User, GlobalProduct, UserProduct, DailyLog

Base.metadata.create_all(bind=engine)