CREATE TABLE IF NOT EXISTS marketing_metrics (
    id SERIAL PRIMARY KEY,
    campaign_name VARCHAR(100),
    date DATE,
    impressions INT,
    clicks INT,
    conversions INT,
    spend NUMERIC(10, 2),
    revenue NUMERIC(10, 2)
);