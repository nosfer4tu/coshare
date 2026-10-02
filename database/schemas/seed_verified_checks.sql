CREATE TABLE verified_checks (
    id SERIAL PRIMARY KEY,
    route VARCHAR(20) NOT NULL,
    check_date DATE NOT NULL,
    flight_date DATE NOT NULL,
    carrier_checked VARCHAR(100) NOT NULL,
    sandbox_source VARCHAR(20) NOT NULL,
    sandbox_price_jpy INTEGER,
    real_price_jpy INTEGER,
    real_source_url VARCHAR(255) NOT NULL,
    verdict VARCHAR(30) NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);