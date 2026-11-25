CREATE TABLE vgsales (
    rank_no INT PRIMARY KEY,
    name TEXT,
    platform VARCHAR(20),
    release_year INT,
    genre VARCHAR(30),
    publisher TEXT,
    na_sales NUMERIC(6,2),
    eu_sales NUMERIC(6,2),
    jp_sales NUMERIC(6,2),
    other_sales NUMERIC(6,2),
    global_sales NUMERIC(6,2)
);

COPY vgsales FROM '/data/vgsales.csv'
WITH (FORMAT csv, HEADER true, NULL 'N/A');