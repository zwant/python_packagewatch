DROP TABLE IF EXISTS "watched_packages";

CREATE TABLE watched_packages
(
    id INTEGER PRIMARY KEY,
    package_name VARCHAR(255) NOT NULL,
    package_version VARCHAR(10),
    latest_version VARCHAR(10),
    last_updated DATETIME
);