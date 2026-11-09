import pandas as pd
from sqlalchemy import create_engine
import os

DB_USER = os.getenv('DB_USER', 'market_admin')
DB_PASS = os.getenv('DB_PASS', 'supersecret_db_pass_2026')
DB_HOST = os.getenv('DB_HOST', 'postgres')
DB_NAME = os.getenv('DB_NAME', 'marketing_db')

engine = create_engine(f'postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:5432/{DB_NAME}')

def process_marketing_etl():
    print("1. Извлечение сырых данных из хранилища...")
    try:
        df = pd.read_sql('SELECT * FROM marketing_metrics', engine)
    except Exception as e:
        print(f"Ошибка чтения данных. Возможно, база пуста: {e}")
        return

    if df.empty:
        print("Данных пока нет. Сначала загрузите их через панель управления.")
        return

    print("2. Рассчет ключевых бизнес-метрик (CPA, ROAS, Profit)...")
    df['roas'] = (df['revenue'] / df['spend']).replace([float('inf'), -float('inf')], 0).fillna(0)
    
    df['cpa'] = (df['spend'] / df['conversions']).replace([float('inf'), -float('inf')], 0).fillna(0)
    
    df['net_profit'] = df['revenue'] - df['spend']
    
    df['is_profitable'] = df['net_profit'] > 0

    print("3. Агрегация данных по рекламным кампаниям...")
    datamart = df.groupby('campaign_name').agg({
        'spend': 'sum',
        'revenue': 'sum',
        'conversions': 'sum',
        'roas': 'mean',
        'cpa': 'mean',
        'net_profit': 'sum'
    }).reset_index()

    datamart = datamart.round(2)

    print("4. Сохранение витрины данных (campaign_roi_mart) в PostgreSQL...")
    datamart.to_sql('campaign_roi_mart', engine, if_exists='replace', index=False)
    
    print("\n✅ ETL-процесс успешно завершен!")
    print("\nТоп-3 кампании по чистой прибыли:")
    print(datamart.sort_values('net_profit', ascending=False).head(3)[['campaign_name', 'net_profit', 'roas']])

if __name__ == "__main__":
    process_marketing_etl()