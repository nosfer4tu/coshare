CREATE TABLE destination_cache (
    id SERIAL PRIMARY KEY,
    destination_code VARCHAR(10) NOT NULL,
    activities_json JSONB NOT NULL,
    cached_at TIMESTAMP DEFAULT NOW()
);