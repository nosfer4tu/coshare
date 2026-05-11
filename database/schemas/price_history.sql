CREATE TABLE price_history (
    id SERIAL PRIMARY KEY,
    route VARCHAR(20) NOT NULL,
    departure_date DATE NOT NULL,
    price_jpy INTEGER NOT NULL,
    operating_airline VARCHAR(100),
    marketing_airline VARCHAR(100),
    recorded_at TIMESTAMP DEFAULT NOW()
);