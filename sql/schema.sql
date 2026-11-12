DROP TABLE IF EXISTS fact_indicator;
DROP TABLE IF EXISTS dim_indicator;
DROP TABLE IF EXISTS dim_date;
DROP TABLE IF EXISTS dim_source;

CREATE TABLE dim_source (
    source_id INT NOT NULL PRIMARY KEY,
    source_name VARCHAR(100) NOT NULL,
    source_url VARCHAR(200)
);

CREATE TABLE dim_indicator (
    indicator_code VARCHAR(20) NOT NULL PRIMARY KEY,
    indicator_name VARCHAR(200) NOT NULL,
    frequency VARCHAR(30),
    source_id INT NOT NULL,
    FOREIGN KEY (source_id) REFERENCES dim_source (source_id)
);

CREATE TABLE dim_date (
    date_key INT NOT NULL PRIMARY KEY,
    full_date DATE NOT NULL,
    year INT NOT NULL,
    quarter INT NOT NULL,
    month INT NOT NULL,
    month_name VARCHAR(20) NOT NULL,
    day_of_week VARCHAR(20) NOT NULL
);

CREATE TABLE fact_indicator (
    date_key INT NOT NULL,
    indicator_code VARCHAR(20) NOT NULL,
    value DECIMAL(12,4) NOT NULL,
    PRIMARY KEY (date_key, indicator_code),
    FOREIGN KEY (date_key) REFERENCES dim_date (date_key),
    FOREIGN KEY (indicator_code) REFERENCES dim_indicator (indicator_code)
);