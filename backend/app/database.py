import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

# Canlıda Railway internal URL'i kullanıyoruz. Lokalde çalışırken .env dosyasındaki URL'i alır.
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://postgres:uGJmsdkHDSnShZPMopuJzDHwauqGfRMH@postgres.railway.internal:5432/railway"
)

# SQLAlchemy standartları gereği bağlantı ön ekini düzenliyoruz
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Her API isteğinde veritabanı bağlantısı açıp kapatacak güvenli fonksiyon
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()