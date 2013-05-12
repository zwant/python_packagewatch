DROP TABLE IF EXISTS "watched_packages";

CREATE TABLE watched_packages
(
    package_name VARCHAR(255) UNIQUE NOT NULL,
    package_url VARCHAR,
    package_version VARCHAR(10) NOT NULL,
    latest_version VARCHAR(10),
    last_updated TIMESTAMP
);