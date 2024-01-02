CREATE TABLE IF NOT EXISTS jobs (
    id SERIAL PRIMARY KEY,
    job_url VARCHAR(255) UNIQUE,
    site VARCHAR(100),
    title VARCHAR(255),
    company VARCHAR(255),
    company_url VARCHAR(255),
    location VARCHAR(255),
    job_type VARCHAR(50),
    date_posted DATE,
    date_fetched DATE,
    interval VARCHAR(50),
    min_amount FLOAT,
    max_amount FLOAT,
    currency VARCHAR(50),
    is_remote VARCHAR(50),
    num_urgent_words FLOAT,
    benefits VARCHAR(255),
    emails VARCHAR(255),
    description TEXT,
    city VARCHAR(100)
);
