CREATE TABLE codeshare_pairs (
    id SERIAL PRIMARY KEY,
    route VARCHAR(20) NOT NULL,
    departure_time TIMESTAMP NOT NULL,
    operating_airline VARCHAR(100) NOT NULL,
    marketing_airline VARCHAR(100) NOT NULL,
    operating_price_jpy INTEGER NOT NULL,
    marketing_price_jpy INTEGER NOT NULL,
    price_difference_jpy INTEGER NOT NULL,
    detected_at TIMESTAMP DEFAULT NOW()
);