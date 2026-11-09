from fastapi import FastAPI, HTTPException, Depends
import os
import time
from faker import Faker
import random
from sqlalchemy import create_engine, Column, Integer, String, Numeric, Date, func
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import declarative_base, sessionmaker, Session

app = FastAPI()
fake = Faker()

DATABASE_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class MarketingMetrics(Base):
    __tablename__ = "marketing_metrics"
    id = Column(Integer, primary_key=True, index=True)
    campaign_name = Column(String(100))
    date = Column(Date)
    impressions = Column(Integer)
    clicks = Column(Integer)
    conversions = Column(Integer)
    spend = Column(Numeric(10, 2))
    revenue = Column(Numeric(10, 2))

max_retries = 5
for attempt in range(max_retries):
    try:
        Base.metadata.create_all(bind=engine)
        print("Успешное подключение к БД и создание таблиц.")
        break
    except OperationalError as e:
        print(f"База недоступна. Попытка {attempt + 1} из {max_retries}. Ждем 5 секунд...")
        time.sleep(5)
        if attempt == max_retries - 1:
            raise e

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/load_data")
def load_data(db: Session = Depends(get_db)):
    try:
        campaigns = ['Google Search Ads', 'Meta Retargeting', 'LinkedIn B2B', 'Email Promo Q3', 'TikTok Influencers']
        new_records = []
        
        for _ in range(50):
            campaign = random.choice(campaigns)
            impressions = random.randint(10000, 200000)
            clicks = int(impressions * random.uniform(0.01, 0.08))
            conversions = int(clicks * random.uniform(0.01, 0.1))
            spend = round(impressions * random.uniform(0.02, 0.08), 2)
            revenue = round(conversions * random.uniform(30, 150), 2) 
            date = fake.date_between(start_date='-6m', end_date='today')
            
            record = MarketingMetrics(
                campaign_name=campaign,
                date=date,
                impressions=impressions,
                clicks=clicks,
                conversions=conversions,
                spend=spend,
                revenue=revenue
            )
            new_records.append(record)
            
        db.add_all(new_records)
        db.commit()
        return {"status": "success", "message": f"Успешно обработано и загружено {len(new_records)} записей."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    try:
        count = db.query(func.count(MarketingMetrics.id)).scalar()
        return {"total_records": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))