CREATE TABLE search_cache (
    id SERIAL PRIMARY KEY,
    route VARCHAR(20) NOT NULL,
    departure_date DATE NOT NULL,
    passengers INTEGER NOT NULL DEFAULT 1,
    result_json JSONB NOT NULL,
    cached_at TIMESTAMP DEFAULT NOW()
);